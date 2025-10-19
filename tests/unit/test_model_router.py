"""
Unit tests for Model Router Service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.services.model_router import (
    ModelRouter, RoutingRequest, RoutingStrategy, ModelTier, ModelConfig,
    ModelMetrics, CostAnalysis, get_model_router
)
from src.utils.exceptions import ModelRoutingError


class TestModelRouter:
    """Test cases for ModelRouter."""
    
    @pytest.fixture
    def router(self):
        """Create model router for testing."""
        router = ModelRouter()
        
        # Mock AWS clients to avoid external dependencies
        router.bedrock_client = AsyncMock()
        router.aws_factory = Mock()
        
        # Mock initialization methods
        router._perform_health_checks = AsyncMock()
        
        return router
    
    @pytest.mark.asyncio
    async def test_initialization(self, router):
        """Test router initialization."""
        await router.initialize()
        
        # Verify model configurations are loaded
        assert len(router.model_configs) >= 3
        assert "claude-3-haiku" in router.model_configs
        assert "claude-3-sonnet" in router.model_configs
        assert "claude-3-opus" in router.model_configs
        
        # Verify task preferences are configured
        assert len(router.task_preferences) >= 5
        assert "detection" in router.task_preferences
        assert "diagnosis" in router.task_preferences
        
        # Verify model metrics are initialized
        assert len(router.model_metrics) == len(router.model_configs)
        for model_name in router.model_configs.keys():
            assert model_name in router.model_metrics
    
    @pytest.mark.asyncio
    async def test_route_request_balanced_strategy(self, router):
        """Test routing request with balanced strategy."""
        await router.initialize()
        
        # Mock health checks to return all models as healthy
        router._is_model_healthy = AsyncMock(return_value=True)
        
        request = RoutingRequest(
            task_type="diagnosis",
            incident_severity="medium",
            required_accuracy=0.85,
            strategy=RoutingStrategy.BALANCED
        )
        
        result = await router.route_request(request)
        
        # Should return valid routing result
        assert result.selected_model in router.model_configs
        assert result.model_config.model_name == result.selected_model
        assert result.estimated_cost > 0
        assert result.estimated_latency_ms > 0
        assert 0 <= result.confidence_score <= 1
        assert isinstance(result.fallback_models, list)
        assert result.routing_reason
    
    @pytest.mark.asyncio
    async def test_route_request_cost_optimized(self, router):
        """Test routing with cost-optimized strategy."""
        await router.initialize()
        
        router._is_model_healthy = AsyncMock(return_value=True)
        
        request = RoutingRequest(
            task_type="communication",
            incident_severity="low",
            required_accuracy=0.80,
            strategy=RoutingStrategy.COST_OPTIMIZED
        )
        
        result = await router.route_request(request)
        
        # Should select cheapest model that meets requirements
        selected_config = router.model_configs[result.selected_model]
        assert selected_config.tier == ModelTier.ECONOMY or selected_config.cost_per_1k_tokens <= 1.0
        assert "Cost-optimized" in result.routing_reason
    
    @pytest.mark.asyncio
    async def test_route_request_latency_optimized(self, router):
        """Test routing with latency-optimized strategy."""
        await router.initialize()
        
        router._is_model_healthy = AsyncMock(return_value=True)
        
        request = RoutingRequest(
            task_type="detection",
            incident_severity="high",
            required_accuracy=0.85,
            strategy=RoutingStrategy.LATENCY_OPTIMIZED,
            max_latency_ms=1000
        )
        
        result = await router.route_request(request)
        
        # Should select fastest model that meets requirements
        assert result.estimated_latency_ms <= 1000
        assert "Latency-optimized" in result.routing_reason
    
    @pytest.mark.asyncio
    async def test_route_request_accuracy_optimized(self, router):
        """Test routing with accuracy-optimized strategy."""
        await router.initialize()
        
        router._is_model_healthy = AsyncMock(return_value=True)
        
        request = RoutingRequest(
            task_type="resolution",
            incident_severity="critical",
            required_accuracy=0.92,
            strategy=RoutingStrategy.ACCURACY_OPTIMIZED
        )
        
        result = await router.route_request(request)
        
        # Should select highest accuracy model
        selected_config = router.model_configs[result.selected_model]
        assert selected_config.accuracy_score >= 0.92
        assert "Accuracy-optimized" in result.routing_reason
    
    @pytest.mark.asyncio
    async def test_route_request_with_cost_limit(self, router):
        """Test routing with cost constraints."""
        await router.initialize()
        
        router._is_model_healthy = AsyncMock(return_value=True)
        
        request = RoutingRequest(
            task_type="diagnosis",
            incident_severity="medium",
            required_accuracy=0.85,
            max_cost_per_1k_tokens=1.0  # Very low limit
        )
        
        result = await router.route_request(request)
        
        # Should respect cost limit
        selected_config = router.model_configs[result.selected_model]
        assert selected_config.cost_per_1k_tokens <= 1.0
    
    @pytest.mark.asyncio
    async def test_route_request_critical_incident_priority(self, router):
        """Test that critical incidents get priority treatment."""
        await router.initialize()
        
        router._is_model_healthy = AsyncMock(return_value=True)
        
        request = RoutingRequest(
            task_type="diagnosis",
            incident_severity="critical",
            required_accuracy=0.90,
            strategy=RoutingStrategy.BALANCED
        )
        
        result = await router.route_request(request)
        
        # Critical incidents should prioritize accuracy and availability
        selected_config = router.model_configs[result.selected_model]
        assert selected_config.accuracy_score >= 0.90
        assert "High-priority incident" in result.routing_reason
    
    @pytest.mark.asyncio
    async def test_filter_available_models(self, router):
        """Test model filtering based on requirements."""
        await router.initialize()
        
        # Mock health checks
        router._is_model_healthy = AsyncMock(return_value=True)
        
        request = RoutingRequest(
            task_type="diagnosis",
            required_accuracy=0.95,  # High accuracy requirement
            max_latency_ms=1000      # Low latency requirement
        )
        
        task_prefs = router.task_preferences.get("diagnosis", {})
        available_models = await router._filter_available_models(request, task_prefs)
        
        # Should only include models that meet requirements
        for model_name in available_models:
            config = router.model_configs[model_name]
            assert config.accuracy_score >= 0.95
            assert config.avg_response_time_ms <= 1000
    
    @pytest.mark.asyncio
    async def test_filter_available_models_unhealthy(self, router):
        """Test that unhealthy models are filtered out."""
        await router.initialize()
        
        # Mock one model as unhealthy
        def mock_health_check(model_name):
            return model_name != "claude-3-opus"  # Opus is unhealthy
        
        router._is_model_healthy = AsyncMock(side_effect=mock_health_check)
        
        request = RoutingRequest(task_type="diagnosis")
        task_prefs = router.task_preferences.get("diagnosis", {})
        available_models = await router._filter_available_models(request, task_prefs)
        
        # Should exclude unhealthy model
        assert "claude-3-opus" not in available_models
        assert len(available_models) >= 1  # Should have other healthy models
    
    @pytest.mark.asyncio
    async def test_no_available_models_error(self, router):
        """Test error when no models meet requirements."""
        await router.initialize()
        
        # Mock all models as unhealthy
        router._is_model_healthy = AsyncMock(return_value=False)
        
        request = RoutingRequest(
            task_type="diagnosis",
            required_accuracy=0.99  # Impossible requirement
        )
        
        with pytest.raises(ModelRoutingError, match="No models available"):
            await router.route_request(request)
    
    def test_select_optimal_model_single_option(self, router):
        """Test model selection with single available model."""
        available_models = ["claude-3-haiku"]
        request = RoutingRequest(task_type="detection")
        task_prefs = {}
        
        selected = router._select_optimal_model(available_models, request, task_prefs)
        assert selected == "claude-3-haiku"
    
    def test_select_optimal_model_cost_strategy(self, router):
        """Test model selection with cost-optimized strategy."""
        available_models = ["claude-3-haiku", "claude-3-sonnet"]
        request = RoutingRequest(
            task_type="detection",
            strategy=RoutingStrategy.COST_OPTIMIZED
        )
        task_prefs = {}
        
        selected = router._select_optimal_model(available_models, request, task_prefs)
        
        # Should select cheaper model
        selected_config = router.model_configs[selected]
        other_model = [m for m in available_models if m != selected][0]
        other_config = router.model_configs[other_model]
        assert selected_config.cost_per_1k_tokens <= other_config.cost_per_1k_tokens
    
    def test_select_optimal_model_task_preference(self, router):
        """Test model selection with task preferences."""
        available_models = ["claude-3-haiku", "claude-3-sonnet"]
        request = RoutingRequest(task_type="detection")
        task_prefs = {"preferred_tier": ModelTier.ECONOMY}
        
        selected = router._select_optimal_model(available_models, request, task_prefs)
        
        # Should prefer economy tier for detection tasks
        selected_config = router.model_configs[selected]
        if selected_config.tier == ModelTier.ECONOMY:
            assert selected == "claude-3-haiku"
    
    def test_estimate_cost(self, router):
        """Test cost estimation."""
        config = router.model_configs["claude-3-sonnet"]
        context_length = 2000
        
        estimated_cost = router._estimate_cost(config, context_length)
        
        # Should calculate cost based on tokens and model pricing
        assert estimated_cost > 0
        # Cost should be proportional to context length
        larger_cost = router._estimate_cost(config, 4000)
        assert larger_cost > estimated_cost
    
    def test_estimate_latency(self, router):
        """Test latency estimation."""
        config = router.model_configs["claude-3-sonnet"]
        context_length = 2000
        
        estimated_latency = router._estimate_latency(config, context_length)
        
        # Should be based on model's average response time plus context processing
        assert estimated_latency >= config.avg_response_time_ms
        
        # Larger context should take longer
        larger_latency = router._estimate_latency(config, 4000)
        assert larger_latency > estimated_latency
    
    def test_generate_fallback_options(self, router):
        """Test fallback model generation."""
        selected_model = "claude-3-sonnet"
        available_models = ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"]
        
        fallbacks = router._generate_fallback_options(selected_model, available_models)
        
        # Should not include selected model
        assert selected_model not in fallbacks
        # Should return up to 2 fallbacks
        assert len(fallbacks) <= 2
        # Should be ordered by availability score
        if len(fallbacks) > 1:
            config1 = router.model_configs[fallbacks[0]]
            config2 = router.model_configs[fallbacks[1]]
            assert config1.availability_score >= config2.availability_score
    
    def test_generate_routing_reason(self, router):
        """Test routing reason generation."""
        request = RoutingRequest(
            task_type="diagnosis",
            incident_severity="critical",
            strategy=RoutingStrategy.COST_OPTIMIZED
        )
        
        reason = router._generate_routing_reason("claude-3-haiku", request)
        
        # Should include strategy and incident severity
        assert "Cost-optimized" in reason
        assert "High-priority incident" in reason
    
    def test_calculate_confidence_score(self, router):
        """Test confidence score calculation."""
        # Set up model metrics
        router.model_metrics["claude-3-sonnet"].total_requests = 100
        router.model_metrics["claude-3-sonnet"].successful_requests = 95
        
        request = RoutingRequest(
            task_type="diagnosis",
            required_accuracy=0.90
        )
        
        confidence = router._calculate_confidence_score("claude-3-sonnet", request)
        
        # Should be between 0 and 1
        assert 0 <= confidence <= 1
        # Should consider model accuracy and success rate
        assert confidence > 0.8  # Should be high for good model
    
    @pytest.mark.asyncio
    async def test_record_routing_decision(self, router):
        """Test routing decision recording."""
        request = RoutingRequest(task_type="diagnosis")
        
        # Create mock result
        result = Mock()
        result.selected_model = "claude-3-sonnet"
        result.estimated_cost = 0.15
        result.estimated_latency_ms = 1200
        result.confidence_score = 0.92
        result.routing_reason = "Test routing"
        
        initial_history_len = len(router.routing_history)
        initial_cost = router.cost_analysis.cost_by_model.get("claude-3-sonnet", 0)
        
        await router._record_routing_decision(request, result)
        
        # Should add to routing history
        assert len(router.routing_history) == initial_history_len + 1
        
        # Should update cost tracking
        assert router.cost_analysis.cost_by_model["claude-3-sonnet"] > initial_cost
    
    @pytest.mark.asyncio
    async def test_record_request_completion(self, router):
        """Test request completion recording."""
        model_name = "claude-3-sonnet"
        initial_metrics = router.model_metrics[model_name]
        initial_requests = initial_metrics.total_requests
        
        await router.record_request_completion(
            model_name=model_name,
            success=True,
            actual_latency_ms=1100,
            actual_cost=0.12,
            tokens_used=800
        )
        
        # Should update metrics
        metrics = router.model_metrics[model_name]
        assert metrics.total_requests == initial_requests + 1
        assert metrics.successful_requests == initial_metrics.successful_requests + 1
        assert metrics.total_cost == initial_metrics.total_cost + 0.12
        assert metrics.total_tokens == initial_metrics.total_tokens + 800
        assert metrics.last_used is not None
    
    @pytest.mark.asyncio
    async def test_record_request_completion_failure(self, router):
        """Test recording failed request completion."""
        model_name = "claude-3-sonnet"
        initial_metrics = router.model_metrics[model_name]
        
        await router.record_request_completion(
            model_name=model_name,
            success=False,
            actual_latency_ms=5000,  # Timeout
            actual_cost=0.0,
            tokens_used=0
        )
        
        # Should update failure metrics
        metrics = router.model_metrics[model_name]
        assert metrics.failed_requests == initial_metrics.failed_requests + 1
        assert metrics.error_rate > initial_metrics.error_rate
    
    @pytest.mark.asyncio
    async def test_model_health_check(self, router):
        """Test model health checking."""
        await router.initialize()
        
        # Mock successful health check
        router.bedrock_client.invoke_model = AsyncMock(return_value="Health check response")
        
        is_healthy = await router._is_model_healthy("claude-3-sonnet")
        assert is_healthy
        
        # Should cache result
        assert "claude-3-sonnet" in router.model_health_cache
        cached_health, _ = router.model_health_cache["claude-3-sonnet"]
        assert cached_health
    
    @pytest.mark.asyncio
    async def test_model_health_check_failure(self, router):
        """Test model health check failure."""
        await router.initialize()
        
        # Mock failed health check
        router.bedrock_client.invoke_model = AsyncMock(side_effect=Exception("Model unavailable"))
        
        is_healthy = await router._is_model_healthy("claude-3-sonnet")
        assert not is_healthy
        
        # Should cache failure result
        cached_health, _ = router.model_health_cache["claude-3-sonnet"]
        assert not cached_health
    
    @pytest.mark.asyncio
    async def test_model_health_cache_expiry(self, router):
        """Test that health check cache expires."""
        await router.initialize()
        
        # Set expired cache entry
        expired_time = datetime.utcnow() - timedelta(seconds=router.health_check_interval + 1)
        router.model_health_cache["claude-3-sonnet"] = (True, expired_time)
        
        # Mock health check
        router.bedrock_client.invoke_model = AsyncMock(return_value="Health check response")
        
        # Should perform new health check due to expired cache
        is_healthy = await router._is_model_healthy("claude-3-sonnet")
        assert is_healthy
        
        # Should update cache timestamp
        _, cached_time = router.model_health_cache["claude-3-sonnet"]
        assert cached_time > expired_time
    
    @pytest.mark.asyncio
    async def test_get_model_metrics(self, router):
        """Test model metrics retrieval."""
        # Set up some metrics
        router.model_metrics["claude-3-sonnet"].total_requests = 50
        router.model_metrics["claude-3-sonnet"].successful_requests = 48
        
        metrics = await router.get_model_metrics()
        
        # Should return copy of metrics
        assert isinstance(metrics, dict)
        assert "claude-3-sonnet" in metrics
        assert metrics["claude-3-sonnet"].total_requests == 50
        assert metrics["claude-3-sonnet"].successful_requests == 48
    
    @pytest.mark.asyncio
    async def test_get_cost_analysis(self, router):
        """Test cost analysis retrieval."""
        # Set up cost data
        router.cost_analysis.current_hourly_cost = 25.0
        router.cost_analysis.cost_by_model["claude-3-sonnet"] = 15.0
        
        analysis = await router.get_cost_analysis()
        
        assert analysis.current_hourly_cost == 25.0
        assert analysis.cost_by_model["claude-3-sonnet"] == 15.0
    
    @pytest.mark.asyncio
    async def test_get_routing_statistics(self, router):
        """Test routing statistics retrieval."""
        # Add some routing history
        router.routing_history.append({
            "timestamp": datetime.utcnow(),
            "selected_model": "claude-3-sonnet",
            "strategy": "balanced",
            "task_type": "diagnosis",
            "estimated_cost": 0.15,
            "estimated_latency_ms": 1200
        })
        
        stats = await router.get_routing_statistics()
        
        assert stats["total_requests"] == 1
        assert "claude-3-sonnet" in stats["model_usage_distribution"]
        assert "balanced" in stats["strategy_usage_distribution"]
        assert "diagnosis" in stats["task_type_distribution"]
        assert stats["average_estimated_cost"] == 0.15
        assert stats["average_estimated_latency_ms"] == 1200
    
    @pytest.mark.asyncio
    async def test_get_routing_statistics_empty(self, router):
        """Test routing statistics with no history."""
        stats = await router.get_routing_statistics()
        
        assert stats["total_requests"] == 0
    
    @pytest.mark.asyncio
    async def test_update_model_config(self, router):
        """Test model configuration updates."""
        model_name = "claude-3-sonnet"
        original_cost = router.model_configs[model_name].cost_per_1k_tokens
        
        updates = {
            "cost_per_1k_tokens": 2.5,
            "accuracy_score": 0.94
        }
        
        await router.update_model_config(model_name, updates)
        
        # Should update configuration
        config = router.model_configs[model_name]
        assert config.cost_per_1k_tokens == 2.5
        assert config.accuracy_score == 0.94
    
    @pytest.mark.asyncio
    async def test_update_model_config_invalid_model(self, router):
        """Test updating configuration for non-existent model."""
        with pytest.raises(ModelRoutingError, match="Model .* not found"):
            await router.update_model_config("non-existent-model", {"cost_per_1k_tokens": 1.0})
    
    @pytest.mark.asyncio
    async def test_update_model_config_invalid_field(self, router):
        """Test updating invalid configuration field."""
        updates = {
            "invalid_field": "value",
            "cost_per_1k_tokens": 2.5  # Valid field
        }
        
        # Should only update valid fields, ignore invalid ones
        await router.update_model_config("claude-3-sonnet", updates)
        
        # Valid field should be updated
        config = router.model_configs["claude-3-sonnet"]
        assert config.cost_per_1k_tokens == 2.5
        
        # Invalid field should not exist
        assert not hasattr(config, "invalid_field")


class TestModelConfig:
    """Test ModelConfig data class."""
    
    def test_model_config_initialization(self):
        """Test model configuration initialization."""
        config = ModelConfig(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            model_name="claude-3-sonnet",
            cost_per_1k_tokens=3.0,
            accuracy_score=0.92,
            avg_response_time_ms=1200,
            max_tokens=4096,
            tier=ModelTier.STANDARD
        )
        
        assert config.model_id == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert config.model_name == "claude-3-sonnet"
        assert config.cost_per_1k_tokens == 3.0
        assert config.accuracy_score == 0.92
        assert config.avg_response_time_ms == 1200
        assert config.max_tokens == 4096
        assert config.tier == ModelTier.STANDARD
        assert config.availability_score == 1.0  # Default value


class TestModelMetrics:
    """Test ModelMetrics data class."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization with defaults."""
        metrics = ModelMetrics()
        
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.avg_response_time_ms == 0.0
        assert metrics.total_cost == 0.0
        assert metrics.total_tokens == 0
        assert metrics.last_used is None
        assert metrics.error_rate == 0.0


class TestRoutingRequest:
    """Test RoutingRequest data class."""
    
    def test_routing_request_defaults(self):
        """Test routing request with default values."""
        request = RoutingRequest(task_type="detection")
        
        assert request.task_type == "detection"
        assert request.incident_severity == "medium"
        assert request.required_accuracy == 0.85
        assert request.max_latency_ms is None
        assert request.max_cost_per_1k_tokens is None
        assert request.strategy == RoutingStrategy.BALANCED
        assert request.context_length == 1000
    
    def test_routing_request_custom_values(self):
        """Test routing request with custom values."""
        request = RoutingRequest(
            task_type="diagnosis",
            incident_severity="critical",
            required_accuracy=0.95,
            max_latency_ms=2000,
            max_cost_per_1k_tokens=5.0,
            strategy=RoutingStrategy.ACCURACY_OPTIMIZED,
            context_length=2500
        )
        
        assert request.task_type == "diagnosis"
        assert request.incident_severity == "critical"
        assert request.required_accuracy == 0.95
        assert request.max_latency_ms == 2000
        assert request.max_cost_per_1k_tokens == 5.0
        assert request.strategy == RoutingStrategy.ACCURACY_OPTIMIZED
        assert request.context_length == 2500


class TestCostAnalysis:
    """Test CostAnalysis data class."""
    
    def test_cost_analysis_initialization(self):
        """Test cost analysis initialization."""
        analysis = CostAnalysis()
        
        assert analysis.current_hourly_cost == 0.0
        assert analysis.projected_daily_cost == 0.0
        assert isinstance(analysis.cost_by_model, dict)
        assert isinstance(analysis.cost_by_task_type, dict)
        assert analysis.potential_savings == 0.0
        assert isinstance(analysis.optimization_recommendations, list)


class TestGlobalModelRouter:
    """Test global model router instance."""
    
    @pytest.mark.asyncio
    async def test_singleton_behavior(self):
        """Test that get_model_router returns singleton."""
        with patch('src.services.model_router.ModelRouter') as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance
            
            # First call should create instance
            router1 = await get_model_router()
            
            # Second call should return same instance
            router2 = await get_model_router()
            
            assert router1 is router2
            mock_class.assert_called_once()


class TestModelRouterIntegration:
    """Integration tests for model router with cost optimizer."""
    
    @pytest.fixture
    def router_with_optimizer(self):
        """Create router with mocked cost optimizer integration."""
        router = ModelRouter()
        router.bedrock_client = AsyncMock()
        router.aws_factory = Mock()
        router._perform_health_checks = AsyncMock()
        return router
    
    @pytest.mark.asyncio
    async def test_routing_with_cost_tracking(self, router_with_optimizer):
        """Test that routing decisions are tracked for cost analysis."""
        router = router_with_optimizer
        await router.initialize()
        
        router._is_model_healthy = AsyncMock(return_value=True)
        
        request = RoutingRequest(
            task_type="diagnosis",
            strategy=RoutingStrategy.COST_OPTIMIZED
        )
        
        result = await router.route_request(request)
        
        # Should record routing decision
        assert len(router.routing_history) > 0
        
        # Should update cost analysis
        assert result.selected_model in router.cost_analysis.cost_by_model
        assert request.task_type in router.cost_analysis.cost_by_task_type
    
    @pytest.mark.asyncio
    async def test_performance_degradation_handling(self, router_with_optimizer):
        """Test handling of model performance degradation."""
        router = router_with_optimizer
        await router.initialize()
        
        # Simulate model with poor performance
        model_name = "claude-3-sonnet"
        metrics = router.model_metrics[model_name]
        metrics.total_requests = 100
        metrics.successful_requests = 70  # 70% success rate
        metrics.failed_requests = 30
        metrics.error_rate = 0.3
        
        # Update availability score based on performance
        router.model_configs[model_name].availability_score = 0.7
        
        router._is_model_healthy = AsyncMock(return_value=True)
        
        request = RoutingRequest(
            task_type="diagnosis",
            strategy=RoutingStrategy.BALANCED
        )
        
        result = await router.route_request(request)
        
        # Should consider availability score in routing decision
        # Lower availability should reduce confidence
        assert result.confidence_score < 1.0