"""
Integration tests for Performance Optimization Services.

Tests the complete performance optimization system including:
- PerformanceOptimizer (connection pooling, caching, memory optimization)
- ScalingManager (auto-scaling, load balancing)
- CostOptimizer (cost-aware scaling, model selection)
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.services.performance_optimizer import get_performance_optimizer
from src.services.scaling_manager import get_scaling_manager
from src.services.cost_optimizer import get_cost_optimizer, CostThreshold
from src.utils.exceptions import PerformanceOptimizationError, ScalingError, CostOptimizationError


class TestPerformanceOptimizationIntegration:
    """Integration tests for complete performance optimization system."""
    
    @pytest.fixture
    async def performance_system(self):
        """Set up complete performance optimization system."""
        # Mock external dependencies
        with patch('aioredis.from_url') as mock_redis, \
             patch('aioboto3.Session') as mock_boto3, \
             patch('psutil.Process') as mock_process:
            
            # Configure mocks
            mock_redis.return_value = AsyncMock()
            mock_boto3.return_value = AsyncMock()
            mock_process.return_value.memory_percent.return_value = 50.0
            
            # Initialize services
            perf_optimizer = await get_performance_optimizer()
            scaling_manager = await get_scaling_manager()
            cost_optimizer = await get_cost_optimizer()
            
            return {
                "performance": perf_optimizer,
                "scaling": scaling_manager,
                "cost": cost_optimizer
            }
    
    @pytest.mark.asyncio
    async def test_end_to_end_incident_processing(self, performance_system):
        """Test end-to-end incident processing with performance optimization."""
        perf_optimizer = performance_system["performance"]
        scaling_manager = performance_system["scaling"]
        cost_optimizer = performance_system["cost"]
        
        # Simulate high-severity incident requiring optimal performance
        incident_data = {
            "incident_id": "critical-incident-001",
            "severity": "critical",
            "region": "us-east-1",
            "estimated_complexity": "high"
        }
        
        # 1. Cost optimizer selects optimal model for critical incident
        optimal_model = await cost_optimizer.select_optimal_model(
            task_type="diagnosis",
            incident_severity="critical",
            required_accuracy=0.95
        )
        
        # Should select high-accuracy model for critical incident
        model_config = cost_optimizer.model_configs[optimal_model]
        assert model_config.accuracy_score >= 0.95
        
        # 2. Scaling manager selects best replica for processing
        replica = await scaling_manager.select_agent_replica("diagnosis", incident_data)
        assert replica is not None
        
        # 3. Assign incident to replica
        await scaling_manager.assign_incident_to_replica(replica, incident_data["incident_id"])
        assert replica.current_load > 0
        
        # 4. Performance optimizer provides cached data if available
        cache_key = f"incident_pattern_{incident_data['severity']}"
        cached_pattern = await perf_optimizer.cache_get("incident_patterns", cache_key)
        
        # If not cached, simulate storing pattern for future use
        if cached_pattern is None:
            pattern_data = {"common_causes": ["database_overload", "memory_leak"]}
            await perf_optimizer.cache_set("incident_patterns", cache_key, pattern_data)
        
        # 5. Simulate incident processing completion
        await scaling_manager.release_incident_from_replica(replica, incident_data["incident_id"])
        assert replica.current_load == 0
        
        # 6. Verify metrics are updated
        perf_metrics = await perf_optimizer.get_performance_metrics()
        scaling_metrics = await scaling_manager.get_scaling_metrics()
        cost_metrics = await cost_optimizer.get_cost_metrics()
        
        assert perf_metrics is not None
        assert scaling_metrics is not None
        assert cost_metrics is not None
    
    @pytest.mark.asyncio
    async def test_auto_scaling_with_cost_optimization(self, performance_system):
        """Test auto-scaling decisions with cost optimization."""
        scaling_manager = performance_system["scaling"]
        cost_optimizer = performance_system["cost"]
        
        # Simulate high load scenario
        current_load = {
            "detection": 0.85,  # High utilization - needs scaling
            "diagnosis": 0.25,  # Low utilization - can scale down
            "prediction": 0.60  # Normal utilization
        }
        
        # Get cost-aware scaling recommendations
        recommendations = await cost_optimizer.optimize_scaling_costs(current_load)
        
        # Should recommend scale up for high utilization
        scale_up_recs = recommendations["scale_up"]
        assert len(scale_up_recs) > 0
        assert any(r["agent_type"] == "detection" for r in scale_up_recs)
        
        # Should recommend scale down for low utilization
        scale_down_recs = recommendations["scale_down"]
        assert len(scale_down_recs) > 0
        assert any(r["agent_type"] == "diagnosis" for r in scale_down_recs)
        
        # Apply scaling recommendations
        for rec in scale_up_recs:
            if rec["agent_type"] == "detection":
                initial_count = len(scaling_manager.agent_replicas["detection"])
                success = await scaling_manager._scale_up_agent("detection")
                if success:
                    assert len(scaling_manager.agent_replicas["detection"]) > initial_count
    
    @pytest.mark.asyncio
    async def test_performance_optimization_under_load(self, performance_system):
        """Test performance optimization under high load conditions."""
        perf_optimizer = performance_system["performance"]
        scaling_manager = performance_system["scaling"]
        
        # Simulate multiple concurrent incidents
        incidents = [
            {"id": f"incident-{i}", "severity": "high", "region": "us-east-1"}
            for i in range(10)
        ]
        
        # Process incidents concurrently
        tasks = []
        for incident in incidents:
            # Select replica for each incident
            replica = await scaling_manager.select_agent_replica("detection", incident)
            if replica:
                await scaling_manager.assign_incident_to_replica(replica, incident["id"])
                
                # Cache incident data
                cache_key = f"incident_{incident['id']}"
                await perf_optimizer.cache_set("incident_patterns", cache_key, incident)
                
                # Record processing time
                await perf_optimizer.record_query_time("incident_processing", 2.5)
        
        # Verify system handles load appropriately
        scaling_metrics = await scaling_manager.get_scaling_metrics()
        perf_metrics = await perf_optimizer.get_performance_metrics()
        
        # Should have recorded multiple incidents
        assert len(scaling_manager.incident_history) >= len(incidents)
        
        # Should have cache hits for repeated patterns
        assert len(perf_optimizer.caches["incident_patterns"]) > 0
        
        # Should have recorded query times
        assert len(perf_metrics.query_response_times["incident_processing"]) > 0
    
    @pytest.mark.asyncio
    async def test_cost_threshold_breach_response(self, performance_system):
        """Test system response to cost threshold breaches."""
        cost_optimizer = performance_system["cost"]
        scaling_manager = performance_system["scaling"]
        
        # Simulate high cost scenario
        cost_optimizer.metrics.current_hourly_cost = 250.0  # Above critical threshold
        
        # Check cost thresholds
        await cost_optimizer._check_cost_thresholds(250.0)
        
        # Should trigger cost optimization
        assert cost_optimizer.current_cost_threshold == CostThreshold.CRITICAL
        
        # Should generate cost optimization recommendations
        recommendations = await cost_optimizer.get_cost_recommendations()
        assert len(recommendations) > 0
        
        # For emergency cost scenario
        await cost_optimizer._check_cost_thresholds(1200.0)  # Emergency level
        
        # Should disable optimization and record emergency action
        assert not cost_optimizer.optimization_enabled
        assert any("Emergency" in action for action in cost_optimizer.metrics.optimization_actions)
    
    @pytest.mark.asyncio
    async def test_lambda_warming_integration(self, performance_system):
        """Test Lambda warming integration with business hours."""
        cost_optimizer = performance_system["cost"]
        
        # Mock Lambda warming
        cost_optimizer._invoke_lambda_warming = AsyncMock()
        
        # Test predictive warming during business hours
        with patch('datetime.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.hour = 9  # Business start
            mock_now.weekday.return_value = 1  # Tuesday
            mock_datetime.now.return_value = mock_now
            
            with patch('pytz.timezone'):
                await cost_optimizer.predictive_lambda_warming("us-east-1")
                
                # Should warm functions during business hours
                assert cost_optimizer.metrics.lambda_warm_cost > 0
    
    @pytest.mark.asyncio
    async def test_cache_performance_optimization(self, performance_system):
        """Test cache performance optimization across services."""
        perf_optimizer = performance_system["performance"]
        cost_optimizer = performance_system["cost"]
        
        # Test cache hit rate optimization
        cache_name = "incident_patterns"
        
        # Generate cache misses
        for i in range(10):
            result = await perf_optimizer.cache_get(cache_name, f"miss_key_{i}")
            assert result is None
        
        # Generate cache hits
        await perf_optimizer.cache_set(cache_name, "hit_key", "cached_value")
        for i in range(5):
            result = await perf_optimizer.cache_get(cache_name, "hit_key")
            assert result == "cached_value"
        
        # Check cache hit rate
        hit_rate = perf_optimizer.metrics.cache_hit_rates.get(cache_name, 0)
        assert 0 < hit_rate < 1  # Should be between 0 and 1
        
        # Get optimization recommendations
        recommendations = await perf_optimizer.get_optimization_recommendations()
        
        # Should include cache optimization recommendations if hit rate is low
        cache_recs = [r for r in recommendations if cache_name in r]
        if hit_rate < 0.5:
            assert len(cache_recs) > 0
    
    @pytest.mark.asyncio
    async def test_geographic_distribution_optimization(self, performance_system):
        """Test geographic distribution and optimization."""
        scaling_manager = performance_system["scaling"]
        cost_optimizer = performance_system["cost"]
        
        # Create incidents from different regions
        incidents = [
            {"id": "us-east-incident", "region": "us-east-1", "severity": "high"},
            {"id": "us-west-incident", "region": "us-west-2", "severity": "medium"},
            {"id": "eu-incident", "region": "eu-west-1", "severity": "low"}
        ]
        
        # Process incidents with geographic optimization
        for incident in incidents:
            # Select replica based on geography
            replica = await scaling_manager.select_agent_replica("detection", incident)
            
            if replica:
                # Should prefer replicas in same region when available
                await scaling_manager.assign_incident_to_replica(replica, incident["id"])
                
                # Select cost-optimized model based on severity and region
                model = await cost_optimizer.select_optimal_model(
                    task_type="detection",
                    incident_severity=incident["severity"]
                )
                
                # Verify model selection is appropriate for severity
                model_config = cost_optimizer.model_configs[model]
                if incident["severity"] == "high":
                    assert model_config.accuracy_score >= 0.85
                
                await scaling_manager.release_incident_from_replica(replica, incident["id"])
        
        # Verify geographic distribution
        replica_status = await scaling_manager.get_replica_status()
        regions_used = set()
        for agent_type, replicas in replica_status.items():
            for replica in replicas:
                regions_used.add(replica["region"])
        
        # Should have replicas in multiple regions
        assert len(regions_used) > 1
    
    @pytest.mark.asyncio
    async def test_memory_optimization_integration(self, performance_system):
        """Test memory optimization integration."""
        perf_optimizer = performance_system["performance"]
        
        # Simulate high memory usage
        with patch('psutil.Process') as mock_process:
            mock_process.return_value.memory_percent.return_value = 90.0
            mock_process.return_value.memory_info.return_value = Mock(rss=2000000)
            
            with patch('gc.collect', return_value=150) as mock_gc:
                # Trigger memory optimization
                await perf_optimizer.optimize_memory_usage()
                
                # Should trigger garbage collection
                mock_gc.assert_called_once()
                assert perf_optimizer.metrics.gc_collections > 0
                
                # Should record optimization action
                assert any("GC collected" in action for action in perf_optimizer.metrics.optimization_actions_taken)
    
    @pytest.mark.asyncio
    async def test_performance_metrics_correlation(self, performance_system):
        """Test correlation between different performance metrics."""
        perf_optimizer = performance_system["performance"]
        scaling_manager = performance_system["scaling"]
        cost_optimizer = performance_system["cost"]
        
        # Generate some activity
        await scaling_manager.record_incident("test-incident")
        await perf_optimizer.record_query_time("test_query", 3.5)
        await cost_optimizer._record_model_selection("claude-3-haiku", "medium", "detection")
        
        # Get all metrics
        perf_metrics = await perf_optimizer.get_performance_metrics()
        scaling_metrics = await scaling_manager.get_scaling_metrics()
        cost_metrics = await cost_optimizer.get_cost_metrics()
        
        # Verify metrics are correlated
        assert len(scaling_manager.incident_history) > 0
        assert len(perf_metrics.query_response_times["test_query"]) > 0
        assert cost_metrics.cost_by_service.get("detection", 0) > 0
        
        # Verify metrics provide actionable insights
        perf_recommendations = await perf_optimizer.get_optimization_recommendations()
        cost_recommendations = await cost_optimizer.get_cost_recommendations()
        
        assert isinstance(perf_recommendations, list)
        assert isinstance(cost_recommendations, list)
    
    @pytest.mark.asyncio
    async def test_error_handling_and_resilience(self, performance_system):
        """Test error handling and system resilience."""
        perf_optimizer = performance_system["performance"]
        scaling_manager = performance_system["scaling"]
        cost_optimizer = performance_system["cost"]
        
        # Test performance optimizer resilience
        with patch.object(perf_optimizer, 'redis_client') as mock_redis:
            mock_redis.get.side_effect = Exception("Redis connection failed")
            
            # Should handle Redis failure gracefully
            result = await perf_optimizer.cache_get("incident_patterns", "test_key")
            assert result is None  # Should return None, not raise exception
        
        # Test scaling manager resilience
        with patch.object(scaling_manager, '_create_agent_replica', side_effect=Exception("Scaling failed")):
            # Should handle scaling failure gracefully
            success = await scaling_manager._scale_up_agent("detection")
            assert not success  # Should return False, not raise exception
        
        # Test cost optimizer resilience
        with patch.object(cost_optimizer, '_invoke_lambda_warming', side_effect=Exception("Lambda failed")):
            # Should handle Lambda warming failure gracefully
            results = await cost_optimizer.warm_lambda_functions(["detection-agent"])
            assert not results["detection-agent"]  # Should return False, not raise exception
    
    @pytest.mark.asyncio
    async def test_cleanup_and_resource_management(self, performance_system):
        """Test proper cleanup and resource management."""
        perf_optimizer = performance_system["performance"]
        scaling_manager = performance_system["scaling"]
        cost_optimizer = performance_system["cost"]
        
        # Mock cleanup operations
        perf_optimizer.connection_pools["http"] = AsyncMock()
        perf_optimizer.redis_client = AsyncMock()
        
        # Perform cleanup
        await perf_optimizer.cleanup()
        await scaling_manager.cleanup()
        await cost_optimizer.cleanup()
        
        # Verify cleanup was called
        perf_optimizer.connection_pools["http"].close.assert_called_once()
        perf_optimizer.redis_client.close.assert_called_once()


class TestPerformanceOptimizationScenarios:
    """Test specific performance optimization scenarios."""
    
    @pytest.mark.asyncio
    async def test_black_friday_scenario(self):
        """Test performance optimization during high-traffic events."""
        with patch('aioredis.from_url') as mock_redis, \
             patch('aioboto3.Session') as mock_boto3:
            
            mock_redis.return_value = AsyncMock()
            mock_boto3.return_value = AsyncMock()
            
            # Initialize services
            scaling_manager = await get_scaling_manager()
            cost_optimizer = await get_cost_optimizer()
            
            # Simulate Black Friday traffic spike
            for i in range(50):  # High incident volume
                await scaling_manager.record_incident(f"black-friday-incident-{i}")
            
            # Should trigger auto-scaling
            metrics = await scaling_manager.get_scaling_metrics()
            assert metrics.total_incidents_per_minute > 0
            
            # Should optimize costs during high volume
            recommendations = await cost_optimizer.optimize_scaling_costs({
                "detection": 0.9,
                "diagnosis": 0.8,
                "communication": 0.7
            })
            
            # Should recommend scaling up for all high-utilization services
            assert len(recommendations["scale_up"]) >= 3
    
    @pytest.mark.asyncio
    async def test_cost_budget_constraint_scenario(self):
        """Test performance optimization under strict cost constraints."""
        with patch('aioboto3.Session') as mock_boto3:
            mock_boto3.return_value = AsyncMock()
            
            cost_optimizer = await get_cost_optimizer()
            
            # Set strict cost threshold
            await cost_optimizer.set_cost_threshold(CostThreshold.LOW)
            
            # Select models under cost constraints
            models = []
            for severity in ["low", "medium", "high", "critical"]:
                model = await cost_optimizer.select_optimal_model(
                    task_type="detection",
                    incident_severity=severity,
                    max_cost_per_1k_tokens=1.0  # Very strict limit
                )
                models.append(model)
            
            # Should select cost-effective models even for high severity
            for model in models:
                config = cost_optimizer.model_configs[model]
                assert config.cost_per_1k_tokens <= 1.0
    
    @pytest.mark.asyncio
    async def test_multi_region_failover_scenario(self):
        """Test performance optimization during regional failures."""
        with patch('aioboto3.Session') as mock_boto3:
            mock_boto3.return_value = AsyncMock()
            
            scaling_manager = await get_scaling_manager()
            
            # Simulate regional failure by marking replicas as unhealthy
            us_east_replicas = [
                r for r in scaling_manager.agent_replicas["detection"]
                if r.region == "us-east-1"
            ]
            
            for replica in us_east_replicas:
                replica.status = "unhealthy"
            
            # Should failover to healthy replicas in other regions
            incident_data = {"region": "us-east-1", "severity": "critical"}
            selected_replica = await scaling_manager.select_agent_replica("detection", incident_data)
            
            if selected_replica:
                # Should select healthy replica from different region
                assert selected_replica.status == "healthy"
                assert selected_replica.region != "us-east-1"