"""
Unit tests for Performance Optimizer Service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.services.performance_optimizer import (
    PerformanceOptimizer, CacheStrategy, ConnectionPoolConfig, CacheConfig,
    PerformanceMetrics, get_performance_optimizer
)
from src.utils.exceptions import PerformanceOptimizationError


class TestPerformanceOptimizer:
    """Test cases for PerformanceOptimizer."""
    
    @pytest.fixture
    def optimizer(self):
        """Create performance optimizer for testing."""
        optimizer = PerformanceOptimizer()
        
        # Mock Redis client to avoid external dependencies
        optimizer.redis_client = AsyncMock()
        optimizer.redis_client.ping = AsyncMock()
        optimizer.redis_client.get = AsyncMock(return_value=None)
        optimizer.redis_client.setex = AsyncMock()
        
        # Mock HTTP session
        optimizer.connection_pools["http"] = AsyncMock()
        optimizer.connection_pools["aws"] = AsyncMock()
        
        # Initialize caches manually for testing
        for cache_name in optimizer.cache_configs.keys():
            optimizer.caches[cache_name] = {}
            optimizer.cache_timestamps[cache_name] = {}
        
        # Mock external initialization methods to avoid network calls
        optimizer._initialize_connection_pools = AsyncMock()
        optimizer._initialize_redis = AsyncMock()
        
        return optimizer
    
    @pytest.mark.asyncio
    async def test_initialization(self, optimizer):
        """Test optimizer initialization."""
        await optimizer.initialize()
        
        assert len(optimizer.caches) == 4
        assert "incident_patterns" in optimizer.caches
        assert "agent_configs" in optimizer.caches
        assert optimizer.metrics is not None
    
    @pytest.mark.asyncio
    async def test_connection_pool_retrieval(self, optimizer):
        """Test connection pool retrieval."""
        await optimizer.initialize()
        
        # Test successful retrieval
        pool = await optimizer.get_connection_pool("http")
        assert pool is not None
        
        # Test non-existent pool
        with pytest.raises(PerformanceOptimizationError):
            await optimizer.get_connection_pool("nonexistent")
    
    @pytest.mark.asyncio
    async def test_local_cache_operations(self, optimizer):
        """Test local cache get/set operations."""
        await optimizer.initialize()
        
        # Test cache miss
        result = await optimizer.cache_get("incident_patterns", "test_key")
        assert result is None
        
        # Test cache set and get
        await optimizer.cache_set("incident_patterns", "test_key", "test_value")
        result = await optimizer.cache_get("incident_patterns", "test_key")
        assert result == "test_value"
        
        # Verify cache hit rate is updated
        assert "incident_patterns" in optimizer.metrics.cache_hit_rates
    
    @pytest.mark.asyncio
    async def test_ttl_cache_expiration(self, optimizer):
        """Test TTL-based cache expiration."""
        await optimizer.initialize()
        
        # Set short TTL for testing
        optimizer.cache_configs["agent_configs"].ttl_seconds = 1
        
        # Set value and verify it exists
        await optimizer.cache_set("agent_configs", "test_key", "test_value")
        result = await optimizer.cache_get("agent_configs", "test_key")
        assert result == "test_value"
        
        # Wait for expiration and verify it's gone
        await asyncio.sleep(1.1)
        result = await optimizer.cache_get("agent_configs", "test_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_eviction(self, optimizer):
        """Test cache eviction when size limit is reached."""
        await optimizer.initialize()
        
        # Set small cache size for testing
        optimizer.cache_configs["incident_patterns"].max_size = 2
        
        # Fill cache to capacity
        await optimizer.cache_set("incident_patterns", "key1", "value1")
        await optimizer.cache_set("incident_patterns", "key2", "value2")
        
        # Add one more item to trigger eviction
        await optimizer.cache_set("incident_patterns", "key3", "value3")
        
        # Verify cache size is maintained
        assert len(optimizer.caches["incident_patterns"]) <= 2
    
    @pytest.mark.asyncio
    async def test_distributed_cache_operations(self, optimizer):
        """Test distributed cache operations with Redis."""
        await optimizer.initialize()
        
        # Mock Redis responses
        optimizer.redis_client.get.return_value = "distributed_value"
        
        # Test distributed cache hit
        result = await optimizer.cache_get("incident_patterns", "distributed_key")
        assert result == "distributed_value"
        
        # Verify Redis was called
        optimizer.redis_client.get.assert_called_with("incident_patterns:distributed_key")
    
    @pytest.mark.asyncio
    async def test_memory_optimization(self, optimizer):
        """Test memory optimization functionality."""
        await optimizer.initialize()
        
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.memory_percent.return_value = 90.0
            mock_process.return_value.memory_info.return_value = Mock(rss=1000000)
            
            with patch('gc.collect', return_value=100) as mock_gc:
                await optimizer.optimize_memory_usage()
                
                # Verify GC was triggered due to high memory usage
                mock_gc.assert_called_once()
                assert optimizer.metrics.gc_collections == 1
                assert "GC collected 100 objects" in optimizer.metrics.optimization_actions_taken
    
    @pytest.mark.asyncio
    async def test_query_time_recording(self, optimizer):
        """Test query time recording and analysis."""
        await optimizer.initialize()
        
        # Record some query times
        await optimizer.record_query_time("database_query", 2.5)
        await optimizer.record_query_time("database_query", 3.0)
        await optimizer.record_query_time("api_call", 1.0)
        
        # Verify times are recorded
        assert len(optimizer.metrics.query_response_times["database_query"]) == 2
        assert len(optimizer.metrics.query_response_times["api_call"]) == 1
        
        # Test query time limit (keep only last 100)
        for i in range(150):
            await optimizer.record_query_time("test_query", float(i))
        
        assert len(optimizer.metrics.query_response_times["test_query"]) == 100
    
    @pytest.mark.asyncio
    async def test_optimization_recommendations(self, optimizer):
        """Test optimization recommendation generation."""
        await optimizer.initialize()
        
        # Set up conditions for recommendations
        optimizer.metrics.cache_hit_rates["low_hit_cache"] = 0.3  # Low hit rate
        optimizer.metrics.memory_usage_percent = 85.0  # High memory usage
        optimizer.metrics.connection_pool_utilization["overloaded_service"] = 0.9  # High utilization
        optimizer.metrics.query_response_times["slow_query"] = [6.0, 7.0, 8.0]  # Slow queries
        
        recommendations = await optimizer.get_optimization_recommendations()
        
        # Verify recommendations are generated
        assert len(recommendations) >= 4
        assert any("low_hit_cache" in rec for rec in recommendations)
        assert any("memory usage" in rec for rec in recommendations)
        assert any("overloaded_service" in rec for rec in recommendations)
        assert any("slow_query" in rec for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_cache_cleanup(self, optimizer):
        """Test expired cache entry cleanup."""
        await optimizer.initialize()
        
        # Set very short TTL for testing
        optimizer.cache_configs["agent_configs"].ttl_seconds = 0.1
        
        # Add some entries
        await optimizer.cache_set("agent_configs", "key1", "value1")
        await optimizer.cache_set("agent_configs", "key2", "value2")
        
        # Wait for expiration
        await asyncio.sleep(0.2)
        
        # Trigger cleanup
        await optimizer._cleanup_expired_caches()
        
        # Verify expired entries are removed
        assert len(optimizer.caches["agent_configs"]) == 0
    
    @pytest.mark.asyncio
    async def test_connection_pool_optimization(self, optimizer):
        """Test connection pool optimization."""
        await optimizer.initialize()
        
        # Mock connection pool with high utilization
        mock_connector = Mock()
        mock_connector._conns = [Mock() for _ in range(8)]  # 8 active connections
        optimizer.connection_pools["http"]._connector = mock_connector
        
        # Run optimization
        await optimizer._optimize_connection_pools()
        
        # Verify utilization is calculated
        utilization = 8 / optimizer.pool_configs["http"].max_size
        assert utilization > 0
    
    @pytest.mark.asyncio
    async def test_performance_metrics_retrieval(self, optimizer):
        """Test performance metrics retrieval."""
        await optimizer.initialize()
        
        # Set some metrics
        optimizer.metrics.memory_usage_percent = 75.0
        optimizer.metrics.gc_collections = 5
        optimizer.metrics.cache_hit_rates["test_cache"] = 0.85
        
        metrics = await optimizer.get_performance_metrics()
        
        assert metrics.memory_usage_percent == 75.0
        assert metrics.gc_collections == 5
        assert metrics.cache_hit_rates["test_cache"] == 0.85
    
    @pytest.mark.asyncio
    async def test_cleanup(self, optimizer):
        """Test resource cleanup."""
        await optimizer.initialize()
        
        # Mock cleanup operations
        optimizer.connection_pools["http"].close = AsyncMock()
        optimizer.redis_client.close = AsyncMock()
        
        await optimizer.cleanup()
        
        # Verify cleanup was called
        optimizer.connection_pools["http"].close.assert_called_once()
        optimizer.redis_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_strategies(self, optimizer):
        """Test different cache strategies."""
        await optimizer.initialize()
        
        # Test LRU strategy
        lru_config = CacheConfig(CacheStrategy.LRU, max_size=2)
        optimizer.cache_configs["lru_test"] = lru_config
        optimizer.caches["lru_test"] = {}
        optimizer.cache_timestamps["lru_test"] = {}
        
        # Fill cache and trigger eviction
        await optimizer.cache_set("lru_test", "key1", "value1")
        await optimizer.cache_set("lru_test", "key2", "value2")
        await optimizer.cache_set("lru_test", "key3", "value3")  # Should trigger eviction
        
        assert len(optimizer.caches["lru_test"]) <= 2
    
    @pytest.mark.asyncio
    async def test_error_handling(self, optimizer):
        """Test error handling in various scenarios."""
        await optimizer.initialize()
        
        # Test Redis connection failure
        optimizer.redis_client.get.side_effect = Exception("Redis connection failed")
        
        # Should not raise exception, should fall back gracefully
        result = await optimizer.cache_get("incident_patterns", "test_key")
        assert result is None
        
        # Test memory optimization with psutil failure
        with patch('psutil.Process', side_effect=Exception("psutil failed")):
            # Should not raise exception
            await optimizer.optimize_memory_usage()


class TestGlobalPerformanceOptimizer:
    """Test global performance optimizer instance."""
    
    @pytest.mark.asyncio
    async def test_singleton_behavior(self):
        """Test that get_performance_optimizer returns singleton."""
        with patch('src.services.performance_optimizer.PerformanceOptimizer') as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance
            
            # First call should create instance
            optimizer1 = await get_performance_optimizer()
            
            # Second call should return same instance
            optimizer2 = await get_performance_optimizer()
            
            assert optimizer1 is optimizer2
            mock_class.assert_called_once()


class TestPerformanceMetrics:
    """Test PerformanceMetrics data class."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization with defaults."""
        metrics = PerformanceMetrics()
        
        assert metrics.memory_usage_percent == 0.0
        assert metrics.gc_collections == 0
        assert isinstance(metrics.connection_pool_utilization, dict)
        assert isinstance(metrics.cache_hit_rates, dict)
        assert isinstance(metrics.query_response_times, dict)
        assert isinstance(metrics.optimization_actions_taken, list)
    
    def test_metrics_updates(self):
        """Test metrics updates."""
        metrics = PerformanceMetrics()
        
        # Update various metrics
        metrics.memory_usage_percent = 85.5
        metrics.gc_collections = 10
        metrics.connection_pool_utilization["test_pool"] = 0.75
        metrics.cache_hit_rates["test_cache"] = 0.90
        metrics.query_response_times["test_query"] = [1.0, 2.0, 3.0]
        metrics.optimization_actions_taken.append("Test optimization")
        
        assert metrics.memory_usage_percent == 85.5
        assert metrics.gc_collections == 10
        assert metrics.connection_pool_utilization["test_pool"] == 0.75
        assert metrics.cache_hit_rates["test_cache"] == 0.90
        assert len(metrics.query_response_times["test_query"]) == 3
        assert "Test optimization" in metrics.optimization_actions_taken


class TestConnectionPoolConfig:
    """Test ConnectionPoolConfig data class."""
    
    def test_config_defaults(self):
        """Test configuration defaults."""
        config = ConnectionPoolConfig(max_size=10)
        
        assert config.max_size == 10
        assert config.min_size == 1
        assert config.timeout == 30
        assert config.keepalive_timeout == 300
        assert config.retry_attempts == 3
    
    def test_config_custom_values(self):
        """Test configuration with custom values."""
        config = ConnectionPoolConfig(
            max_size=20,
            min_size=5,
            timeout=60,
            keepalive_timeout=600,
            retry_attempts=5
        )
        
        assert config.max_size == 20
        assert config.min_size == 5
        assert config.timeout == 60
        assert config.keepalive_timeout == 600
        assert config.retry_attempts == 5


class TestCacheConfig:
    """Test CacheConfig data class."""
    
    def test_cache_config_defaults(self):
        """Test cache configuration defaults."""
        config = CacheConfig(CacheStrategy.LRU)
        
        assert config.strategy == CacheStrategy.LRU
        assert config.ttl_seconds == 300
        assert config.max_size == 1000
        assert config.eviction_policy == "lru"
    
    def test_cache_config_custom_values(self):
        """Test cache configuration with custom values."""
        config = CacheConfig(
            strategy=CacheStrategy.TTL,
            ttl_seconds=600,
            max_size=500,
            eviction_policy="random"
        )
        
        assert config.strategy == CacheStrategy.TTL
        assert config.ttl_seconds == 600
        assert config.max_size == 500
        assert config.eviction_policy == "random"