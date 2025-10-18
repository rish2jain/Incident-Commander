"""
Performance Optimizer Service

Implements enterprise-scale performance optimizations including:
- Connection pooling for external service integrations
- Intelligent caching strategies for frequently accessed data
- Database query optimization and indexing strategies
- Memory usage optimization and garbage collection tuning

Requirements: 10.3, 15.4
"""

import asyncio
import gc
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

import redis.asyncio as aioredis
import aioboto3
from aiohttp import ClientSession, TCPConnector, ClientTimeout

from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.constants import RATE_LIMITS, RESOURCE_LIMITS, PERFORMANCE_TARGETS
from src.utils.exceptions import PerformanceOptimizationError


logger = get_logger(__name__)


class CacheStrategy(Enum):
    """Cache strategy types."""
    LRU = "lru"
    TTL = "ttl"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pools."""
    max_size: int
    min_size: int = 1
    timeout: int = 30
    keepalive_timeout: int = 300
    retry_attempts: int = 3


@dataclass
class CacheConfig:
    """Configuration for caching strategies."""
    strategy: CacheStrategy
    ttl_seconds: int = 300
    max_size: int = 1000
    eviction_policy: str = "lru"


@dataclass
class PerformanceMetrics:
    """Performance optimization metrics."""
    connection_pool_utilization: Dict[str, float] = field(default_factory=dict)
    cache_hit_rates: Dict[str, float] = field(default_factory=dict)
    memory_usage_percent: float = 0.0
    gc_collections: int = 0
    query_response_times: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    optimization_actions_taken: List[str] = field(default_factory=list)


class PerformanceOptimizer:
    """
    Enterprise-scale performance optimizer with connection pooling,
    intelligent caching, and memory optimization.
    """
    
    def __init__(self):
        self.logger = logger
        
        # Connection pools for external services
        self.connection_pools: Dict[str, Any] = {}
        self.pool_configs = {
            "aws": ConnectionPoolConfig(max_size=50, min_size=5, timeout=30),
            "datadog": ConnectionPoolConfig(max_size=20, min_size=2, timeout=15),
            "pagerduty": ConnectionPoolConfig(max_size=10, min_size=1, timeout=20),
            "slack": ConnectionPoolConfig(max_size=5, min_size=1, timeout=10),
            "http": ConnectionPoolConfig(max_size=100, min_size=10, timeout=30)
        }
        
        # Cache configurations
        self.cache_configs = {
            "incident_patterns": CacheConfig(CacheStrategy.LRU, ttl_seconds=1800, max_size=500),
            "agent_configs": CacheConfig(CacheStrategy.TTL, ttl_seconds=300, max_size=100),
            "business_rules": CacheConfig(CacheStrategy.WRITE_THROUGH, ttl_seconds=3600, max_size=200),
            "query_results": CacheConfig(CacheStrategy.LRU, ttl_seconds=600, max_size=1000)
        }
        
        # Cache storage
        self.caches: Dict[str, Dict[str, Any]] = {}
        self.cache_timestamps: Dict[str, Dict[str, datetime]] = {}
        
        # Performance metrics
        self.metrics = PerformanceMetrics()
        self.last_gc_time = time.time()
        self.last_optimization_time = time.time()
        
        # Redis client for distributed caching
        self.redis_client: Optional[aioredis.Redis] = None
        
        # Memory monitoring
        self.memory_threshold = RESOURCE_LIMITS["memory_threshold"]
        self.gc_threshold = 0.85  # Trigger GC at 85% memory usage
        
    async def initialize(self) -> None:
        """Initialize performance optimizer with connection pools and caches."""
        try:
            # Initialize connection pools
            await self._initialize_connection_pools()
            
            # Initialize caches
            await self._initialize_caches()
            
            # Initialize Redis for distributed caching
            await self._initialize_redis()
            
            # Start background optimization tasks
            asyncio.create_task(self._optimization_loop())
            
            self.logger.info("Performance optimizer initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize performance optimizer: {e}")
            raise PerformanceOptimizationError(f"Initialization failed: {e}")
    
    async def _initialize_connection_pools(self) -> None:
        """Initialize connection pools for external services."""
        # HTTP connection pool
        connector = TCPConnector(
            limit=self.pool_configs["http"].max_size,
            limit_per_host=20,
            keepalive_timeout=self.pool_configs["http"].keepalive_timeout,
            enable_cleanup_closed=True
        )
        
        timeout = ClientTimeout(total=self.pool_configs["http"].timeout)
        self.connection_pools["http"] = ClientSession(
            connector=connector,
            timeout=timeout
        )
        
        # AWS connection pool (using aioboto3 session)
        self.connection_pools["aws"] = aioboto3.Session()
        
        self.logger.info("Connection pools initialized")
    
    async def _initialize_caches(self) -> None:
        """Initialize local caches with configured strategies."""
        for cache_name, config in self.cache_configs.items():
            self.caches[cache_name] = {}
            self.cache_timestamps[cache_name] = {}
        
        self.logger.info(f"Initialized {len(self.cache_configs)} local caches")
    
    async def _initialize_redis(self) -> None:
        """Initialize Redis client for distributed caching."""
        try:
            redis_url = config.get_redis_url()
            self.redis_client = await aioredis.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20
            )
            
            # Test connection
            await self.redis_client.ping()
            self.logger.info("Redis client initialized for distributed caching")
            
        except Exception as e:
            self.logger.warning(f"Redis initialization failed, using local cache only: {e}")
            self.redis_client = None
    
    async def get_connection_pool(self, service_name: str) -> Any:
        """Get connection pool for specified service."""
        if service_name not in self.connection_pools:
            raise PerformanceOptimizationError(f"No connection pool for service: {service_name}")
        
        pool = self.connection_pools[service_name]
        
        # Update utilization metrics
        if hasattr(pool, '_connector') and hasattr(pool._connector, '_conns'):
            total_connections = len(pool._connector._conns)
            max_connections = self.pool_configs.get(service_name, {}).max_size or 10
            utilization = total_connections / max_connections
            self.metrics.connection_pool_utilization[service_name] = utilization
        
        return pool
    
    async def cache_get(self, cache_name: str, key: str) -> Optional[Any]:
        """Get value from cache with intelligent strategy handling."""
        if cache_name not in self.caches:
            return None
        
        # Check local cache first
        local_value = await self._get_from_local_cache(cache_name, key)
        if local_value is not None:
            self._update_cache_hit_rate(cache_name, True)
            return local_value
        
        # Check distributed cache if available
        if self.redis_client:
            distributed_value = await self._get_from_distributed_cache(cache_name, key)
            if distributed_value is not None:
                # Store in local cache for faster access
                await self._set_in_local_cache(cache_name, key, distributed_value)
                self._update_cache_hit_rate(cache_name, True)
                return distributed_value
        
        self._update_cache_hit_rate(cache_name, False)
        return None
    
    async def cache_set(self, cache_name: str, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with strategy-specific handling."""
        if cache_name not in self.caches:
            return
        
        config = self.cache_configs[cache_name]
        effective_ttl = ttl or config.ttl_seconds
        
        # Set in local cache
        await self._set_in_local_cache(cache_name, key, value, effective_ttl)
        
        # Set in distributed cache based on strategy
        if self.redis_client and config.strategy in [CacheStrategy.WRITE_THROUGH, CacheStrategy.WRITE_BEHIND]:
            await self._set_in_distributed_cache(cache_name, key, value, effective_ttl)
    
    async def _get_from_local_cache(self, cache_name: str, key: str) -> Optional[Any]:
        """Get value from local cache with TTL checking."""
        if key not in self.caches[cache_name]:
            return None
        
        config = self.cache_configs[cache_name]
        
        # Check TTL for TTL-based strategies
        if config.strategy == CacheStrategy.TTL:
            timestamp = self.cache_timestamps[cache_name].get(key)
            if timestamp and datetime.utcnow() - timestamp > timedelta(seconds=config.ttl_seconds):
                # Expired, remove from cache
                del self.caches[cache_name][key]
                del self.cache_timestamps[cache_name][key]
                return None
        
        return self.caches[cache_name][key]
    
    async def _set_in_local_cache(self, cache_name: str, key: str, value: Any, ttl: int = None) -> None:
        """Set value in local cache with eviction policy."""
        config = self.cache_configs[cache_name]
        
        # Check cache size and evict if necessary
        if len(self.caches[cache_name]) >= config.max_size:
            await self._evict_from_local_cache(cache_name)
        
        self.caches[cache_name][key] = value
        self.cache_timestamps[cache_name][key] = datetime.utcnow()
    
    async def _evict_from_local_cache(self, cache_name: str) -> None:
        """Evict items from local cache based on eviction policy."""
        config = self.cache_configs[cache_name]
        cache = self.caches[cache_name]
        timestamps = self.cache_timestamps[cache_name]
        
        if config.eviction_policy == "lru":
            # Remove oldest accessed item
            oldest_key = min(timestamps.keys(), key=lambda k: timestamps[k])
            del cache[oldest_key]
            del timestamps[oldest_key]
        elif config.eviction_policy == "random":
            # Remove random item
            import random
            key_to_remove = random.choice(list(cache.keys()))
            del cache[key_to_remove]
            del timestamps[key_to_remove]
    
    async def _get_from_distributed_cache(self, cache_name: str, key: str) -> Optional[Any]:
        """Get value from distributed Redis cache."""
        if not self.redis_client:
            return None
        
        try:
            redis_key = f"{cache_name}:{key}"
            value = await self.redis_client.get(redis_key)
            return value
        except Exception as e:
            self.logger.warning(f"Failed to get from distributed cache: {e}")
            return None
    
    async def _set_in_distributed_cache(self, cache_name: str, key: str, value: Any, ttl: int) -> None:
        """Set value in distributed Redis cache."""
        if not self.redis_client:
            return
        
        try:
            redis_key = f"{cache_name}:{key}"
            await self.redis_client.setex(redis_key, ttl, str(value))
        except Exception as e:
            self.logger.warning(f"Failed to set in distributed cache: {e}")
    
    def _update_cache_hit_rate(self, cache_name: str, hit: bool) -> None:
        """Update cache hit rate metrics."""
        if cache_name not in self.metrics.cache_hit_rates:
            self.metrics.cache_hit_rates[cache_name] = 0.0
        
        # Simple moving average for hit rate
        current_rate = self.metrics.cache_hit_rates[cache_name]
        new_rate = current_rate * 0.9 + (1.0 if hit else 0.0) * 0.1
        self.metrics.cache_hit_rates[cache_name] = new_rate
    
    async def optimize_memory_usage(self) -> None:
        """Optimize memory usage with garbage collection and cleanup."""
        try:
            # Get current memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            self.metrics.memory_usage_percent = memory_percent
            
            # Trigger garbage collection if memory usage is high
            if memory_percent > self.gc_threshold * 100:
                collected = gc.collect()
                self.metrics.gc_collections += 1
                self.metrics.optimization_actions_taken.append(f"GC collected {collected} objects")
                self.logger.info(f"Garbage collection freed {collected} objects, memory: {memory_percent:.1f}%")
            
            # Clean expired cache entries
            await self._cleanup_expired_caches()
            
            # Optimize connection pools
            await self._optimize_connection_pools()
            
        except Exception as e:
            self.logger.error(f"Memory optimization failed: {e}")
    
    async def _cleanup_expired_caches(self) -> None:
        """Clean up expired cache entries."""
        cleaned_count = 0
        
        for cache_name, config in self.cache_configs.items():
            if config.strategy == CacheStrategy.TTL:
                cache = self.caches[cache_name]
                timestamps = self.cache_timestamps[cache_name]
                current_time = datetime.utcnow()
                
                expired_keys = [
                    key for key, timestamp in timestamps.items()
                    if current_time - timestamp > timedelta(seconds=config.ttl_seconds)
                ]
                
                for key in expired_keys:
                    del cache[key]
                    del timestamps[key]
                    cleaned_count += 1
        
        if cleaned_count > 0:
            self.metrics.optimization_actions_taken.append(f"Cleaned {cleaned_count} expired cache entries")
    
    async def _optimize_connection_pools(self) -> None:
        """Optimize connection pool sizes based on usage patterns."""
        for service_name, pool in self.connection_pools.items():
            if service_name == "http" and hasattr(pool, '_connector'):
                connector = pool._connector
                if hasattr(connector, '_conns'):
                    active_connections = len(connector._conns)
                    config = self.pool_configs[service_name]
                    
                    # Log connection pool status
                    utilization = active_connections / config.max_size
                    self.logger.debug(f"{service_name} pool: {active_connections}/{config.max_size} ({utilization:.1%})")
    
    async def record_query_time(self, query_type: str, duration: float) -> None:
        """Record query execution time for optimization analysis."""
        self.metrics.query_response_times[query_type].append(duration)
        
        # Keep only recent measurements (last 100)
        if len(self.metrics.query_response_times[query_type]) > 100:
            self.metrics.query_response_times[query_type] = self.metrics.query_response_times[query_type][-100:]
    
    async def get_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on metrics."""
        recommendations = []
        
        # Analyze cache hit rates
        for cache_name, hit_rate in self.metrics.cache_hit_rates.items():
            if hit_rate < 0.5:  # Less than 50% hit rate
                recommendations.append(f"Consider increasing cache size or TTL for {cache_name} (hit rate: {hit_rate:.1%})")
        
        # Analyze memory usage
        if self.metrics.memory_usage_percent > 80:
            recommendations.append("High memory usage detected, consider scaling up or optimizing memory-intensive operations")
        
        # Analyze connection pool utilization
        for service, utilization in self.metrics.connection_pool_utilization.items():
            if utilization > 0.8:
                recommendations.append(f"High connection pool utilization for {service} ({utilization:.1%}), consider increasing pool size")
        
        # Analyze query response times
        for query_type, times in self.metrics.query_response_times.items():
            if times:
                avg_time = sum(times) / len(times)
                if avg_time > 5.0:  # More than 5 seconds average
                    recommendations.append(f"Slow query performance for {query_type} (avg: {avg_time:.2f}s), consider optimization")
        
        return recommendations
    
    async def _optimization_loop(self) -> None:
        """Background optimization loop."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Perform memory optimization
                await self.optimize_memory_usage()
                
                # Generate and log recommendations every 10 minutes
                if time.time() - self.last_optimization_time > 600:
                    recommendations = await self.get_optimization_recommendations()
                    if recommendations:
                        self.logger.info(f"Performance optimization recommendations: {recommendations}")
                    self.last_optimization_time = time.time()
                
            except Exception as e:
                self.logger.error(f"Optimization loop error: {e}")
    
    async def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        return self.metrics
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        try:
            # Close HTTP connection pool
            if "http" in self.connection_pools:
                await self.connection_pools["http"].close()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            self.logger.info("Performance optimizer cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


# Global performance optimizer instance
_performance_optimizer: Optional[PerformanceOptimizer] = None


async def get_performance_optimizer() -> PerformanceOptimizer:
    """Get global performance optimizer instance."""
    global _performance_optimizer
    
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
        await _performance_optimizer.initialize()
    
    return _performance_optimizer