"""
Advanced Caching System for Agentic Research Engine
Enterprise-grade distributed caching with Redis, LRU, and TTL strategies
"""

import asyncio
import json
import time
import hashlib
from typing import Any, Dict, Optional, Union, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    from functools import lru_cache
    import pickle
except ImportError:
    pass

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache strategy types"""
    LRU = "lru"
    TTL = "ttl"
    LRU_TTL = "lru_ttl"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_writes: int = 0
    cache_evictions: int = 0
    average_response_time_ms: float = 0.0
    hit_rate_percent: float = 0.0
    memory_usage_mb: float = 0.0

class AdvancedCacheSystem:
    """
    Enterprise advanced caching system providing:
    - Redis distributed caching with connection pooling
    - Multi-tier caching (L1: local LRU, L2: Redis)
    - TTL-based cache expiration
    - Cache warming and preloading
    - Performance metrics and monitoring
    - Intelligent cache invalidation
    """
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 local_cache_size: int = 2048,
                 default_ttl_seconds: int = 3600,
                 enable_metrics: bool = True):
        
        self.redis_url = redis_url
        self.local_cache_size = local_cache_size
        self.default_ttl_seconds = default_ttl_seconds
        self.enable_metrics = enable_metrics
        
        # Redis connection pool
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self.redis_client: Optional[redis.Redis] = None
        
        # Local LRU cache
        self.local_cache: Dict[str, Tuple[Any, float]] = {}
        self.cache_order: List[str] = []
        
        # Performance metrics
        self.metrics = CacheMetrics()
        self.performance_history: List[Dict] = []
        
        # Cache configuration
        self.cache_strategies: Dict[str, CacheStrategy] = {}
        self.ttl_config: Dict[str, int] = {}
        
        self.initialized = False
    
    async def initialize(self):
        """Initialize the advanced caching system"""
        if self.initialized:
            return
            
        logger.info("Initializing Advanced Caching System...")
        start_time = time.time()
        
        try:
            # Initialize Redis connection pool if available
            if REDIS_AVAILABLE:
                self.redis_pool = redis.ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                self.redis_client = redis.Redis(connection_pool=self.redis_pool)
                
                # Test Redis connection
                await self.redis_client.ping()
                logger.info("Redis connection pool initialized successfully")
            else:
                logger.warning("Redis not available, using local cache only")
            
            # Initialize cache strategies for different data types
            await self._setup_cache_strategies()
            
            # Start cache maintenance tasks
            if self.enable_metrics:
                asyncio.create_task(self._cache_maintenance_loop())
            
            self.initialized = True
            
            init_time = (time.time() - start_time) * 1000
            logger.info(f"Advanced Caching System initialized in {init_time:.2f}ms")
            
        except Exception as e:
            logger.error(f"Failed to initialize caching system: {str(e)}")
            # Continue with local cache only
            self.redis_client = None
            self.initialized = True
    
    async def _setup_cache_strategies(self):
        """Setup cache strategies for different data types"""
        
        # Default cache strategies and TTLs
        strategies = {
            'embedding': (CacheStrategy.LRU_TTL, 3600),  # 1 hour
            'vector_search': (CacheStrategy.LRU_TTL, 1800),  # 30 minutes
            'ltm_query': (CacheStrategy.TTL, 600),  # 10 minutes
            'api_response': (CacheStrategy.LRU_TTL, 300),  # 5 minutes
            'model_inference': (CacheStrategy.WRITE_THROUGH, 7200),  # 2 hours
            'user_session': (CacheStrategy.TTL, 1800),  # 30 minutes
        }
        
        for data_type, (strategy, ttl) in strategies.items():
            self.cache_strategies[data_type] = strategy
            self.ttl_config[data_type] = ttl
    
    def _generate_cache_key(self, namespace: str, identifier: Union[str, Dict]) -> str:
        """Generate cache key with namespace"""
        if isinstance(identifier, dict):
            # Create deterministic hash for dict keys
            sorted_items = json.dumps(identifier, sort_keys=True)
            identifier = hashlib.md5(sorted_items.encode()).hexdigest()
        
        return f"are_cache:{namespace}:{identifier}"
    
    async def get(self, namespace: str, key: Union[str, Dict], 
                  default: Any = None) -> Optional[Any]:
        """Get value from cache with multi-tier lookup"""
        
        start_time = time.time()
        cache_key = self._generate_cache_key(namespace, key)
        
        try:
            self.metrics.total_requests += 1
            
            # L1 Cache: Local LRU lookup
            local_result = self._get_from_local_cache(cache_key)
            if local_result is not None:
                self.metrics.cache_hits += 1
                self._update_performance_metrics(start_time, True)
                return local_result
            
            # L2 Cache: Redis lookup
            if self.redis_client:
                try:
                    redis_data = await self.redis_client.get(cache_key)
                    if redis_data:
                        # Deserialize and add to local cache
                        value = pickle.loads(redis_data)
                        self._add_to_local_cache(cache_key, value, namespace)
                        
                        self.metrics.cache_hits += 1
                        self._update_performance_metrics(start_time, True)
                        return value
                        
                except Exception as e:
                    logger.warning(f"Redis get failed: {str(e)}")
            
            # Cache miss
            self.metrics.cache_misses += 1
            self._update_performance_metrics(start_time, False)
            return default
            
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            self.metrics.cache_misses += 1
            return default
    
    async def set(self, namespace: str, key: Union[str, Dict], value: Any, 
                  ttl: Optional[int] = None, strategy: Optional[CacheStrategy] = None) -> bool:
        """Set value in cache with specified strategy"""
        
        start_time = time.time()
        cache_key = self._generate_cache_key(namespace, key)
        
        try:
            # Determine TTL and strategy
            if ttl is None:
                ttl = self.ttl_config.get(namespace, self.default_ttl_seconds)
            
            if strategy is None:
                strategy = self.cache_strategies.get(namespace, CacheStrategy.LRU_TTL)
            
            # Store in local cache
            self._add_to_local_cache(cache_key, value, namespace, ttl)
            
            # Store in Redis if available
            if self.redis_client:
                try:
                    serialized_value = pickle.dumps(value)
                    
                    if strategy in [CacheStrategy.TTL, CacheStrategy.LRU_TTL]:
                        await self.redis_client.setex(cache_key, ttl, serialized_value)
                    else:
                        await self.redis_client.set(cache_key, serialized_value)
                    
                except Exception as e:
                    logger.warning(f"Redis set failed: {str(e)}")
            
            self.metrics.cache_writes += 1
            self._update_performance_metrics(start_time, True)
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False
    
    def _get_from_local_cache(self, cache_key: str) -> Optional[Any]:
        """Get from local LRU cache"""
        
        if cache_key not in self.local_cache:
            return None
        
        value, expiry_time = self.local_cache[cache_key]
        
        # Check TTL expiration
        if expiry_time > 0 and time.time() > expiry_time:
            self._evict_from_local_cache(cache_key)
            return None
        
        # Update LRU order
        if cache_key in self.cache_order:
            self.cache_order.remove(cache_key)
        self.cache_order.append(cache_key)
        
        return value
    
    def _add_to_local_cache(self, cache_key: str, value: Any, namespace: str, ttl: int = 0):
        """Add to local LRU cache with size management"""
        
        # Calculate expiry time
        expiry_time = time.time() + ttl if ttl > 0 else 0
        
        # Add/update cache entry
        self.local_cache[cache_key] = (value, expiry_time)
        
        # Update LRU order
        if cache_key in self.cache_order:
            self.cache_order.remove(cache_key)
        self.cache_order.append(cache_key)
        
        # Evict oldest entries if cache is full
        while len(self.local_cache) > self.local_cache_size:
            oldest_key = self.cache_order.pop(0)
            self._evict_from_local_cache(oldest_key)
    
    def _evict_from_local_cache(self, cache_key: str):
        """Evict entry from local cache"""
        if cache_key in self.local_cache:
            del self.local_cache[cache_key]
            self.metrics.cache_evictions += 1
    
    async def invalidate(self, namespace: str, key: Union[str, Dict] = None) -> bool:
        """Invalidate cache entries"""
        
        try:
            if key is None:
                # Invalidate entire namespace
                pattern = f"are_cache:{namespace}:*"
                
                # Clear from local cache
                keys_to_remove = [k for k in self.local_cache.keys() if k.startswith(f"are_cache:{namespace}:")]
                for k in keys_to_remove:
                    self._evict_from_local_cache(k)
                
                # Clear from Redis
                if self.redis_client:
                    try:
                        keys = await self.redis_client.keys(pattern)
                        if keys:
                            await self.redis_client.delete(*keys)
                    except Exception as e:
                        logger.warning(f"Redis invalidate failed: {str(e)}")
            else:
                # Invalidate specific key
                cache_key = self._generate_cache_key(namespace, key)
                
                # Remove from local cache
                self._evict_from_local_cache(cache_key)
                
                # Remove from Redis
                if self.redis_client:
                    try:
                        await self.redis_client.delete(cache_key)
                    except Exception as e:
                        logger.warning(f"Redis delete failed: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {str(e)}")
            return False
    
    async def warm_cache(self, namespace: str, 
                        data_loader_func, 
                        keys: List[Union[str, Dict]]) -> int:
        """Warm cache with preloaded data"""
        
        logger.info(f"Warming cache for namespace: {namespace}")
        warmed_count = 0
        
        for key in keys:
            try:
                # Check if already cached
                existing = await self.get(namespace, key)
                if existing is not None:
                    continue
                
                # Load data and cache
                data = await data_loader_func(key)
                if data is not None:
                    await self.set(namespace, key, data)
                    warmed_count += 1
                    
            except Exception as e:
                logger.warning(f"Cache warming failed for key {key}: {str(e)}")
        
        logger.info(f"Cache warming complete: {warmed_count} entries loaded")
        return warmed_count
    
    def _update_performance_metrics(self, start_time: float, hit: bool):
        """Update performance metrics"""
        
        response_time = (time.time() - start_time) * 1000
        
        # Update running average
        total_ops = self.metrics.cache_hits + self.metrics.cache_misses
        if total_ops > 0:
            self.metrics.average_response_time_ms = (
                (self.metrics.average_response_time_ms * (total_ops - 1) + response_time) / total_ops
            )
            self.metrics.hit_rate_percent = (self.metrics.cache_hits / total_ops) * 100
    
    async def _cache_maintenance_loop(self):
        """Background cache maintenance and metrics collection"""
        
        while True:
            try:
                # Clean expired entries from local cache
                current_time = time.time()
                expired_keys = []
                
                for cache_key, (value, expiry_time) in self.local_cache.items():
                    if expiry_time > 0 and current_time > expiry_time:
                        expired_keys.append(cache_key)
                
                for key in expired_keys:
                    self._evict_from_local_cache(key)
                
                # Update memory usage estimate
                try:
                    import sys
                    self.metrics.memory_usage_mb = sys.getsizeof(self.local_cache) / 1024 / 1024
                except:
                    pass
                
                # Record performance history
                if self.enable_metrics:
                    self.performance_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'metrics': asdict(self.metrics)
                    })
                    
                    # Keep last 1000 entries
                    if len(self.performance_history) > 1000:
                        self.performance_history = self.performance_history[-1000:]
                
                await asyncio.sleep(60)  # Run maintenance every minute
                
            except Exception as e:
                logger.error(f"Cache maintenance error: {str(e)}")
                await asyncio.sleep(300)  # Wait longer on error
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive cache performance report"""
        
        return {
            'cache_metrics': asdict(self.metrics),
            'configuration': {
                'local_cache_size': self.local_cache_size,
                'default_ttl_seconds': self.default_ttl_seconds,
                'redis_enabled': self.redis_client is not None,
                'strategies_configured': len(self.cache_strategies)
            },
            'current_state': {
                'local_cache_entries': len(self.local_cache),
                'cache_utilization_percent': (len(self.local_cache) / self.local_cache_size) * 100,
                'strategies_in_use': list(self.cache_strategies.keys())
            },
            'performance_optimization': {
                'average_response_time_ms': self.metrics.average_response_time_ms,
                'hit_rate_percent': self.metrics.hit_rate_percent,
                'efficiency_score': min(100, self.metrics.hit_rate_percent + 
                                      (100 - min(100, self.metrics.average_response_time_ms))),
                'optimization_recommendations': self._generate_optimization_recommendations()
            }
        }
    
    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate cache optimization recommendations"""
        
        recommendations = []
        
        if self.metrics.hit_rate_percent < 70:
            recommendations.append("Increase cache TTL values or cache size")
        
        if self.metrics.average_response_time_ms > 10:
            recommendations.append("Consider local cache preloading for hot data")
        
        if self.redis_client is None and REDIS_AVAILABLE:
            recommendations.append("Enable Redis for distributed caching")
        
        cache_util = (len(self.local_cache) / self.local_cache_size) * 100
        if cache_util > 90:
            recommendations.append("Increase local cache size")
        
        return recommendations
    
    async def close(self):
        """Close cache system and cleanup resources"""
        
        logger.info("Closing Advanced Caching System...")
        
        if self.redis_client:
            try:
                await self.redis_client.close()
            except:
                pass
        
        if self.redis_pool:
            try:
                await self.redis_pool.disconnect()
            except:
                pass
        
        self.local_cache.clear()
        self.cache_order.clear()
        
        logger.info("Advanced Caching System closed")

# Global cache system instance
advanced_cache_system = AdvancedCacheSystem()

# Convenience decorators for caching functions
def cached_function(namespace: str, ttl: int = 3600):
    """Decorator for caching function results"""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function signature
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            
            # Try to get from cache
            cached_result = await advanced_cache_system.get(namespace, key_data)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await advanced_cache_system.set(namespace, key_data, result, ttl)
            
            return result
        
        return wrapper
    return decorator