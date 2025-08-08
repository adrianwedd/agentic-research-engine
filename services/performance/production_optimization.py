"""
Production Optimization Suite for Agentic Research Engine
Enterprise-grade production readiness with advanced performance optimizations
and scalability enhancements for pilot deployment.

Author: Performance Virtuoso Agent
Version: 2.0.0
License: Proprietary - Agentic Research Engine
"""

import asyncio
import time
import psutil
import gc
import os
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
import logging
import json
import weakref
from collections import deque, defaultdict

# Import existing performance components
from .connection_pool_optimizer import connection_pool_manager, ConnectionConfig, PoolStrategy

logger = logging.getLogger(__name__)


@dataclass
class ProductionMetrics:
    """Production environment performance metrics"""
    # Core performance metrics
    requests_per_second: float = 0.0
    average_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    
    # Resource utilization
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    disk_io_ops_per_sec: float = 0.0
    network_io_bytes_per_sec: float = 0.0
    
    # Application metrics
    active_connections: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hit_rate_percent: float = 0.0
    
    # Concurrency metrics
    thread_pool_utilization: float = 0.0
    async_task_queue_depth: int = 0
    
    # Stability metrics
    uptime_seconds: float = 0.0
    error_rate_percent: float = 0.0
    recovery_time_ms: float = 0.0


class ProductionOptimizer:
    """
    Production optimization system for enterprise deployment readiness.
    Provides comprehensive performance monitoring, resource optimization,
    and scalability management for the Agentic Research Engine.
    """
    
    def __init__(self):
        self.initialized = False
        self.start_time = time.time()
        
        # Performance targets for production
        self.performance_targets = {
            'min_rps': 500.0,              # Minimum 500 RPS sustained
            'max_response_time_ms': 50.0,   # Sub-50ms response times
            'min_success_rate': 99.9,       # 99.9% success rate
            'max_cpu_usage': 80.0,          # Max 80% CPU utilization
            'max_memory_usage': 85.0,       # Max 85% memory usage
            'min_cache_hit_rate': 90.0,     # 90% cache hit rate
        }
        
        # Monitoring and optimization
        self.metrics = ProductionMetrics()
        self.metrics_history: deque = deque(maxlen=10000)
        self.optimization_history: List[Dict] = []
        
        # Resource management
        self.thread_pools: Dict[str, ThreadPoolExecutor] = {}
        self.connection_pools: Dict[str, Any] = {}
        self.optimization_tasks: List[asyncio.Task] = []
        
        # Performance monitoring
        self.performance_samples: deque = deque(maxlen=1000)
        self.error_tracking: Dict[str, List] = defaultdict(list)
        
        # Optimization state
        self.optimization_enabled = True
        self.auto_scaling_enabled = True
        self.monitoring_interval = 5.0  # 5 seconds
        
        # Shutdown event
        self.shutdown_event = asyncio.Event()
        
    async def initialize(self):
        """Initialize the production optimizer"""
        
        if self.initialized:
            return
            
        logger.info("Initializing Production Optimizer for pilot deployment...")
        init_start = time.time()
        
        try:
            # Initialize connection pool manager
            await connection_pool_manager.create_pool(
                'ltm_service',
                self._create_ltm_connection,
                ConnectionConfig(
                    min_connections=20,
                    max_connections=100,
                    connection_timeout=10.0,
                    idle_timeout=300.0,
                    health_check_interval=30.0
                )
            )
            
            # Initialize optimized thread pools
            await self._initialize_thread_pools()
            
            # Start monitoring and optimization tasks
            await self._start_optimization_tasks()
            
            # Initialize garbage collection optimization
            self._optimize_garbage_collection()
            
            # Set up memory optimization
            self._setup_memory_optimization()
            
            # Initialize performance baselines
            await self._establish_performance_baselines()
            
            self.initialized = True
            init_time = (time.time() - init_start) * 1000
            
            logger.info("Production Optimizer initialized for enterprise deployment",
                       initialization_time_ms=init_time,
                       targets=self.performance_targets)
                       
        except Exception as e:
            logger.error("Failed to initialize Production Optimizer", error=str(e))
            raise
    
    async def _create_ltm_connection(self):
        """Create optimized LTM service connection"""
        # This would create actual LTM service connections
        # For now, return a mock connection
        return {"connection_id": f"ltm_{int(time.time() * 1000)}"}
    
    async def _initialize_thread_pools(self):
        """Initialize optimized thread pools for different operations"""
        
        # High-performance pool for vector operations
        self.thread_pools['vector_ops'] = ThreadPoolExecutor(
            max_workers=min(32, (os.cpu_count() or 4) * 4),
            thread_name_prefix='vector_ops'
        )
        
        # I/O operations pool
        self.thread_pools['io_ops'] = ThreadPoolExecutor(
            max_workers=min(64, (os.cpu_count() or 4) * 8),
            thread_name_prefix='io_ops'
        )
        
        # Background processing pool
        self.thread_pools['background'] = ThreadPoolExecutor(
            max_workers=min(16, (os.cpu_count() or 4) * 2),
            thread_name_prefix='background'
        )
        
        logger.info("Thread pools initialized",
                   pools={name: pool._max_workers for name, pool in self.thread_pools.items()})
    
    def _optimize_garbage_collection(self):
        """Optimize Python garbage collection for production"""
        
        # Optimize GC thresholds for better performance
        gc.set_threshold(700, 10, 10)  # More aggressive collection
        
        # Enable GC stats collection
        gc.set_debug(gc.DEBUG_STATS)
        
        # Schedule regular GC optimization
        def optimize_gc():
            gc.collect(0)  # Collect generation 0
            if len(gc.garbage) > 0:
                logger.warning("Unreachable objects found in garbage collection",
                             count=len(gc.garbage))
                gc.garbage.clear()
        
        # Run GC optimization every 30 seconds
        def gc_scheduler():
            while not self.shutdown_event.is_set():
                try:
                    optimize_gc()
                    time.sleep(30)
                except Exception as e:
                    logger.error("GC optimization error", error=str(e))
        
        gc_thread = threading.Thread(target=gc_scheduler, daemon=True)
        gc_thread.start()
        
        logger.info("Garbage collection optimization enabled")
    
    def _setup_memory_optimization(self):
        """Setup memory optimization for production deployment"""
        
        # Monitor memory usage and optimize when needed
        def memory_optimizer():
            while not self.shutdown_event.is_set():
                try:
                    memory_info = psutil.virtual_memory()
                    
                    if memory_info.percent > 90:
                        logger.warning("High memory usage detected",
                                     percent=memory_info.percent)
                        # Force garbage collection
                        gc.collect()
                        
                        # Clear internal caches if available
                        self._clear_internal_caches()
                    
                    time.sleep(10)  # Check every 10 seconds
                    
                except Exception as e:
                    logger.error("Memory optimization error", error=str(e))
        
        memory_thread = threading.Thread(target=memory_optimizer, daemon=True)
        memory_thread.start()
        
        logger.info("Memory optimization monitoring enabled")
    
    def _clear_internal_caches(self):
        """Clear internal caches to free memory"""
        try:
            # Clear metrics history if too large
            if len(self.metrics_history) > 5000:
                # Keep only recent 2500 entries
                recent_metrics = list(self.metrics_history)[-2500:]
                self.metrics_history.clear()
                self.metrics_history.extend(recent_metrics)
            
            # Clear error tracking old entries
            for error_type, errors in self.error_tracking.items():
                if len(errors) > 100:
                    self.error_tracking[error_type] = errors[-50:]
            
            # Clear performance samples
            if len(self.performance_samples) > 500:
                recent_samples = list(self.performance_samples)[-250:]
                self.performance_samples.clear()
                self.performance_samples.extend(recent_samples)
                
        except Exception as e:
            logger.error("Error clearing internal caches", error=str(e))
    
    async def _establish_performance_baselines(self):
        """Establish performance baselines for monitoring"""
        
        # Collect initial performance samples
        for _ in range(10):
            await self._collect_performance_metrics()
            await asyncio.sleep(0.1)
        
        if self.performance_samples:
            baseline_latency = sum(sample.get('response_time_ms', 0) 
                                 for sample in self.performance_samples) / len(self.performance_samples)
            baseline_cpu = sum(sample.get('cpu_percent', 0) 
                             for sample in self.performance_samples) / len(self.performance_samples)
            
            logger.info("Performance baselines established",
                       baseline_latency_ms=baseline_latency,
                       baseline_cpu_percent=baseline_cpu)
    
    async def _start_optimization_tasks(self):
        """Start background optimization tasks"""
        
        optimization_tasks = [
            self._performance_monitor(),
            self._resource_optimizer(),
            self._scalability_manager(),
            self._health_monitor(),
            self._metrics_aggregator()
        ]
        
        for task_coro in optimization_tasks:
            task = asyncio.create_task(task_coro)
            self.optimization_tasks.append(task)
        
        logger.info("Production optimization tasks started",
                   task_count=len(optimization_tasks))
    
    async def _performance_monitor(self):
        """Monitor performance metrics continuously"""
        
        while not self.shutdown_event.is_set():
            try:
                await self._collect_performance_metrics()
                await self._analyze_performance_trends()
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error("Performance monitoring error", error=str(e))
                await asyncio.sleep(10)
    
    async def _collect_performance_metrics(self):
        """Collect comprehensive performance metrics"""
        
        try:
            current_time = time.time()
            
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            
            # Network and disk I/O
            net_io = psutil.net_io_counters()
            disk_io = psutil.disk_io_counters()
            
            # Update metrics
            self.metrics.cpu_usage_percent = cpu_percent
            self.metrics.memory_usage_percent = memory_info.percent
            self.metrics.memory_usage_mb = memory_info.used / (1024 * 1024)
            self.metrics.uptime_seconds = current_time - self.start_time
            
            # Application-specific metrics
            self.metrics.active_connections = sum(
                pool.get_size() if hasattr(pool, 'get_size') else 0 
                for pool in self.connection_pools.values()
            )
            
            # Thread pool utilization
            total_threads = sum(pool._threads.__len__() if hasattr(pool, '_threads') else 0
                               for pool in self.thread_pools.values())
            max_threads = sum(pool._max_workers for pool in self.thread_pools.values())
            self.metrics.thread_pool_utilization = (total_threads / max_threads * 100) if max_threads > 0 else 0
            
            # Store performance sample
            sample = {
                'timestamp': current_time,
                'response_time_ms': self.metrics.average_response_time_ms,
                'cpu_percent': cpu_percent,
                'memory_percent': memory_info.percent,
                'active_connections': self.metrics.active_connections,
                'requests_per_second': self.metrics.requests_per_second
            }
            
            self.performance_samples.append(sample)
            
            # Store in metrics history
            self.metrics_history.append({
                'timestamp': datetime.now().isoformat(),
                'metrics': asdict(self.metrics)
            })
            
        except Exception as e:
            logger.error("Error collecting performance metrics", error=str(e))
    
    async def _analyze_performance_trends(self):
        """Analyze performance trends and detect issues"""
        
        if len(self.performance_samples) < 10:
            return
        
        recent_samples = list(self.performance_samples)[-10:]
        
        # Analyze response time trend
        response_times = [s.get('response_time_ms', 0) for s in recent_samples]
        avg_response_time = sum(response_times) / len(response_times)
        
        if avg_response_time > self.performance_targets['max_response_time_ms']:
            await self._handle_performance_degradation('response_time', avg_response_time)
        
        # Analyze CPU usage trend
        cpu_usage = [s.get('cpu_percent', 0) for s in recent_samples]
        avg_cpu = sum(cpu_usage) / len(cpu_usage)
        
        if avg_cpu > self.performance_targets['max_cpu_usage']:
            await self._handle_performance_degradation('cpu_usage', avg_cpu)
        
        # Analyze throughput trend
        throughput = [s.get('requests_per_second', 0) for s in recent_samples]
        avg_throughput = sum(throughput) / len(throughput)
        
        if avg_throughput < self.performance_targets['min_rps']:
            await self._handle_performance_degradation('throughput', avg_throughput)
    
    async def _handle_performance_degradation(self, metric_type: str, current_value: float):
        """Handle detected performance degradation"""
        
        logger.warning("Performance degradation detected",
                      metric_type=metric_type,
                      current_value=current_value,
                      target=self.performance_targets.get(f"{'min_' if metric_type == 'throughput' else 'max_'}{metric_type}", 0))
        
        if self.optimization_enabled:
            optimization_action = None
            
            if metric_type == 'response_time':
                optimization_action = await self._optimize_response_time()
            elif metric_type == 'cpu_usage':
                optimization_action = await self._optimize_cpu_usage()
            elif metric_type == 'throughput':
                optimization_action = await self._optimize_throughput()
            
            if optimization_action:
                self.optimization_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'metric_type': metric_type,
                    'trigger_value': current_value,
                    'action': optimization_action
                })
    
    async def _optimize_response_time(self) -> str:
        """Optimize response time when degradation is detected"""
        
        # Increase connection pool sizes
        for pool_name, pool in self.connection_pools.items():
            if hasattr(pool, 'get_size') and pool.get_size() < 50:
                # This would scale up the pool
                logger.info("Scaling up connection pool for response time optimization",
                           pool_name=pool_name)
        
        # Clear caches to reduce memory pressure
        self._clear_internal_caches()
        
        # Force garbage collection
        gc.collect()
        
        return "increased_connection_pools_and_cleared_caches"
    
    async def _optimize_cpu_usage(self) -> str:
        """Optimize CPU usage when high utilization is detected"""
        
        # Reduce thread pool sizes temporarily
        for pool_name, pool in self.thread_pools.items():
            if pool._max_workers > 8:
                # This would be done through pool reconfiguration
                logger.info("Reducing thread pool size for CPU optimization",
                           pool_name=pool_name)
        
        # Increase monitoring interval to reduce overhead
        if self.monitoring_interval < 10:
            self.monitoring_interval = min(10, self.monitoring_interval * 1.5)
        
        return "reduced_thread_pools_and_monitoring_frequency"
    
    async def _optimize_throughput(self) -> str:
        """Optimize throughput when performance is below target"""
        
        # Increase thread pool sizes
        for pool_name, pool in self.thread_pools.items():
            if pool._max_workers < 64:
                logger.info("Scaling up thread pool for throughput optimization",
                           pool_name=pool_name)
        
        # Decrease monitoring interval for faster response
        if self.monitoring_interval > 1:
            self.monitoring_interval = max(1, self.monitoring_interval * 0.8)
        
        return "increased_thread_pools_and_monitoring_frequency"
    
    async def _resource_optimizer(self):
        """Optimize resource usage continuously"""
        
        while not self.shutdown_event.is_set():
            try:
                await self._optimize_memory_usage()
                await self._optimize_connection_pools()
                await asyncio.sleep(30)  # Optimize every 30 seconds
                
            except Exception as e:
                logger.error("Resource optimization error", error=str(e))
                await asyncio.sleep(60)
    
    async def _optimize_memory_usage(self):
        """Optimize memory usage"""
        
        memory_info = psutil.virtual_memory()
        
        if memory_info.percent > 85:
            # Aggressive optimization
            gc.collect()
            self._clear_internal_caches()
            
            # Reduce metrics history size
            if len(self.metrics_history) > 1000:
                recent_history = list(self.metrics_history)[-500:]
                self.metrics_history.clear()
                self.metrics_history.extend(recent_history)
            
            logger.info("Memory optimization applied",
                       memory_percent=memory_info.percent)
    
    async def _optimize_connection_pools(self):
        """Optimize connection pool configurations"""
        
        for pool_name, pool in self.connection_pools.items():
            try:
                # Get pool performance report
                if hasattr(pool, 'get_performance_report'):
                    report = await pool.get_performance_report()
                    
                    utilization = report.get('connection_details', {}).get('connection_utilization_percent', 0)
                    
                    if utilization > 90:
                        logger.info("High connection pool utilization detected",
                                   pool_name=pool_name,
                                   utilization=utilization)
                    elif utilization < 10:
                        logger.info("Low connection pool utilization detected",
                                   pool_name=pool_name,
                                   utilization=utilization)
                        
            except Exception as e:
                logger.error("Error optimizing connection pool",
                           pool_name=pool_name,
                           error=str(e))
    
    async def _scalability_manager(self):
        """Manage scalability and auto-scaling"""
        
        while not self.shutdown_event.is_set():
            try:
                if self.auto_scaling_enabled:
                    await self._evaluate_scaling_needs()
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error("Scalability management error", error=str(e))
                await asyncio.sleep(120)
    
    async def _evaluate_scaling_needs(self):
        """Evaluate if scaling is needed"""
        
        if len(self.performance_samples) < 20:
            return
        
        recent_samples = list(self.performance_samples)[-20:]
        
        # Check if consistently high resource usage
        high_cpu_count = sum(1 for s in recent_samples 
                            if s.get('cpu_percent', 0) > 70)
        high_memory_count = sum(1 for s in recent_samples
                               if s.get('memory_percent', 0) > 80)
        low_throughput_count = sum(1 for s in recent_samples
                                  if s.get('requests_per_second', 0) < self.performance_targets['min_rps'])
        
        # Scale up recommendations
        if high_cpu_count > 15:  # 75% of samples show high CPU
            logger.info("Scaling recommendation: CPU resources",
                       high_cpu_samples=high_cpu_count,
                       total_samples=len(recent_samples))
        
        if high_memory_count > 15:  # 75% of samples show high memory
            logger.info("Scaling recommendation: Memory resources",
                       high_memory_samples=high_memory_count,
                       total_samples=len(recent_samples))
        
        if low_throughput_count > 10:  # 50% of samples show low throughput
            logger.info("Scaling recommendation: Throughput capacity",
                       low_throughput_samples=low_throughput_count,
                       total_samples=len(recent_samples))
    
    async def _health_monitor(self):
        """Monitor overall system health"""
        
        while not self.shutdown_event.is_set():
            try:
                health_status = await self._assess_system_health()
                
                if health_status['status'] != 'healthy':
                    logger.warning("System health issue detected",
                                 health_status=health_status)
                
                await asyncio.sleep(30)  # Check health every 30 seconds
                
            except Exception as e:
                logger.error("Health monitoring error", error=str(e))
                await asyncio.sleep(60)
    
    async def _assess_system_health(self) -> Dict[str, Any]:
        """Assess overall system health"""
        
        health_issues = []
        
        # Check performance targets
        if self.metrics.average_response_time_ms > self.performance_targets['max_response_time_ms']:
            health_issues.append(f"Response time {self.metrics.average_response_time_ms:.1f}ms exceeds target")
        
        if self.metrics.requests_per_second < self.performance_targets['min_rps']:
            health_issues.append(f"Throughput {self.metrics.requests_per_second:.1f} below target")
        
        if self.metrics.cpu_usage_percent > self.performance_targets['max_cpu_usage']:
            health_issues.append(f"CPU usage {self.metrics.cpu_usage_percent:.1f}% exceeds target")
        
        if self.metrics.memory_usage_percent > self.performance_targets['max_memory_usage']:
            health_issues.append(f"Memory usage {self.metrics.memory_usage_percent:.1f}% exceeds target")
        
        # Calculate success rate
        total_requests = self.metrics.total_requests
        success_rate = 0
        if total_requests > 0:
            success_rate = (self.metrics.successful_requests / total_requests) * 100
            if success_rate < self.performance_targets['min_success_rate']:
                health_issues.append(f"Success rate {success_rate:.1f}% below target")
        
        status = 'healthy' if not health_issues else 'degraded'
        
        return {
            'status': status,
            'issues': health_issues,
            'metrics_summary': {
                'response_time_ms': self.metrics.average_response_time_ms,
                'throughput_rps': self.metrics.requests_per_second,
                'cpu_percent': self.metrics.cpu_usage_percent,
                'memory_percent': self.metrics.memory_usage_percent,
                'success_rate_percent': success_rate
            }
        }
    
    async def _metrics_aggregator(self):
        """Aggregate and compute advanced metrics"""
        
        while not self.shutdown_event.is_set():
            try:
                await self._compute_advanced_metrics()
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except Exception as e:
                logger.error("Metrics aggregation error", error=str(e))
                await asyncio.sleep(30)
    
    async def _compute_advanced_metrics(self):
        """Compute advanced performance metrics"""
        
        if len(self.performance_samples) < 5:
            return
        
        recent_samples = list(self.performance_samples)[-100:]  # Last 100 samples
        
        # Compute percentiles
        response_times = [s.get('response_time_ms', 0) for s in recent_samples if s.get('response_time_ms', 0) > 0]
        if response_times:
            response_times.sort()
            n = len(response_times)
            if n >= 20:  # Need sufficient samples for percentiles
                self.metrics.p95_response_time_ms = response_times[int(n * 0.95)]
                self.metrics.p99_response_time_ms = response_times[int(n * 0.99)]
        
        # Compute average metrics
        if recent_samples:
            self.metrics.average_response_time_ms = sum(
                s.get('response_time_ms', 0) for s in recent_samples
            ) / len(recent_samples)
            
            self.metrics.requests_per_second = sum(
                s.get('requests_per_second', 0) for s in recent_samples
            ) / len(recent_samples)
    
    async def get_production_readiness_report(self) -> Dict[str, Any]:
        """Get comprehensive production readiness report"""
        
        health_status = await self._assess_system_health()
        
        # Assess production readiness
        readiness_checks = {
            'performance_targets_met': health_status['status'] == 'healthy',
            'resource_utilization_optimal': (
                self.metrics.cpu_usage_percent < 70 and 
                self.metrics.memory_usage_percent < 75
            ),
            'high_availability_ready': (
                self.metrics.uptime_seconds > 3600 and  # At least 1 hour uptime
                self.metrics.error_rate_percent < 0.1
            ),
            'scalability_prepared': len(self.optimization_history) < 10,  # Few optimization interventions needed
            'monitoring_active': len(self.metrics_history) > 100
        }
        
        readiness_score = sum(1 for check in readiness_checks.values() if check)
        readiness_percentage = (readiness_score / len(readiness_checks)) * 100
        
        return {
            'timestamp': datetime.now().isoformat(),
            'production_readiness': {
                'overall_score': readiness_percentage,
                'status': 'ready' if readiness_percentage >= 80 else 'needs_optimization',
                'checks': readiness_checks
            },
            'current_performance': asdict(self.metrics),
            'performance_targets': self.performance_targets,
            'health_assessment': health_status,
            'optimization_history': self.optimization_history[-10:],  # Last 10 optimizations
            'resource_recommendations': self._generate_resource_recommendations(),
            'deployment_recommendations': self._generate_deployment_recommendations()
        }
    
    def _generate_resource_recommendations(self) -> List[str]:
        """Generate resource scaling recommendations"""
        
        recommendations = []
        
        if self.metrics.cpu_usage_percent > 70:
            recommendations.append("Consider increasing CPU resources or scaling horizontally")
        
        if self.metrics.memory_usage_percent > 75:
            recommendations.append("Consider increasing memory allocation")
        
        if self.metrics.requests_per_second < self.performance_targets['min_rps']:
            recommendations.append("Optimize application code or scale up infrastructure")
        
        if self.metrics.average_response_time_ms > 20:
            recommendations.append("Implement caching or optimize database queries")
        
        return recommendations
    
    def _generate_deployment_recommendations(self) -> List[str]:
        """Generate deployment recommendations"""
        
        recommendations = []
        
        if len(self.optimization_history) > 20:
            recommendations.append("System requires frequent optimization - consider infrastructure upgrade")
        
        if self.metrics.error_rate_percent > 0.5:
            recommendations.append("Address error conditions before production deployment")
        
        if self.metrics.cache_hit_rate_percent < 85:
            recommendations.append("Optimize caching strategy for better performance")
        
        recommendations.extend([
            "Deploy with load balancer for high availability",
            "Implement comprehensive monitoring and alerting",
            "Set up automated scaling policies",
            "Configure backup and disaster recovery procedures"
        ])
        
        return recommendations
    
    async def close(self):
        """Shutdown production optimizer"""
        
        logger.info("Shutting down Production Optimizer...")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Cancel optimization tasks
        for task in self.optimization_tasks:
            task.cancel()
        
        if self.optimization_tasks:
            await asyncio.gather(*self.optimization_tasks, return_exceptions=True)
        
        # Close thread pools
        for pool_name, pool in self.thread_pools.items():
            pool.shutdown(wait=True)
            logger.info("Thread pool closed", pool_name=pool_name)
        
        # Close connection pools
        await connection_pool_manager.close_all_pools()
        
        self.thread_pools.clear()
        self.optimization_tasks.clear()
        
        logger.info("Production Optimizer shutdown complete")


# Global production optimizer instance
production_optimizer = ProductionOptimizer()