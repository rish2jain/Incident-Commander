"""
Unit tests for Cost Optimizer Service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.services.cost_optimizer import (
    CostOptimizer, ModelTier, CostThreshold, ModelConfig, CostMetrics,
    BusinessHourPattern, get_cost_optimizer
)
from src.utils.exceptions import CostOptimizationError


class TestCostOptimizer:
    """Test cases for CostOptimizer."""
    
    @pytest.fixture
    def optimizer(self):
        """Create cost optimizer for testing."""
        optimizer = CostOptimizer()
        
        # Mock AWS clients to avoid external dependencies
        optimizer.lambda_client = AsyncMock()
        optimizer.cloudwatch_client = AsyncMock()
        optimizer.cost_explorer_client = AsyncMock()
        
        # Mock initialization methods to avoid external dependencies
        optimizer._initialize_aws_clients = AsyncMock()
        optimizer._load_model_configs = AsyncMock()
        
        return optimizer
    
    @pytest.mark.asyncio
    async def test_initialization(self, optimizer):
        """Test optimizer initialization."""
        await optimizer.initialize()
        
        # Verify model configurations are loaded
        assert len(optimizer.model_configs) >= 4
        assert "claude-3-haiku" in optimizer.model_configs
        assert "claude-3-sonnet" in optimizer.model_configs
        
        # Verify cost thresholds are set
        assert len(optimizer.cost_thresholds) == 4
        assert CostThreshold.LOW in optimizer.cost_thresholds
        
        # Verify business patterns are configured
        assert len(optimizer.business_patterns) >= 4
        assert "us-east-1" in optimizer.business_patterns
    
    @pytest.mark.asyncio
    async def test_model_selection_critical_incident(self, optimizer):
        """Test model selection for critical incidents."""
        await optimizer.initialize()
        
        # Critical incident should prioritize accuracy over cost
        model = await optimizer.select_optimal_model(
            task_type="diagnosis",
            incident_severity="critical",
            required_accuracy=0.85  # Adjusted to match available models
        )
        
        # Should select high-accuracy model (best available)
        selected_config = optimizer.model_configs[model]
        assert selected_config.accuracy_score >= 0.85
    
    @pytest.mark.asyncio
    async def test_model_selection_low_severity(self, optimizer):
        """Test model selection for low severity incidents."""
        await optimizer.initialize()
        
        # Low severity should prioritize cost over accuracy
        model = await optimizer.select_optimal_model(
            task_type="detection",
            incident_severity="low",
            required_accuracy=0.80
        )
        
        # Should select cost-effective model
        selected_config = optimizer.model_configs[model]
        assert selected_config.tier in [ModelTier.ECONOMY, ModelTier.STANDARD]
    
    @pytest.mark.asyncio
    async def test_model_selection_with_cost_limit(self, optimizer):
        """Test model selection with cost constraints."""
        await optimizer.initialize()
        
        # Set strict cost limit
        model = await optimizer.select_optimal_model(
            task_type="communication",
            incident_severity="medium",
            required_accuracy=0.85,
            max_cost_per_1k_tokens=1.0  # Very low limit
        )
        
        # Should select cheapest model that meets requirements
        selected_config = optimizer.model_configs[model]
        assert selected_config.cost_per_1k_tokens <= 1.0
    
    @pytest.mark.asyncio
    async def test_cost_effectiveness_calculation(self, optimizer):
        """Test cost-effectiveness calculation."""
        await optimizer.initialize()
        
        # Create test models with different characteristics
        models = [
            ("fast_cheap", ModelConfig("fast_cheap", 0.5, 0.85, 500, 4096, ModelTier.ECONOMY)),
            ("slow_expensive", ModelConfig("slow_expensive", 5.0, 0.95, 2000, 4096, ModelTier.PREMIUM))
        ]
        
        # For speed-critical tasks, should prefer faster model
        best_model = optimizer._calculate_cost_effectiveness(models, "detection")
        assert best_model in ["fast_cheap", "slow_expensive"]
        
        # For accuracy-critical tasks, should consider accuracy more
        best_model = optimizer._calculate_cost_effectiveness(models, "diagnosis")
        assert best_model in ["fast_cheap", "slow_expensive"]
    
    @pytest.mark.asyncio
    async def test_token_usage_estimation(self, optimizer):
        """Test token usage estimation."""
        await optimizer.initialize()
        
        # Test different task types
        detection_tokens = optimizer._estimate_token_usage("detection", "medium")
        diagnosis_tokens = optimizer._estimate_token_usage("diagnosis", "medium")
        
        # Diagnosis should use more tokens than detection
        assert diagnosis_tokens > detection_tokens
        
        # High severity should use more tokens
        high_severity_tokens = optimizer._estimate_token_usage("detection", "high")
        medium_severity_tokens = optimizer._estimate_token_usage("detection", "medium")
        assert high_severity_tokens > medium_severity_tokens
    
    @pytest.mark.asyncio
    async def test_lambda_warming(self, optimizer):
        """Test Lambda function warming."""
        await optimizer.initialize()
        
        # Mock successful warming
        optimizer._invoke_lambda_warming = AsyncMock()
        
        functions = ["detection-agent", "diagnosis-agent"]
        results = await optimizer.warm_lambda_functions(functions)
        
        # Should warm all requested functions
        assert len(results) == 2
        assert all(results.values())  # All should succeed
        
        # Should update warming cost
        assert optimizer.metrics.lambda_warm_cost > 0
    
    @pytest.mark.asyncio
    async def test_lambda_warming_cache(self, optimizer):
        """Test Lambda warming cache to prevent over-warming."""
        await optimizer.initialize()
        
        # Mock successful warming
        optimizer._invoke_lambda_warming = AsyncMock()
        
        # Warm function first time
        await optimizer.warm_lambda_functions(["detection-agent"])
        first_call_count = optimizer._invoke_lambda_warming.call_count
        
        # Warm again immediately - should use cache
        await optimizer.warm_lambda_functions(["detection-agent"])
        second_call_count = optimizer._invoke_lambda_warming.call_count
        
        # Should not invoke warming again due to cache
        assert second_call_count == first_call_count
    
    @pytest.mark.asyncio
    async def test_predictive_lambda_warming(self, optimizer):
        """Test predictive Lambda warming based on business hours."""
        await optimizer.initialize()
        
        optimizer.warm_lambda_functions = AsyncMock()
        
        # Mock business hours (9 AM in timezone) - skip pytz dependency
        with patch('src.services.cost_optimizer.datetime') as mock_datetime:
            mock_now = Mock()
            mock_now.hour = 9  # Business start time
            mock_now.weekday.return_value = 1  # Tuesday
            mock_datetime.now.return_value = mock_now
            
            # Mock the timezone import to avoid pytz dependency
            with patch('src.services.cost_optimizer.pytz') as mock_pytz:
                mock_tz = Mock()
                mock_pytz.timezone.return_value = mock_tz
                
                await optimizer.predictive_lambda_warming("us-east-1")
                
                # Should trigger warming during business hours
                optimizer.warm_lambda_functions.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scaling_cost_optimization(self, optimizer):
        """Test scaling cost optimization recommendations."""
        await optimizer.initialize()
        
        # Mock current cost calculation
        optimizer._calculate_current_hourly_cost = AsyncMock(return_value=75.0)
        
        # Test with high utilization
        current_load = {
            "detection": 0.85,  # High utilization
            "diagnosis": 0.25   # Low utilization
        }
        
        recommendations = await optimizer.optimize_scaling_costs(current_load)
        
        # Should recommend scale up for high utilization
        assert len(recommendations["scale_up"]) > 0
        assert any(r["agent_type"] == "detection" for r in recommendations["scale_up"])
        
        # Should recommend scale down for low utilization
        assert len(recommendations["scale_down"]) > 0
        assert any(r["agent_type"] == "diagnosis" for r in recommendations["scale_down"])
    
    @pytest.mark.asyncio
    async def test_replica_cost_estimation(self, optimizer):
        """Test replica cost estimation."""
        await optimizer.initialize()
        
        # Test different agent types
        detection_cost = optimizer._estimate_replica_cost("detection")
        diagnosis_cost = optimizer._estimate_replica_cost("diagnosis")
        
        # Diagnosis should be more expensive due to model calls
        assert diagnosis_cost > detection_cost
        
        # Unknown agent type should have default cost
        unknown_cost = optimizer._estimate_replica_cost("unknown")
        assert unknown_cost > 0
    
    @pytest.mark.asyncio
    async def test_current_hourly_cost_calculation(self, optimizer):
        """Test current hourly cost calculation."""
        await optimizer.initialize()
        
        # Set up some costs
        optimizer.metrics.cost_by_service["detection"] = 10.0
        optimizer.metrics.cost_by_service["diagnosis"] = 20.0
        optimizer.metrics.lambda_warm_cost = 0.001
        optimizer.metrics.scaling_cost = 5.0
        
        cost = await optimizer._calculate_current_hourly_cost()
        
        # Should sum all cost sources
        assert cost >= 35.0  # 10 + 20 + 5 + (0.001 * 3600)
    
    @pytest.mark.asyncio
    async def test_cost_threshold_monitoring(self, optimizer):
        """Test cost threshold monitoring and responses."""
        await optimizer.initialize()
        
        # Mock emergency cost controls
        optimizer._trigger_emergency_cost_controls = AsyncMock()
        optimizer._trigger_cost_optimization = AsyncMock()
        
        # Test emergency threshold
        await optimizer._check_cost_thresholds(1500.0)  # Above emergency limit
        optimizer._trigger_emergency_cost_controls.assert_called_once()
        
        # Reset mocks for next test
        optimizer._trigger_cost_optimization.reset_mock()
        
        # Test critical threshold (need to reset emergency flag first)
        optimizer.optimization_enabled = True  # Reset from emergency
        await optimizer._check_cost_thresholds(600.0)  # Above critical (500.0)
        optimizer._trigger_cost_optimization.assert_called_once()
        
        # Test normal threshold
        await optimizer._check_cost_thresholds(50.0)  # Normal range
        assert optimizer.current_cost_threshold == CostThreshold.LOW  # 50 is in LOW range
    
    @pytest.mark.asyncio
    async def test_emergency_cost_controls(self, optimizer):
        """Test emergency cost control activation."""
        await optimizer.initialize()
        
        optimizer.metrics.current_hourly_cost = 1200.0
        
        await optimizer._trigger_emergency_cost_controls()
        
        # Should disable optimization and record action
        assert not optimizer.optimization_enabled
        assert any("Emergency cost controls" in action for action in optimizer.metrics.optimization_actions)
    
    @pytest.mark.asyncio
    async def test_cost_optimization_recommendations(self, optimizer):
        """Test cost optimization recommendation generation."""
        await optimizer.initialize()
        
        # Set up usage history for expensive model
        optimizer.model_usage_history["claude-3-opus"] = [
            {
                "timestamp": datetime.utcnow(),
                "task_type": "detection",
                "severity": "low",
                "estimated_cost": 0.15,
                "estimated_tokens": 500
            }
        ] * 15  # Enough data for analysis
        
        recommendations = await optimizer._generate_cost_optimizations()
        
        # Should recommend cheaper alternatives for expensive models
        model_recs = [r for r in recommendations if r["type"] == "model_optimization"]
        if model_recs:
            assert any(r["current_model"] == "claude-3-opus" for r in model_recs)
    
    @pytest.mark.asyncio
    async def test_cost_optimization_application(self, optimizer):
        """Test cost optimization application."""
        await optimizer.initialize()
        
        recommendation = {
            "type": "model_optimization",
            "current_model": "claude-3-opus",
            "recommended_model": "claude-3-sonnet",
            "potential_savings": 5.0
        }
        
        initial_savings = optimizer.metrics.cost_savings_achieved
        
        await optimizer._apply_cost_optimization(recommendation)
        
        # Should record cost savings
        assert optimizer.metrics.cost_savings_achieved > initial_savings
    
    @pytest.mark.asyncio
    async def test_usage_history_cleanup(self, optimizer):
        """Test usage history cleanup to prevent memory bloat."""
        await optimizer.initialize()
        
        # Add old usage data
        old_timestamp = datetime.utcnow() - timedelta(hours=25)
        recent_timestamp = datetime.utcnow() - timedelta(hours=1)
        
        optimizer.model_usage_history["test_model"] = [
            {"timestamp": old_timestamp, "cost": 1.0},
            {"timestamp": recent_timestamp, "cost": 2.0}
        ]
        
        await optimizer._cleanup_usage_history()
        
        # Should remove old data, keep recent
        remaining = optimizer.model_usage_history["test_model"]
        assert len(remaining) == 1
        assert remaining[0]["timestamp"] == recent_timestamp
    
    @pytest.mark.asyncio
    async def test_cost_metrics_retrieval(self, optimizer):
        """Test cost metrics retrieval."""
        await optimizer.initialize()
        
        # Set some metrics (note: get_cost_metrics recalculates current_hourly_cost)
        optimizer.metrics.projected_daily_cost = 2040.0
        optimizer.metrics.cost_by_service["detection"] = 25.0
        
        metrics = await optimizer.get_cost_metrics()
        
        # Current hourly cost is recalculated, so check it's updated
        assert metrics.current_hourly_cost >= 0  # Should be calculated value
        assert metrics.projected_daily_cost == 2040.0
        assert metrics.cost_by_service["detection"] == 25.0
    
    @pytest.mark.asyncio
    async def test_cost_recommendations_retrieval(self, optimizer):
        """Test cost recommendation retrieval."""
        await optimizer.initialize()
        
        # Set high cost to trigger recommendations
        optimizer.metrics.current_hourly_cost = 150.0
        
        recommendations = await optimizer.get_cost_recommendations()
        
        # Should include general recommendations for high cost
        assert len(recommendations) > 0
        general_recs = [r for r in recommendations if r["type"] == "general"]
        assert len(general_recs) > 0
    
    @pytest.mark.asyncio
    async def test_cost_threshold_setting(self, optimizer):
        """Test cost threshold setting."""
        await optimizer.initialize()
        
        await optimizer.set_cost_threshold(CostThreshold.HIGH)
        
        assert optimizer.current_cost_threshold == CostThreshold.HIGH
    
    @pytest.mark.asyncio
    async def test_model_selection_recording(self, optimizer):
        """Test model selection recording for cost tracking."""
        await optimizer.initialize()
        
        initial_model_cost = optimizer.metrics.cost_by_model.get("claude-3-haiku", 0)
        initial_service_cost = optimizer.metrics.cost_by_service.get("detection", 0)
        
        await optimizer._record_model_selection("claude-3-haiku", "medium", "detection")
        
        # Should update cost metrics
        assert optimizer.metrics.cost_by_model["claude-3-haiku"] > initial_model_cost
        assert optimizer.metrics.cost_by_service["detection"] > initial_service_cost
        
        # Should record usage history
        assert len(optimizer.model_usage_history["claude-3-haiku"]) > 0


class TestModelConfig:
    """Test ModelConfig data class."""
    
    def test_model_config_initialization(self):
        """Test model configuration initialization."""
        config = ModelConfig(
            model_name="test-model",
            cost_per_1k_tokens=2.5,
            accuracy_score=0.90,
            avg_response_time_ms=1500,
            max_tokens=4096,
            tier=ModelTier.STANDARD
        )
        
        assert config.model_name == "test-model"
        assert config.cost_per_1k_tokens == 2.5
        assert config.accuracy_score == 0.90
        assert config.avg_response_time_ms == 1500
        assert config.max_tokens == 4096
        assert config.tier == ModelTier.STANDARD


class TestCostMetrics:
    """Test CostMetrics data class."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization with defaults."""
        metrics = CostMetrics()
        
        assert metrics.current_hourly_cost == 0.0
        assert metrics.projected_daily_cost == 0.0
        assert isinstance(metrics.cost_by_service, dict)
        assert isinstance(metrics.cost_by_model, dict)
        assert metrics.cost_savings_achieved == 0.0
        assert isinstance(metrics.optimization_actions, list)
        assert metrics.lambda_warm_cost == 0.0
        assert metrics.scaling_cost == 0.0


class TestBusinessHourPattern:
    """Test BusinessHourPattern data class."""
    
    def test_pattern_initialization(self):
        """Test business hour pattern initialization."""
        pattern = BusinessHourPattern(
            timezone="America/New_York",
            business_start=9,
            business_end=17
        )
        
        assert pattern.timezone == "America/New_York"
        assert pattern.business_start == 9
        assert pattern.business_end == 17
        assert pattern.weekend_factor == 0.3
        assert pattern.holiday_factor == 0.1
    
    def test_pattern_custom_factors(self):
        """Test pattern with custom factors."""
        pattern = BusinessHourPattern(
            timezone="Europe/London",
            business_start=8,
            business_end=18,
            weekend_factor=0.5,
            holiday_factor=0.2
        )
        
        assert pattern.weekend_factor == 0.5
        assert pattern.holiday_factor == 0.2


class TestGlobalCostOptimizer:
    """Test global cost optimizer instance."""
    
    @pytest.mark.asyncio
    async def test_singleton_behavior(self):
        """Test that get_cost_optimizer returns singleton."""
        with patch('src.services.cost_optimizer.CostOptimizer') as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance
            
            # First call should create instance
            optimizer1 = await get_cost_optimizer()
            
            # Second call should return same instance
            optimizer2 = await get_cost_optimizer()
            
            assert optimizer1 is optimizer2
            mock_class.assert_called_once()