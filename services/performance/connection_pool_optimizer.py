"""
Connection Pool Optimizer for Agentic Research Engine
Enterprise-grade connection pooling with adaptive scaling and monitoring
"""

import asyncio
import time
import statistics
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
from contextlib import asynccontextmanager
import threading

try:
    import aiohttp
    import asyncpg
    import aiomysql
    ASYNC_CLIENTS_AVAILABLE = True
except ImportError:
    ASYNC_CLIENTS_AVAILABLE = False

logger = logging.getLogger(__name__)

T = TypeVar('T')

class PoolStrategy(Enum):
    """Connection pool strategies"""
    FIXED_SIZE = "fixed_size"
    ADAPTIVE = "adaptive"
    ELASTIC = "elastic"
    CIRCUIT_BREAKER = "circuit_breaker"

@dataclass
class PoolMetrics:
    """Connection pool metrics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    pool_hits: int = 0
    pool_misses: int = 0
    average_wait_time_ms: float = 0.0
    average_connection_lifetime_ms: float = 0.0
    throughput_per_second: float = 0.0

@dataclass
class ConnectionConfig:
    """Connection configuration"""
    min_connections: int = 5
    max_connections: int = 50
    connection_timeout: float = 30.0
    idle_timeout: float = 300.0
    retry_attempts: int = 3
    retry_delay: float = 1.0
    health_check_interval: float = 60.0

class ConnectionPool(Generic[T]):
    """
    Generic connection pool with enterprise features:
    - Adaptive pool sizing based on load
    - Connection health monitoring
    - Circuit breaker pattern
    - Performance metrics collection
    - Graceful degradation
    """
    
    def __init__(self, 
                 connection_factory: Callable,
                 config: ConnectionConfig,
                 pool_name: str = "default"):
        
        self.connection_factory = connection_factory
        self.config = config
        self.pool_name = pool_name
        
        # Pool state
        self.available_connections: asyncio.Queue = asyncio.Queue()
        self.all_connections: List[T] = []
        self.connection_metrics: Dict[T, Dict] = {}
        
        # Performance tracking
        self.metrics = PoolMetrics()
        self.performance_history: List[Dict] = []
        
        # Pool management
        self.lock = asyncio.Lock()
        self.shutdown_event = asyncio.Event()
        self.health_check_task: Optional[asyncio.Task] = None
        
        # Circuit breaker state
        self.circuit_breaker_open = False
        self.circuit_breaker_failures = 0
        self.circuit_breaker_last_failure = 0
        self.circuit_breaker_timeout = 60.0  # 1 minute
        
        self.initialized = False
    
    async def initialize(self):
        """Initialize the connection pool"""
        if self.initialized:
            return
            
        logger.info(f"Initializing connection pool: {self.pool_name}")
        start_time = time.time()
        
        try:
            # Create initial connections
            for _ in range(self.config.min_connections):
                connection = await self._create_connection()
                if connection:
                    await self.available_connections.put(connection)
                    self.all_connections.append(connection)
                    self.connection_metrics[connection] = {
                        'created_at': time.time(),
                        'last_used': time.time(),
                        'use_count': 0,
                        'errors': 0
                    }
            
            # Start health check task
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            self.metrics.total_connections = len(self.all_connections)
            self.metrics.idle_connections = len(self.all_connections)
            
            self.initialized = True
            
            init_time = (time.time() - start_time) * 1000
            logger.info(f"Connection pool {self.pool_name} initialized with "
                       f"{len(self.all_connections)} connections in {init_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"Failed to initialize connection pool {self.pool_name}: {str(e)}")
            raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get connection from pool with context manager"""
        
        start_time = time.time()
        connection = None
        
        try:
            # Check circuit breaker
            if self._is_circuit_breaker_open():
                raise Exception("Circuit breaker is open")
            
            # Get connection from pool
            connection = await self._get_connection_from_pool()
            
            if connection is None:
                self.metrics.pool_misses += 1
                raise Exception("No available connections")
            
            self.metrics.pool_hits += 1
            self.metrics.active_connections += 1
            self.metrics.idle_connections -= 1
            
            # Update connection metrics
            conn_metrics = self.connection_metrics[connection]
            conn_metrics['last_used'] = time.time()
            conn_metrics['use_count'] += 1
            
            # Update wait time metrics
            wait_time = (time.time() - start_time) * 1000
            self._update_wait_time_metrics(wait_time)
            
            yield connection
            
        except Exception as e:
            logger.error(f"Connection pool error: {str(e)}")
            self._handle_connection_error(connection)
            raise
            
        finally:
            # Return connection to pool
            if connection:
                await self._return_connection_to_pool(connection)
                self.metrics.active_connections -= 1
                self.metrics.idle_connections += 1
    
    async def _get_connection_from_pool(self) -> Optional[T]:
        """Get connection from available pool"""
        
        try:
            # Try to get existing connection
            connection = await asyncio.wait_for(
                self.available_connections.get(),
                timeout=self.config.connection_timeout
            )
            
            # Validate connection health
            if await self._is_connection_healthy(connection):
                return connection
            else:
                # Connection is unhealthy, remove and create new one
                await self._remove_connection(connection)
                return await self._create_new_connection_if_needed()
                
        except asyncio.TimeoutError:
            # No available connections, try to create new one
            return await self._create_new_connection_if_needed()
    
    async def _create_new_connection_if_needed(self) -> Optional[T]:
        """Create new connection if under max limit"""
        
        async with self.lock:
            if len(self.all_connections) < self.config.max_connections:
                connection = await self._create_connection()
                if connection:
                    self.all_connections.append(connection)
                    self.connection_metrics[connection] = {
                        'created_at': time.time(),
                        'last_used': time.time(),
                        'use_count': 0,
                        'errors': 0
                    }
                    self.metrics.total_connections += 1
                    return connection
        
        return None
    
    async def _create_connection(self) -> Optional[T]:
        """Create a new connection"""
        
        try:
            connection = await self.connection_factory()
            return connection
            
        except Exception as e:
            logger.error(f"Failed to create connection: {str(e)}")
            self.metrics.failed_connections += 1
            self._update_circuit_breaker_on_failure()
            return None
    
    async def _return_connection_to_pool(self, connection: T):
        """Return connection to the available pool"""
        
        try:
            if await self._is_connection_healthy(connection):
                await self.available_connections.put(connection)
            else:
                await self._remove_connection(connection)
                
        except Exception as e:
            logger.error(f"Error returning connection to pool: {str(e)}")
            await self._remove_connection(connection)
    
    async def _is_connection_healthy(self, connection: T) -> bool:
        """Check if connection is healthy"""
        
        try:
            # Basic connection validation
            if hasattr(connection, 'ping'):
                await connection.ping()
            elif hasattr(connection, 'execute'):
                # For database connections
                await connection.execute('SELECT 1')
            elif hasattr(connection, 'get'):
                # For HTTP connections
                pass  # HTTP connections are typically stateless
            
            return True
            
        except Exception as e:
            logger.debug(f"Connection health check failed: {str(e)}")
            return False
    
    async def _remove_connection(self, connection: T):
        """Remove unhealthy connection from pool"""
        
        try:
            # Close connection if possible
            if hasattr(connection, 'close'):
                await connection.close()
            
            # Remove from tracking
            if connection in self.all_connections:
                self.all_connections.remove(connection)
                self.metrics.total_connections -= 1
            
            if connection in self.connection_metrics:
                del self.connection_metrics[connection]
                
        except Exception as e:
            logger.error(f"Error removing connection: {str(e)}")
    
    async def _health_check_loop(self):
        """Background health check for idle connections"""
        
        while not self.shutdown_event.is_set():
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                current_time = time.time()
                unhealthy_connections = []
                
                # Check idle connections for health and timeout
                for connection in self.all_connections:
                    metrics = self.connection_metrics.get(connection, {})
                    last_used = metrics.get('last_used', 0)
                    
                    # Check idle timeout
                    if current_time - last_used > self.config.idle_timeout:
                        unhealthy_connections.append(connection)
                        continue
                    
                    # Periodic health check for idle connections
                    if not await self._is_connection_healthy(connection):
                        unhealthy_connections.append(connection)
                
                # Remove unhealthy connections
                for connection in unhealthy_connections:
                    await self._remove_connection(connection)
                
                # Ensure minimum connections
                while len(self.all_connections) < self.config.min_connections:
                    connection = await self._create_connection()
                    if connection:
                        self.all_connections.append(connection)
                        await self.available_connections.put(connection)
                        self.connection_metrics[connection] = {
                            'created_at': current_time,
                            'last_used': current_time,
                            'use_count': 0,
                            'errors': 0
                        }
                        self.metrics.total_connections += 1
                        self.metrics.idle_connections += 1
                
                # Update metrics
                self._update_pool_metrics()
                
            except Exception as e:
                logger.error(f"Health check loop error: {str(e)}")
    
    def _handle_connection_error(self, connection: Optional[T]):
        """Handle connection error"""
        
        if connection and connection in self.connection_metrics:
            self.connection_metrics[connection]['errors'] += 1
        
        self._update_circuit_breaker_on_failure()
    
    def _update_circuit_breaker_on_failure(self):
        """Update circuit breaker state on failure"""
        
        self.circuit_breaker_failures += 1
        self.circuit_breaker_last_failure = time.time()
        
        # Open circuit breaker if too many failures
        if self.circuit_breaker_failures >= 5:
            self.circuit_breaker_open = True
            logger.warning(f"Circuit breaker opened for pool {self.pool_name}")
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        
        if not self.circuit_breaker_open:
            return False
        
        # Check if circuit breaker should be closed (timeout expired)
        if time.time() - self.circuit_breaker_last_failure > self.circuit_breaker_timeout:
            self.circuit_breaker_open = False
            self.circuit_breaker_failures = 0
            logger.info(f"Circuit breaker closed for pool {self.pool_name}")
            return False
        
        return True
    
    def _update_wait_time_metrics(self, wait_time_ms: float):
        """Update wait time metrics"""
        
        total_ops = self.metrics.pool_hits + self.metrics.pool_misses
        if total_ops > 0:
            self.metrics.average_wait_time_ms = (
                (self.metrics.average_wait_time_ms * (total_ops - 1) + wait_time_ms) / total_ops
            )
    
    def _update_pool_metrics(self):
        """Update pool performance metrics"""
        
        self.metrics.idle_connections = self.available_connections.qsize()
        self.metrics.active_connections = (self.metrics.total_connections - 
                                          self.metrics.idle_connections)
        
        # Calculate throughput
        current_time = time.time()
        if hasattr(self, '_last_throughput_update'):
            time_delta = current_time - self._last_throughput_update
            if time_delta > 0:
                ops_delta = self.metrics.pool_hits - getattr(self, '_last_pool_hits', 0)
                self.metrics.throughput_per_second = ops_delta / time_delta
        
        self._last_throughput_update = current_time
        self._last_pool_hits = self.metrics.pool_hits
        
        # Record performance history
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'metrics': asdict(self.metrics)
        })
        
        # Keep last 1000 entries
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive pool performance report"""
        
        self._update_pool_metrics()
        
        return {
            'pool_name': self.pool_name,
            'metrics': asdict(self.metrics),
            'configuration': asdict(self.config),
            'circuit_breaker': {
                'open': self.circuit_breaker_open,
                'failures': self.circuit_breaker_failures,
                'last_failure_ago_seconds': time.time() - self.circuit_breaker_last_failure
            },
            'connection_details': {
                'total_connections': len(self.all_connections),
                'available_connections': self.available_connections.qsize(),
                'average_connection_age_seconds': self._calculate_average_connection_age(),
                'connection_utilization_percent': (self.metrics.active_connections / 
                                                 max(1, self.metrics.total_connections)) * 100
            },
            'performance_analysis': {
                'efficiency_score': self._calculate_efficiency_score(),
                'recommendations': self._generate_optimization_recommendations()
            }
        }
    
    def _calculate_average_connection_age(self) -> float:
        """Calculate average age of connections"""
        
        if not self.connection_metrics:
            return 0.0
        
        current_time = time.time()
        ages = [current_time - metrics['created_at'] 
                for metrics in self.connection_metrics.values()]
        
        return statistics.mean(ages) if ages else 0.0
    
    def _calculate_efficiency_score(self) -> float:
        """Calculate pool efficiency score (0-100)"""
        
        total_requests = self.metrics.pool_hits + self.metrics.pool_misses
        if total_requests == 0:
            return 100.0
        
        hit_rate = (self.metrics.pool_hits / total_requests) * 100
        wait_time_score = max(0, 100 - self.metrics.average_wait_time_ms)
        utilization_score = min(100, (self.metrics.active_connections / 
                                     max(1, self.metrics.total_connections)) * 100)
        
        return (hit_rate * 0.4 + wait_time_score * 0.4 + utilization_score * 0.2)
    
    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate pool optimization recommendations"""
        
        recommendations = []
        
        # Hit rate recommendations
        total_requests = self.metrics.pool_hits + self.metrics.pool_misses
        if total_requests > 0:
            hit_rate = (self.metrics.pool_hits / total_requests) * 100
            if hit_rate < 90:
                recommendations.append("Consider increasing min_connections for better hit rate")
        
        # Wait time recommendations
        if self.metrics.average_wait_time_ms > 50:
            recommendations.append("High wait times detected - increase max_connections")
        
        # Circuit breaker recommendations
        if self.circuit_breaker_failures > 0:
            recommendations.append("Connection failures detected - check connection factory")
        
        # Utilization recommendations
        utilization = (self.metrics.active_connections / max(1, self.metrics.total_connections)) * 100
        if utilization > 90:
            recommendations.append("High utilization - consider scaling up")
        elif utilization < 20:
            recommendations.append("Low utilization - consider reducing min_connections")
        
        return recommendations
    
    async def close(self):
        """Close connection pool and cleanup resources"""
        
        logger.info(f"Closing connection pool: {self.pool_name}")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Cancel health check task
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for connection in self.all_connections[:]:
            try:
                await self._remove_connection(connection)
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")
        
        # Clear state
        self.all_connections.clear()
        self.connection_metrics.clear()
        
        logger.info(f"Connection pool {self.pool_name} closed")

class ConnectionPoolManager:
    """
    Manager for multiple connection pools with global optimization
    """
    
    def __init__(self):
        self.pools: Dict[str, ConnectionPool] = {}
        self.global_metrics = PoolMetrics()
        
    async def create_pool(self, 
                         pool_name: str, 
                         connection_factory: Callable,
                         config: ConnectionConfig) -> ConnectionPool:
        """Create and initialize a new connection pool"""
        
        if pool_name in self.pools:
            raise ValueError(f"Pool {pool_name} already exists")
        
        pool = ConnectionPool(connection_factory, config, pool_name)
        await pool.initialize()
        
        self.pools[pool_name] = pool
        logger.info(f"Connection pool {pool_name} created and initialized")
        
        return pool
    
    def get_pool(self, pool_name: str) -> Optional[ConnectionPool]:
        """Get connection pool by name"""
        return self.pools.get(pool_name)
    
    async def get_global_performance_report(self) -> Dict[str, Any]:
        """Get performance report for all pools"""
        
        pool_reports = {}
        total_connections = 0
        total_active = 0
        total_throughput = 0.0
        
        for pool_name, pool in self.pools.items():
            report = await pool.get_performance_report()
            pool_reports[pool_name] = report
            
            total_connections += report['metrics']['total_connections']
            total_active += report['metrics']['active_connections']
            total_throughput += report['metrics']['throughput_per_second']
        
        return {
            'timestamp': datetime.now().isoformat(),
            'global_summary': {
                'total_pools': len(self.pools),
                'total_connections': total_connections,
                'total_active_connections': total_active,
                'global_throughput_per_second': total_throughput,
                'global_utilization_percent': (total_active / max(1, total_connections)) * 100
            },
            'pool_reports': pool_reports,
            'optimization_recommendations': self._generate_global_recommendations(pool_reports)
        }
    
    def _generate_global_recommendations(self, pool_reports: Dict) -> List[str]:
        """Generate global optimization recommendations"""
        
        recommendations = []
        
        # Analyze cross-pool patterns
        low_utilization_pools = []
        high_utilization_pools = []
        
        for pool_name, report in pool_reports.items():
            utilization = report['connection_details']['connection_utilization_percent']
            if utilization < 20:
                low_utilization_pools.append(pool_name)
            elif utilization > 90:
                high_utilization_pools.append(pool_name)
        
        if low_utilization_pools:
            recommendations.append(f"Consider consolidating or reducing pools: {', '.join(low_utilization_pools)}")
        
        if high_utilization_pools:
            recommendations.append(f"Consider scaling up pools: {', '.join(high_utilization_pools)}")
        
        return recommendations
    
    async def close_all_pools(self):
        """Close all connection pools"""
        
        logger.info("Closing all connection pools...")
        
        for pool_name, pool in self.pools.items():
            try:
                await pool.close()
            except Exception as e:
                logger.error(f"Error closing pool {pool_name}: {str(e)}")
        
        self.pools.clear()
        logger.info("All connection pools closed")

# Global connection pool manager
connection_pool_manager = ConnectionPoolManager()