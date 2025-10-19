"""
Unit tests for Model Cost Optimizer Service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import statistics

from src.services.model_cost_optimizer import (
    ModelCostOptimizer, CostAlert, OptimizationType, CostBudget, UsagePattern,
    CostOptimization, CostForecast, CostMetrics, get_cost_optimizer
)
from src.utils.exceptions import CostOptimizationError


class TestModelCostOptimizer:
    """Test cases for ModelCostOptimizer."""
    
    @pytest.fixture
    def optimizer(self):
        """Create cost optimizer for testing."""
        optimizer = ModelCostOptimizer()
        
        # Mock initialization methods to avoid external dependencies
        optimizer._cost_tracking_loop = AsyncMock()
        optimizer._pattern_analysis_loop = AsyncMock()
        optimizer._optimization_loop = AsyncMock()
        optimizer._forecasting_loop = AsyncMock()
        optimizer._alert_monitoring_loop = AsyncMock()
        
        return optimizer
    
    @pytest.mark.asyncio
    async def test_initialization(self, optimizer):
        """Test optimizer initialization."""
        await optimizer.initialize()
        
        # Verify budget is configured
        assert optimizer.budget.daily_limit > 0
        assert optimizer.budget.weekly_limit > 0
        assert optimizer.budget.monthly_limit > 0
        
        # Verify model costs are configured
        assert len(optimizer.model_costs) >= 3
        assert "claude-3-haiku" in optimizer.model_costs
        assert "claude-3-sonnet" in optimizer.model_costs
        
        # Verify optimization rules are configured
        assert len(optimizer.optimization_rules) > 0
        
        # Verify cost metrics are initialized
        assert isinstance(optimizer.cost_metrics, CostMetrics)
    
    @pytest.mark.asyncio
    async def test_record_model_usage(self, optimizer):
        """Test recording model usage for cost tracking."""
        await optimizer.initialize()
        
        initial_requests = optimizer.cost_metrics.total_requests
        initial_model_cost = optimizer.cost_metrics.cost_by_model.get("claude-3-sonnet", 0)
        initial_task_cost = optimizer.cost_metrics.cost_by_task.get("diagnosis", 0)
        
        await optimizer.record_model_usage(
            model_name="claude-3-sonnet",
            task_type="diagnosis",
            tokens_used=1500,
            actual_cost=4.5
        )
        
        # Should update metrics
        assert optimizer.cost_metrics.total_requests == initial_requests + 1
        assert optimizer.cost_metrics.cost_by_model["claude-3-sonnet"] > initial_model_cost
        assert optimizer.cost_metrics.cost_by_task["diagnosis"] > initial_task_cost
        
        # Should create usage pattern
        pattern_key = "diagnosis_claude-3-sonnet"
        assert pattern_key in optimizer.usage_patterns
        
        # Should add to cost history
        assert len(optimizer.cost_history) > 0
    
    @pytest.mark.asyncio
    async def test_update_real_time_metrics(self, optimizer):
        """Test real-time metrics updates."""
        await optimizer.initialize()
        
        # Add some cost history
        now = datetime.utcnow()
        optimizer.cost_history.extend([
            {"timestamp": now - timedelta(minutes=30), "cost": 2.0},
            {"timestamp": now - timedelta(minutes=15), "cost": 3.0},
            {"timestamp": now - timedelta(minutes=5), "cost": 1.5}
        ])
        
        optimizer.cost_metrics.total_requests = 10
        optimizer.cost_metrics.cost_by_model = {"claude-3-sonnet": 15.0, "claude-3-haiku": 5.0}
        
        await optimizer._update_real_time_metrics()
        
        # Should calculate hourly rate from recent costs
        assert optimizer.cost_metrics.current_hourly_rate > 0
        
        # Should calculate daily spend
        assert optimizer.cost_metrics.daily_spend > 0
        
        # Should calculate average cost per request
        assert optimizer.cost_metrics.average_cost_per_request > 0
        
        # Should calculate efficiency score
        assert 0 <= optimizer.cost_metrics.cost_efficiency_score <= 1
    
    @pytest.mark.asyncio
    async def test_calculate_efficiency_score(self, optimizer):
        """Test efficiency score calculation."""
        await optimizer.initialize()
        
        # Create usage patterns with different efficiency levels
        optimizer.usage_patterns["high_efficiency"] = UsagePattern(
            task_type="detection",
            model_name="claude-3-haiku",
            hourly_usage=[10, 8, 12, 15],
            cost_per_hour=[2.0, 1.5, 2.5, 3.0]
        )
        
        optimizer.usage_patterns["low_efficiency"] = UsagePattern(
            task_type="diagnosis",
            model_name="claude-3-opus",
            hourly_usage=[2, 1, 3, 2],
            cost_per_hour=[15.0, 12.0, 18.0, 14.0]
        )
        
        efficiency_score = await optimizer._calculate_efficiency_score()
        
        # Should calculate efficiency based on usage vs cost
        assert 0 <= efficiency_score <= 1
        
        # Should update individual pattern efficiency scores
        assert optimizer.usage_patterns["high_efficiency"].efficiency_score > 0
        assert optimizer.usage_patterns["low_efficiency"].efficiency_score > 0
    
    @pytest.mark.asyncio
    async def test_analyze_usage_patterns(self, optimizer):
        """Test usage pattern analysis."""
        await optimizer.initialize()
        
        # Create test usage pattern
        pattern = UsagePattern(
            task_type="diagnosis",
            model_name="claude-3-sonnet",
            hourly_usage=[0, 0, 5, 10, 15, 12, 8, 3, 0, 0],  # Peak at hours 3-7
            cost_per_hour=[0, 0, 15, 30, 45, 36, 24, 9, 0, 0]
        )
        optimizer.usage_patterns["diagnosis_claude-3-sonnet"] = pattern
        
        analysis = await optimizer.analyze_usage_patterns()
        
        # Should identify patterns
        assert "patterns" in analysis
        assert "diagnosis_claude-3-sonnet" in analysis["patterns"]
        
        # Should identify peak hours
        pattern_info = analysis["patterns"]["diagnosis_claude-3-sonnet"]
        assert len(pattern_info["peak_hours"]) > 0
        assert 4 in pattern_info["peak_hours"]  # Hour with max usage
        
        # Should calculate totals
        assert pattern_info["total_usage"] == sum(pattern.hourly_usage)
        assert pattern_info["total_cost"] == sum(pattern.cost_per_hour)
    
    @pytest.mark.asyncio
    async def test_generate_optimizations_model_substitution(self, optimizer):
        """Test optimization generation for model substitution."""
        await optimizer.initialize()
        
        # Create expensive usage pattern
        expensive_pattern = UsagePattern(
            task_type="communication",  # Low-accuracy task
            model_name="claude-3-opus",  # Expensive model
            hourly_usage=[5, 3, 8, 6],
            cost_per_hour=[75, 45, 120, 90]
        )
        optimizer.usage_patterns["communication_claude-3-opus"] = expensive_pattern
        
        optimizations = await optimizer.generate_optimizations()
        
        # Should recommend cheaper model for low-accuracy tasks
        model_substitutions = [
            opt for opt in optimizations 
            if opt.optimization_type == OptimizationType.MODEL_SUBSTITUTION
        ]
        
        assert len(model_substitutions) > 0
        substitution = model_substitutions[0]
        assert substitution.current_model == "claude-3-opus"
        assert substitution.recommended_model == "claude-3-haiku"
        assert substitution.potential_savings > 0
    
    @pytest.mark.asyncio
    async def test_generate_optimizations_batching(self, optimizer):
        """Test optimization generation for batching."""
        await optimizer.initialize()
        
        # Create concentrated usage pattern
        concentrated_pattern = UsagePattern(
            task_type="diagnosis",
            model_name="claude-3-sonnet",
            hourly_usage=[0, 0, 20, 25, 18, 0, 0, 0],  # Concentrated in 3 hours
            cost_per_hour=[0, 0, 60, 75, 54, 0, 0, 0],
            peak_hours=[2, 3, 4]
        )
        optimizer.usage_patterns["diagnosis_claude-3-sonnet"] = concentrated_pattern
        
        optimizations = await optimizer.generate_optimizations()
        
        # Should recommend batching for concentrated usage
        batching_opts = [
            opt for opt in optimizations 
            if opt.optimization_type == OptimizationType.BATCHING
        ]
        
        assert len(batching_opts) > 0
        batching = batching_opts[0]
        assert batching.task_type == "diagnosis"
        assert batching.potential_savings > 0
    
    @pytest.mark.asyncio
    async def test_generate_optimizations_caching(self, optimizer):
        """Test optimization generation for caching."""
        await optimizer.initialize()
        
        # Create low-efficiency pattern
        inefficient_pattern = UsagePattern(
            task_type="prediction",
            model_name="claude-3-sonnet",
            hourly_usage=[10, 8, 12, 9],
            cost_per_hour=[30, 24, 36, 27],
            efficiency_score=0.3  # Low efficiency
        )
        optimizer.usage_patterns["prediction_claude-3-sonnet"] = inefficient_pattern
        
        optimizations = await optimizer.generate_optimizations()
        
        # Should recommend caching for low efficiency
        caching_opts = [
            opt for opt in optimizations 
            if opt.optimization_type == OptimizationType.CACHING
        ]
        
        assert len(caching_opts) > 0
        caching = caching_opts[0]
        assert caching.task_type == "prediction"
        assert caching.potential_savings > 0
    
    @pytest.mark.asyncio
    async def test_apply_optimization_auto_applicable(self, optimizer):
        """Test applying auto-applicable optimization."""
        await optimizer.initialize()
        
        optimization = CostOptimization(
            optimization_type=OptimizationType.MODEL_SUBSTITUTION,
            current_model="claude-3-sonnet",
            recommended_model="claude-3-haiku",
            task_type="communication",
            potential_savings=10.0,
            confidence_score=0.9,
            impact_assessment="Minimal impact",
            implementation_effort="Low",
            auto_applicable=True
        )
        
        result = await optimizer.apply_optimization(optimization)
        
        # Should succeed for auto-applicable optimization
        assert result["success"]
        assert len(optimizer.applied_optimizations) > 0
    
    @pytest.mark.asyncio
    async def test_apply_optimization_manual_required(self, optimizer):
        """Test applying optimization that requires manual implementation."""
        await optimizer.initialize()
        
        optimization = CostOptimization(
            optimization_type=OptimizationType.CACHING,
            current_model="claude-3-sonnet",
            recommended_model=None,
            task_type="diagnosis",
            potential_savings=15.0,
            confidence_score=0.8,
            impact_assessment="Requires caching implementation",
            implementation_effort="High",
            auto_applicable=False
        )
        
        result = await optimizer.apply_optimization(optimization)
        
        # Should fail for manual optimization
        assert not result["success"]
        assert "Manual implementation required" in result["reason"]
    
    @pytest.mark.asyncio
    async def test_generate_cost_forecast_insufficient_data(self, optimizer):
        """Test cost forecast with insufficient data."""
        await optimizer.initialize()
        
        # Add minimal cost history
        optimizer.cost_history.extend([
            {"timestamp": datetime.utcnow(), "cost": 5.0}
        ])
        
        forecast = await optimizer.generate_cost_forecast(30)
        
        # Should return empty forecast for insufficient data
        assert len(forecast.daily_forecast) == 0
        assert len(forecast.weekly_forecast) == 0
        assert len(forecast.monthly_forecast) == 0
    
    @pytest.mark.asyncio
    async def test_generate_cost_forecast_with_data(self, optimizer):
        """Test cost forecast with sufficient data."""
        await optimizer.initialize()
        
        # Add sufficient cost history (14 days)
        base_date = datetime.utcnow() - timedelta(days=14)
        for day in range(14):
            for hour in range(24):
                timestamp = base_date + timedelta(days=day, hours=hour)
                # Simulate increasing trend
                cost = 5.0 + (day * 0.5) + (hour * 0.1)
                optimizer.cost_history.append({
                    "timestamp": timestamp,
                    "cost": cost
                })
        
        forecast = await optimizer.generate_cost_forecast(30)
        
        # Should generate forecasts
        assert len(forecast.daily_forecast) == 30
        assert len(forecast.weekly_forecast) > 0
        assert len(forecast.monthly_forecast) > 0
        
        # Should detect trend
        assert forecast.trend_direction in ["increasing", "decreasing", "stable"]
        
        # Should have confidence interval
        assert len(forecast.confidence_interval) == 2
        assert forecast.confidence_interval[0] <= forecast.confidence_interval[1]
    
    @pytest.mark.asyncio
    async def test_check_budget_alerts_daily_warning(self, optimizer):
        """Test budget alert generation for daily warning."""
        await optimizer.initialize()
        
        # Set budget and current spend
        optimizer.budget.daily_limit = 100.0
        optimizer.cost_metrics.daily_spend = 85.0  # 85% of budget
        
        alerts = await optimizer.check_budget_alerts()
        
        # Should generate warning alert
        warning_alerts = [alert for alert in alerts if alert["level"] == CostAlert.WARNING]
        assert len(warning_alerts) > 0
        
        daily_alerts = [alert for alert in alerts if alert["type"] == "daily_budget"]
        assert len(daily_alerts) > 0
    
    @pytest.mark.asyncio
    async def test_check_budget_alerts_daily_critical(self, optimizer):
        """Test budget alert generation for daily critical."""
        await optimizer.initialize()
        
        # Set budget and current spend
        optimizer.budget.daily_limit = 100.0
        optimizer.cost_metrics.daily_spend = 95.0  # 95% of budget
        
        alerts = await optimizer.check_budget_alerts()
        
        # Should generate critical alert
        critical_alerts = [alert for alert in alerts if alert["level"] == CostAlert.CRITICAL]
        assert len(critical_alerts) > 0
    
    @pytest.mark.asyncio
    async def test_check_budget_alerts_spending_spike(self, optimizer):
        """Test spending spike alert generation."""
        await optimizer.initialize()
        
        # Set up spending spike
        optimizer.cost_metrics.current_hourly_rate = 50.0
        optimizer.cost_metrics.average_cost_per_request = 0.1  # Normal rate
        
        alerts = await optimizer.check_budget_alerts()
        
        # Should detect spending spike
        spike_alerts = [alert for alert in alerts if alert["type"] == "spending_spike"]
        assert len(spike_alerts) > 0
    
    @pytest.mark.asyncio
    async def test_get_cost_report(self, optimizer):
        """Test comprehensive cost report generation."""
        await optimizer.initialize()
        
        # Set up some data
        optimizer.cost_metrics.daily_spend = 75.0
        optimizer.budget.daily_limit = 100.0
        optimizer.cost_metrics.weekly_spend = 450.0
        optimizer.budget.weekly_limit = 600.0
        
        # Mock methods to avoid complex setup
        optimizer.generate_optimizations = AsyncMock(return_value=[])
        optimizer.generate_cost_forecast = AsyncMock(return_value=CostForecast())
        optimizer.analyze_usage_patterns = AsyncMock(return_value={"patterns": {}})
        optimizer.check_budget_alerts = AsyncMock(return_value=[])
        
        report = await optimizer.get_cost_report()
        
        # Should include all report sections
        assert "cost_metrics" in report
        assert "budget_status" in report
        assert "usage_analysis" in report
        assert "optimizations" in report
        assert "cost_forecast" in report
        assert "alerts" in report
        
        # Should calculate budget usage
        budget_status = report["budget_status"]
        assert budget_status["daily_usage"] == 0.75  # 75/100
        assert budget_status["weekly_usage"] == 0.75  # 450/600
        assert budget_status["remaining_daily"] == 25.0
        assert budget_status["remaining_weekly"] == 150.0
    
    @pytest.mark.asyncio
    async def test_set_budget(self, optimizer):
        """Test budget setting."""
        await optimizer.initialize()
        
        await optimizer.set_budget(
            daily_limit=150.0,
            weekly_limit=900.0,
            monthly_limit=3600.0
        )
        
        # Should update budget
        assert optimizer.budget.daily_limit == 150.0
        assert optimizer.budget.weekly_limit == 900.0
        assert optimizer.budget.monthly_limit == 3600.0


class TestCostBudget:
    """Test CostBudget data class."""
    
    def test_budget_initialization(self):
        """Test budget initialization."""
        budget = CostBudget(
            daily_limit=100.0,
            weekly_limit=600.0,
            monthly_limit=2400.0
        )
        
        assert budget.daily_limit == 100.0
        assert budget.weekly_limit == 600.0
        assert budget.monthly_limit == 2400.0
        
        # Should have default alert thresholds
        assert "warning" in budget.alert_thresholds
        assert "critical" in budget.alert_thresholds
        assert "emergency" in budget.alert_thresholds
    
    def test_budget_custom_thresholds(self):
        """Test budget with custom alert thresholds."""
        custom_thresholds = {
            "warning": 0.7,
            "critical": 0.85,
            "emergency": 0.95
        }
        
        budget = CostBudget(
            daily_limit=100.0,
            weekly_limit=600.0,
            monthly_limit=2400.0,
            alert_thresholds=custom_thresholds
        )
        
        assert budget.alert_thresholds["warning"] == 0.7
        assert budget.alert_thresholds["critical"] == 0.85
        assert budget.alert_thresholds["emergency"] == 0.95


class TestUsagePattern:
    """Test UsagePattern data class."""
    
    def test_usage_pattern_initialization(self):
        """Test usage pattern initialization."""
        pattern = UsagePattern(
            task_type="diagnosis",
            model_name="claude-3-sonnet"
        )
        
        assert pattern.task_type == "diagnosis"
        assert pattern.model_name == "claude-3-sonnet"
        assert isinstance(pattern.hourly_usage, list)
        assert isinstance(pattern.daily_usage, list)
        assert isinstance(pattern.cost_per_hour, list)
        assert isinstance(pattern.peak_hours, list)
        assert pattern.efficiency_score == 0.0


class TestCostOptimization:
    """Test CostOptimization data class."""
    
    def test_optimization_initialization(self):
        """Test optimization initialization."""
        optimization = CostOptimization(
            optimization_type=OptimizationType.MODEL_SUBSTITUTION,
            current_model="claude-3-opus",
            recommended_model="claude-3-sonnet",
            task_type="diagnosis",
            potential_savings=25.0,
            confidence_score=0.85,
            impact_assessment="Minimal accuracy impact",
            implementation_effort="Low"
        )
        
        assert optimization.optimization_type == OptimizationType.MODEL_SUBSTITUTION
        assert optimization.current_model == "claude-3-opus"
        assert optimization.recommended_model == "claude-3-sonnet"
        assert optimization.task_type == "diagnosis"
        assert optimization.potential_savings == 25.0
        assert optimization.confidence_score == 0.85
        assert optimization.impact_assessment == "Minimal accuracy impact"
        assert optimization.implementation_effort == "Low"
        assert optimization.auto_applicable == False  # Default value


class TestCostForecast:
    """Test CostForecast data class."""
    
    def test_forecast_initialization(self):
        """Test forecast initialization with defaults."""
        forecast = CostForecast()
        
        assert isinstance(forecast.daily_forecast, list)
        assert isinstance(forecast.weekly_forecast, list)
        assert isinstance(forecast.monthly_forecast, list)
        assert forecast.trend_direction == "stable"
        assert forecast.confidence_interval == (0.0, 0.0)
        assert forecast.forecast_accuracy == 0.0
    
    def test_forecast_with_data(self):
        """Test forecast with actual data."""
        forecast = CostForecast(
            daily_forecast=[100.0, 105.0, 110.0],
            weekly_forecast=[700.0, 735.0],
            monthly_forecast=[3000.0],
            trend_direction="increasing",
            confidence_interval=(95.0, 115.0),
            forecast_accuracy=0.85
        )
        
        assert len(forecast.daily_forecast) == 3
        assert len(forecast.weekly_forecast) == 2
        assert len(forecast.monthly_forecast) == 1
        assert forecast.trend_direction == "increasing"
        assert forecast.confidence_interval == (95.0, 115.0)
        assert forecast.forecast_accuracy == 0.85


class TestCostMetrics:
    """Test CostMetrics data class."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization with defaults."""
        metrics = CostMetrics()
        
        assert metrics.current_hourly_rate == 0.0
        assert metrics.daily_spend == 0.0
        assert metrics.weekly_spend == 0.0
        assert metrics.monthly_spend == 0.0
        assert isinstance(metrics.cost_by_model, dict)
        assert isinstance(metrics.cost_by_task, dict)
        assert isinstance(metrics.cost_by_hour, list)
        assert metrics.total_requests == 0
        assert metrics.average_cost_per_request == 0.0
        assert metrics.cost_efficiency_score == 0.0


class TestGlobalCostOptimizer:
    """Test global cost optimizer instance."""
    
    @pytest.mark.asyncio
    async def test_singleton_behavior(self):
        """Test that get_cost_optimizer returns singleton."""
        with patch('src.services.model_cost_optimizer.ModelCostOptimizer') as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance
            
            # First call should create instance
            optimizer1 = await get_cost_optimizer()
            
            # Second call should return same instance
            optimizer2 = await get_cost_optimizer()
            
            assert optimizer1 is optimizer2
            mock_class.assert_called_once()


class TestCostOptimizerIntegration:
    """Integration tests for cost optimizer."""
    
    @pytest.fixture
    def optimizer_with_data(self):
        """Create optimizer with test data."""
        optimizer = ModelCostOptimizer()
        
        # Mock background tasks
        optimizer._cost_tracking_loop = AsyncMock()
        optimizer._pattern_analysis_loop = AsyncMock()
        optimizer._optimization_loop = AsyncMock()
        optimizer._forecasting_loop = AsyncMock()
        optimizer._alert_monitoring_loop = AsyncMock()
        
        # Add test data
        optimizer.cost_metrics.daily_spend = 80.0
        optimizer.budget.daily_limit = 100.0
        
        return optimizer
    
    @pytest.mark.asyncio
    async def test_end_to_end_optimization_workflow(self, optimizer_with_data):
        """Test complete optimization workflow."""
        optimizer = optimizer_with_data
        await optimizer.initialize()
        
        # Record usage to create patterns
        await optimizer.record_model_usage("claude-3-opus", "communication", 1000, 15.0)
        await optimizer.record_model_usage("claude-3-opus", "communication", 800, 12.0)
        await optimizer.record_model_usage("claude-3-opus", "communication", 1200, 18.0)
        
        # Analyze patterns
        analysis = await optimizer.analyze_usage_patterns()
        assert "patterns" in analysis
        
        # Generate optimizations
        optimizations = await optimizer.generate_optimizations()
        assert len(optimizations) > 0
        
        # Check for model substitution recommendation
        model_subs = [opt for opt in optimizations 
                     if opt.optimization_type == OptimizationType.MODEL_SUBSTITUTION]
        assert len(model_subs) > 0
        
        # Apply auto-applicable optimization
        auto_opts = [opt for opt in optimizations if opt.auto_applicable]
        if auto_opts:
            result = await optimizer.apply_optimization(auto_opts[0])
            assert result["success"]
        
        # Generate cost report
        report = await optimizer.get_cost_report()
        assert "cost_metrics" in report
        assert "optimizations" in report
    
    @pytest.mark.asyncio
    async def test_budget_monitoring_workflow(self, optimizer_with_data):
        """Test budget monitoring and alerting workflow."""
        optimizer = optimizer_with_data
        await optimizer.initialize()
        
        # Set up budget breach scenario
        optimizer.cost_metrics.daily_spend = 92.0  # 92% of budget
        optimizer.budget.daily_limit = 100.0
        
        # Check alerts
        alerts = await optimizer.check_budget_alerts()
        
        # Should generate critical alert
        critical_alerts = [alert for alert in alerts if alert["level"] == CostAlert.CRITICAL]
        assert len(critical_alerts) > 0
        
        # Should update active alerts
        assert len(optimizer.active_alerts) > 0
        
        # Should add to alert history
        assert len(optimizer.alert_history) > 0