"""
Integration tests for Model Routing API endpoints.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routers.model_routing import router as model_routing_router
from src.services.model_router import ModelRouter, RoutingStrategy, ModelTier
from src.services.model_cost_optimizer import ModelCostOptimizer


@pytest.fixture
def app():
    """Create FastAPI app with model routing router for testing."""
    app = FastAPI()
    app.include_router(model_routing_router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_model_router():
    """Create mock model router."""
    router = AsyncMock(spec=ModelRouter)
    
    # Mock model configurations
    router.model_configs = {
        "claude-3-haiku": Mock(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            model_name="claude-3-haiku",
            cost_per_1k_tokens=0.25,
            accuracy_score=0.85,
            avg_response_time_ms=800,
            max_tokens=4096,
            tier=ModelTier.ECONOMY,
            availability_score=1.0,
            last_health_check=None
        ),
        "claude-3-sonnet": Mock(
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            model_name="claude-3-sonnet",
            cost_per_1k_tokens=3.0,
            accuracy_score=0.92,
            avg_response_time_ms=1200,
            max_tokens=4096,
            tier=ModelTier.STANDARD,
            availability_score=1.0,
            last_health_check=datetime.utcnow()
        )
    }
    
    # Mock health cache
    router.model_health_cache = {
        "claude-3-haiku": (True, datetime.utcnow()),
        "claude-3-sonnet": (True, datetime.utcnow())
    }
    
    return router


@pytest.fixture
def mock_cost_optimizer():
    """Create mock cost optimizer."""
    optimizer = AsyncMock(spec=ModelCostOptimizer)
    return optimizer


class TestModelRoutingAPI:
    """Test model routing API endpoints."""
    
    @patch('src.api.routers.model_routing.get_model_router')
    def test_route_model_request(self, mock_get_router, client, mock_model_router):
        """Test model routing endpoint."""
        mock_get_router.return_value = mock_model_router
        
        # Mock routing result
        mock_result = Mock()
        mock_result.selected_model = "claude-3-sonnet"
        mock_result.model_config = mock_model_router.model_configs["claude-3-sonnet"]
        mock_result.routing_reason = "Balanced optimization"
        mock_result.estimated_cost = 0.15
        mock_result.estimated_latency_ms = 1200
        mock_result.confidence_score = 0.92
        mock_result.fallback_models = ["claude-3-haiku"]
        
        mock_model_router.route_request.return_value = mock_result
        
        # Test request
        request_data = {
            "task_type": "diagnosis",
            "incident_severity": "medium",
            "required_accuracy": 0.90,
            "strategy": "balanced"
        }
        
        response = client.post("/model-routing/route", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["selected_model"] == "claude-3-sonnet"
        assert data["model_id"] == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert data["routing_reason"] == "Balanced optimization"
        assert data["estimated_cost"] == 0.15
        assert data["estimated_latency_ms"] == 1200
        assert data["confidence_score"] == 0.92
        assert data["fallback_models"] == ["claude-3-haiku"]
        assert data["tier"] == "standard"
        assert data["accuracy_score"] == 0.92
    
    @patch('src.api.routers.model_routing.get_model_router')
    def test_route_model_request_with_constraints(self, mock_get_router, client, mock_model_router):
        """Test model routing with cost and latency constraints."""
        mock_get_router.return_value = mock_model_router
        
        mock_result = Mock()
        mock_result.selected_model = "claude-3-haiku"
        mock_result.model_config = mock_model_router.model_configs["claude-3-haiku"]
        mock_result.routing_reason = "Cost-optimized selection"
        mock_result.estimated_cost = 0.05
        mock_result.estimated_latency_ms = 800
        mock_result.confidence_score = 0.85
        mock_result.fallback_models = []
        
        mock_model_router.route_request.return_value = mock_result
        
        request_data = {
            "task_type": "communication",
            "incident_severity": "low",
            "required_accuracy": 0.80,
            "max_latency_ms": 1000,
            "max_cost_per_1k_tokens": 1.0,
            "strategy": "cost_optimized",
            "context_length": 500
        }
        
        response = client.post("/model-routing/route", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["selected_model"] == "claude-3-haiku"
        assert data["estimated_cost"] == 0.05
        assert data["estimated_latency_ms"] == 800
    
    @patch('src.api.routers.model_routing.get_model_router')
    def test_route_model_request_error(self, mock_get_router, client):
        """Test model routing error handling."""
        mock_router = AsyncMock()
        mock_router.route_request.side_effect = Exception("Routing failed")
        mock_get_router.return_value = mock_router
        
        request_data = {
            "task_type": "diagnosis",
            "strategy": "balanced"
        }
        
        response = client.post("/model-routing/route", json=request_data)
        
        assert response.status_code == 500
        assert "Routing failed" in response.json()["detail"]
    
    @patch('src.api.routers.model_routing.get_model_router')
    def test_get_available_models(self, mock_get_router, client, mock_model_router):
        """Test get available models endpoint."""
        mock_get_router.return_value = mock_model_router
        
        response = client.get("/model-routing/models")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "models" in data
        assert "total_models" in data
        assert data["total_models"] == 2
        
        models = data["models"]
        assert "claude-3-haiku" in models
        assert "claude-3-sonnet" in models
        
        haiku_info = models["claude-3-haiku"]
        assert haiku_info["model_id"] == "anthropic.claude-3-haiku-20240307-v1:0"
        assert haiku_info["cost_per_1k_tokens"] == 0.25
        assert haiku_info["accuracy_score"] == 0.85
        assert haiku_info["tier"] == "economy"
    
    @patch('src.api.routers.model_routing.get_model_router')
    def test_update_model_config(self, mock_get_router, client, mock_model_router):
        """Test update model configuration endpoint."""
        mock_get_router.return_value = mock_model_router
        mock_model_router.update_model_config.return_value = None
        
        update_data = {
            "cost_per_1k_tokens": 2.8,
            "accuracy_score": 0.93
        }
        
        response = client.put("/model-routing/models/claude-3-sonnet/config", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["model_name"] == "claude-3-sonnet"
        assert data["updates_applied"]["cost_per_1k_tokens"] == 2.8
        assert data["updates_applied"]["accuracy_score"] == 0.93
        
        # Verify update_model_config was called
        mock_model_router.update_model_config.assert_called_once_with(
            "claude-3-sonnet", 
            {"cost_per_1k_tokens": 2.8, "accuracy_score": 0.93}
        )
    
    @patch('src.api.routers.model_routing.get_model_router')
    def test_update_model_config_no_updates(self, mock_get_router, client, mock_model_router):
        """Test update model config with no updates provided."""
        mock_get_router.return_value = mock_model_router
        
        response = client.put("/model-routing/models/claude-3-sonnet/config", json={})
        
        assert response.status_code == 400
        assert "No updates provided" in response.json()["detail"]
    
    @patch('src.api.routers.model_routing.get_model_router')
    def test_get_routing_metrics(self, mock_get_router, client, mock_model_router):
        """Test get routing metrics endpoint."""
        mock_get_router.return_value = mock_model_router
        
        # Mock model metrics
        mock_metrics = {
            "claude-3-sonnet": Mock(
                total_requests=100,
                successful_requests=95,
                failed_requests=5,
                avg_response_time_ms=1150.0,
                total_cost=45.0,
                total_tokens=15000,
                last_used=datetime.utcnow(),
                error_rate=0.05
            )
        }
        mock_model_router.get_model_metrics.return_value = mock_metrics
        
        # Mock routing statistics
        mock_stats = {
            "total_requests": 100,
            "model_usage_distribution": {"claude-3-sonnet": 60, "claude-3-haiku": 40},
            "strategy_usage_distribution": {"balanced": 70, "cost_optimized": 30},
            "task_type_distribution": {"diagnosis": 50, "detection": 30, "communication": 20},
            "average_estimated_cost": 0.12,
            "average_estimated_latency_ms": 1000,
            "model_health": {"claude-3-sonnet": True, "claude-3-haiku": True}
        }
        mock_model_router.get_routing_statistics.return_value = mock_stats
        
        response = client.get("/model-routing/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "model_metrics" in data
        assert "routing_statistics" in data
        assert "timestamp" in data
        
        # Check model metrics formatting
        model_metrics = data["model_metrics"]
        assert "claude-3-sonnet" in model_metrics
        sonnet_metrics = model_metrics["claude-3-sonnet"]
        assert sonnet_metrics["total_requests"] == 100
        assert sonnet_metrics["success_rate"] == 0.95
        assert sonnet_metrics["avg_cost_per_token"] == 0.003  # 45.0 / 15000
    
    @patch('src.api.routers.model_routing.get_model_router')
    @patch('src.api.routers.model_routing.get_cost_optimizer')
    def test_record_model_usage(self, mock_get_optimizer, mock_get_router, client, 
                               mock_model_router, mock_cost_optimizer):
        """Test record model usage endpoint."""
        mock_get_router.return_value = mock_model_router
        mock_get_optimizer.return_value = mock_cost_optimizer
        
        mock_model_router.record_request_completion.return_value = None
        mock_cost_optimizer.record_model_usage.return_value = None
        
        usage_data = {
            "model_name": "claude-3-sonnet",
            "task_type": "diagnosis",
            "tokens_used": 1500,
            "actual_cost": 4.5,
            "success": True,
            "actual_latency_ms": 1180
        }
        
        response = client.post("/model-routing/usage/record", json=usage_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "Usage recorded successfully" in data["message"]
        
        # Verify both services were called
        mock_model_router.record_request_completion.assert_called_once_with(
            model_name="claude-3-sonnet",
            success=True,
            actual_latency_ms=1180,
            actual_cost=4.5,
            tokens_used=1500
        )
        
        mock_cost_optimizer.record_model_usage.assert_called_once_with(
            model_name="claude-3-sonnet",
            task_type="diagnosis",
            tokens_used=1500,
            actual_cost=4.5
        )
    
    @patch('src.api.routers.model_routing.get_cost_optimizer')
    def test_get_cost_analysis(self, mock_get_optimizer, client, mock_cost_optimizer):
        """Test get cost analysis endpoint."""
        mock_get_optimizer.return_value = mock_cost_optimizer
        
        mock_report = {
            "cost_metrics": {
                "current_hourly_rate": 25.0,
                "daily_spend": 180.0,
                "cost_by_model": {"claude-3-sonnet": 120.0, "claude-3-haiku": 60.0}
            },
            "budget_status": {
                "daily_usage": 0.72,
                "remaining_daily": 70.0
            },
            "optimizations": [],
            "alerts": []
        }
        mock_cost_optimizer.get_cost_report.return_value = mock_report
        
        response = client.get("/model-routing/cost/analysis")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "cost_analysis" in data
        assert "timestamp" in data
        
        cost_analysis = data["cost_analysis"]
        assert cost_analysis["cost_metrics"]["current_hourly_rate"] == 25.0
        assert cost_analysis["budget_status"]["daily_usage"] == 0.72
    
    @patch('src.api.routers.model_routing.get_cost_optimizer')
    def test_set_cost_budget(self, mock_get_optimizer, client, mock_cost_optimizer):
        """Test set cost budget endpoint."""
        mock_get_optimizer.return_value = mock_cost_optimizer
        mock_cost_optimizer.set_budget.return_value = None
        
        budget_data = {
            "daily_limit": 200.0,
            "weekly_limit": 1200.0,
            "monthly_limit": 4800.0
        }
        
        response = client.post("/model-routing/cost/budget", json=budget_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["budget"]["daily_limit"] == 200.0
        assert data["budget"]["weekly_limit"] == 1200.0
        assert data["budget"]["monthly_limit"] == 4800.0
        
        mock_cost_optimizer.set_budget.assert_called_once_with(
            daily_limit=200.0,
            weekly_limit=1200.0,
            monthly_limit=4800.0
        )
    
    @patch('src.api.routers.model_routing.get_cost_optimizer')
    def test_get_cost_optimizations(self, mock_get_optimizer, client, mock_cost_optimizer):
        """Test get cost optimizations endpoint."""
        mock_get_optimizer.return_value = mock_cost_optimizer
        
        mock_optimizations = [
            Mock(
                optimization_type=Mock(value="model_substitution"),
                current_model="claude-3-opus",
                recommended_model="claude-3-sonnet",
                task_type="communication",
                potential_savings=15.0,
                confidence_score=0.85,
                impact_assessment="Minimal impact",
                implementation_effort="Low",
                auto_applicable=True
            ),
            Mock(
                optimization_type=Mock(value="caching"),
                current_model="claude-3-sonnet",
                recommended_model=None,
                task_type="diagnosis",
                potential_savings=8.0,
                confidence_score=0.75,
                impact_assessment="Requires caching implementation",
                implementation_effort="Medium",
                auto_applicable=False
            )
        ]
        mock_cost_optimizer.generate_optimizations.return_value = mock_optimizations
        
        response = client.get("/model-routing/cost/optimizations")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "optimizations" in data
        assert "total_optimizations" in data
        assert "total_potential_savings" in data
        
        assert data["total_optimizations"] == 2
        assert data["total_potential_savings"] == 23.0
        
        optimizations = data["optimizations"]
        assert len(optimizations) == 2
        
        first_opt = optimizations[0]
        assert first_opt["index"] == 0
        assert first_opt["type"] == "model_substitution"
        assert first_opt["current_model"] == "claude-3-opus"
        assert first_opt["recommended_model"] == "claude-3-sonnet"
        assert first_opt["potential_savings"] == 15.0
        assert first_opt["auto_applicable"] == True
    
    @patch('src.api.routers.model_routing.get_cost_optimizer')
    def test_apply_cost_optimization(self, mock_get_optimizer, client, mock_cost_optimizer):
        """Test apply cost optimization endpoint."""
        mock_get_optimizer.return_value = mock_cost_optimizer
        
        # Mock optimization to apply
        mock_optimization = Mock(
            optimization_type=Mock(value="model_substitution"),
            current_model="claude-3-opus",
            recommended_model="claude-3-sonnet",
            auto_applicable=True
        )
        mock_cost_optimizer.generate_optimizations.return_value = [mock_optimization]
        
        # Mock application result
        mock_result = {
            "success": True,
            "optimization": mock_optimization,
            "application_record": {"timestamp": datetime.utcnow()}
        }
        mock_cost_optimizer.apply_optimization.return_value = mock_result
        
        request_data = {"optimization_index": 0}
        
        response = client.post("/model-routing/cost/optimizations/apply", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "application_result" in data
        assert data["application_result"]["success"] == True
    
    @patch('src.api.routers.model_routing.get_cost_optimizer')
    def test_apply_cost_optimization_invalid_index(self, mock_get_optimizer, client, mock_cost_optimizer):
        """Test apply cost optimization with invalid index."""
        mock_get_optimizer.return_value = mock_cost_optimizer
        mock_cost_optimizer.generate_optimizations.return_value = []  # No optimizations
        
        request_data = {"optimization_index": 0}
        
        response = client.post("/model-routing/cost/optimizations/apply", json=request_data)
        
        assert response.status_code == 400
        assert "Invalid optimization index" in response.json()["detail"]
    
    @patch('src.api.routers.model_routing.get_cost_optimizer')
    def test_get_cost_forecast(self, mock_get_optimizer, client, mock_cost_optimizer):
        """Test get cost forecast endpoint."""
        mock_get_optimizer.return_value = mock_cost_optimizer
        
        mock_forecast = Mock(
            daily_forecast=[100.0, 105.0, 110.0],
            weekly_forecast=[700.0, 735.0],
            monthly_forecast=[3000.0],
            trend_direction="increasing",
            confidence_interval=(95.0, 115.0),
            forecast_accuracy=0.85
        )
        mock_cost_optimizer.generate_cost_forecast.return_value = mock_forecast
        
        response = client.get("/model-routing/cost/forecast?days=30")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "forecast" in data
        forecast = data["forecast"]
        assert forecast["days"] == 30
        assert forecast["daily_forecast"] == [100.0, 105.0, 110.0]
        assert forecast["trend_direction"] == "increasing"
        assert forecast["confidence_interval"] == [95.0, 115.0]
        assert forecast["forecast_accuracy"] == 0.85
    
    @patch('src.api.routers.model_routing.get_cost_optimizer')
    def test_get_cost_alerts(self, mock_get_optimizer, client, mock_cost_optimizer):
        """Test get cost alerts endpoint."""
        mock_get_optimizer.return_value = mock_cost_optimizer
        
        mock_alerts = [
            {
                "level": Mock(value="warning"),
                "type": "daily_budget",
                "message": "Daily budget 80% reached",
                "usage_percentage": 80.0,
                "timestamp": datetime.utcnow()
            },
            {
                "level": "critical",  # Test string level too
                "type": "weekly_budget",
                "message": "Weekly budget 90% exceeded",
                "usage_percentage": 90.0,
                "timestamp": datetime.utcnow()
            }
        ]
        mock_cost_optimizer.check_budget_alerts.return_value = mock_alerts
        
        response = client.get("/model-routing/cost/alerts")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "alerts" in data
        assert "alert_count" in data
        assert "has_critical_alerts" in data
        
        assert data["alert_count"] == 2
        assert data["has_critical_alerts"] == True
        
        alerts = data["alerts"]
        assert len(alerts) == 2
        assert alerts[0]["level"] == "warning"
        assert alerts[0]["type"] == "daily_budget"
        assert alerts[1]["level"] == "critical"
    
    @patch('src.api.routers.model_routing.get_model_router')
    def test_get_model_health(self, mock_get_router, client, mock_model_router):
        """Test get model health endpoint."""
        mock_get_router.return_value = mock_model_router
        
        # Mock health check results
        def mock_health_check(model_name):
            return model_name != "claude-3-opus"  # Opus is unhealthy
        
        mock_model_router._is_model_healthy.side_effect = mock_health_check
        
        response = client.get("/model-routing/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "overall_health" in data
        assert "model_health" in data
        assert "timestamp" in data
        
        # Should reflect that not all models are healthy
        model_health = data["model_health"]
        assert "claude-3-haiku" in model_health
        assert "claude-3-sonnet" in model_health
        
        # Check individual health status
        assert model_health["claude-3-haiku"]["healthy"] == True
        assert model_health["claude-3-sonnet"]["healthy"] == True
    
    def test_get_routing_strategies(self, client):
        """Test get routing strategies endpoint."""
        response = client.get("/model-routing/strategies")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "strategies" in data
        assert "default_strategy" in data
        
        strategies = data["strategies"]
        assert "cost_optimized" in strategies
        assert "latency_optimized" in strategies
        assert "accuracy_optimized" in strategies
        assert "balanced" in strategies
        
        # Check strategy details
        cost_opt = strategies["cost_optimized"]
        assert "name" in cost_opt
        assert "description" in cost_opt
        assert "use_case" in cost_opt
        
        assert data["default_strategy"] == "balanced"
    
    def test_get_model_tiers(self, client):
        """Test get model tiers endpoint."""
        response = client.get("/model-routing/tiers")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tiers" in data
        assert "tier_count" in data
        
        tiers = data["tiers"]
        assert "economy" in tiers
        assert "standard" in tiers
        assert "premium" in tiers
        
        # Check tier details
        economy = tiers["economy"]
        assert "name" in economy
        assert "description" in economy
        assert "typical_models" in economy
        assert "use_cases" in economy
        
        assert data["tier_count"] == 3


class TestModelRoutingAPIValidation:
    """Test API request validation."""
    
    def test_route_request_missing_task_type(self, client):
        """Test routing request with missing required field."""
        request_data = {
            "incident_severity": "medium"
            # Missing task_type
        }
        
        response = client.post("/model-routing/route", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_route_request_invalid_accuracy(self, client):
        """Test routing request with invalid accuracy value."""
        request_data = {
            "task_type": "diagnosis",
            "required_accuracy": 1.5  # Invalid: > 1.0
        }
        
        response = client.post("/model-routing/route", json=request_data)
        
        assert response.status_code == 422
    
    def test_budget_request_negative_limit(self, client):
        """Test budget request with negative values."""
        budget_data = {
            "daily_limit": -100.0,  # Invalid: negative
            "weekly_limit": 600.0,
            "monthly_limit": 2400.0
        }
        
        response = client.post("/model-routing/cost/budget", json=budget_data)
        
        assert response.status_code == 422
    
    def test_usage_record_missing_fields(self, client):
        """Test usage record with missing required fields."""
        usage_data = {
            "model_name": "claude-3-sonnet",
            # Missing other required fields
        }
        
        response = client.post("/model-routing/usage/record", json=usage_data)
        
        assert response.status_code == 422
    
    def test_forecast_invalid_days(self, client):
        """Test forecast request with invalid days parameter."""
        response = client.get("/model-routing/cost/forecast?days=0")  # Invalid: <= 0
        
        assert response.status_code == 422
        
        response = client.get("/model-routing/cost/forecast?days=100")  # Invalid: > 90
        
        assert response.status_code == 422