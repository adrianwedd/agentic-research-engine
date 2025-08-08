"""
Production Reliability Patterns Module
Provides circuit breakers, retry mechanisms, and graceful shutdown patterns
"""

import asyncio
import logging
import signal
import time
from contextlib import asynccontextmanager
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union

import httpx
from tenacity import RetryError, retry, stop_after_attempt, wait_exponential


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker implementation for service resilience."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        expected_exception: type = Exception,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN - service unavailable")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        return (
            self.last_failure_time is not None
            and time.time() - self.last_failure_time >= self.recovery_timeout
        )

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN


class ResilientHTTPClient:
    """HTTP client with circuit breaker and retry patterns."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)
        self._client = httpx.AsyncClient(timeout=timeout)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _make_request(
        self, method: str, path: str, **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retry logic."""
        url = f"{self.base_url}{path}"
        return await self._client.request(method, url, **kwargs)

    async def get(self, path: str, **kwargs) -> httpx.Response:
        """GET request with circuit breaker protection."""
        return self.circuit_breaker.call(self._make_request, "GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        """POST request with circuit breaker protection."""
        return self.circuit_breaker.call(self._make_request, "POST", path, **kwargs)

    async def put(self, path: str, **kwargs) -> httpx.Response:
        """PUT request with circuit breaker protection."""
        return self.circuit_breaker.call(self._make_request, "PUT", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        """DELETE request with circuit breaker protection."""
        return self.circuit_breaker.call(self._make_request, "DELETE", path, **kwargs)

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()


class GracefulShutdown:
    """Graceful shutdown handler for production services."""

    def __init__(self, shutdown_timeout: int = 30):
        self.shutdown_timeout = shutdown_timeout
        self.shutdown_event = asyncio.Event()
        self.cleanup_tasks: list[Callable] = []
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logging.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(self._shutdown())

    async def _shutdown(self):
        """Execute graceful shutdown sequence."""
        logging.info("Starting graceful shutdown...")
        
        # Run cleanup tasks
        for cleanup_task in reversed(self.cleanup_tasks):
            try:
                if asyncio.iscoroutinefunction(cleanup_task):
                    await cleanup_task()
                else:
                    cleanup_task()
                logging.info(f"Completed cleanup task: {cleanup_task.__name__}")
            except Exception as e:
                logging.error(f"Error in cleanup task {cleanup_task.__name__}: {e}")

        self.shutdown_event.set()
        logging.info("Graceful shutdown completed")

    def register_cleanup(self, cleanup_func: Callable):
        """Register a cleanup function to run during shutdown."""
        self.cleanup_tasks.append(cleanup_func)

    async def wait_for_shutdown(self):
        """Wait for shutdown signal."""
        await self.shutdown_event.wait()


@asynccontextmanager
async def resilient_operation(
    operation_name: str, 
    timeout: Optional[float] = None,
    on_error: Optional[Callable] = None
):
    """Context manager for resilient operations with timeout and error handling."""
    start_time = time.time()
    try:
        if timeout:
            async with asyncio.timeout(timeout):
                yield
        else:
            yield
        
        execution_time = time.time() - start_time
        logging.info(f"Operation '{operation_name}' completed successfully in {execution_time:.2f}s")
        
    except asyncio.TimeoutError:
        logging.error(f"Operation '{operation_name}' timed out after {timeout}s")
        if on_error:
            await on_error("timeout")
        raise
    except Exception as e:
        execution_time = time.time() - start_time
        logging.error(f"Operation '{operation_name}' failed after {execution_time:.2f}s: {e}")
        if on_error:
            await on_error("error", e)
        raise


def resilient_endpoint(timeout: int = 30):
    """Decorator for API endpoints with built-in resilience patterns."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with resilient_operation(func.__name__, timeout=timeout):
                return await func(*args, **kwargs)
        return wrapper
    return decorator


class HealthChecker:
    """Centralized health checking for service dependencies."""

    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.last_check_results: Dict[str, Dict] = {}

    def register_check(self, name: str, check_func: Callable):
        """Register a health check function."""
        self.checks[name] = check_func

    async def run_checks(self) -> Dict[str, Dict]:
        """Run all registered health checks."""
        results = {}
        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                duration = time.time() - start_time
                results[name] = {
                    "status": "healthy",
                    "duration_ms": round(duration * 1000, 2),
                    "result": result,
                    "timestamp": time.time()
                }
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": time.time()
                }
        
        self.last_check_results = results
        return results

    def get_overall_status(self) -> str:
        """Get overall health status based on all checks."""
        if not self.last_check_results:
            return "unknown"
        
        statuses = [check["status"] for check in self.last_check_results.values()]
        return "healthy" if all(s == "healthy" for s in statuses) else "unhealthy"


# Global instances for service-wide use
health_checker = HealthChecker()
graceful_shutdown = GracefulShutdown()