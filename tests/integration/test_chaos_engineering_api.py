"""
Integration tests for Chaos Engineering API

Tests the complete chaos engineering API endpoints including:
- Experiment creation and execution
- Real-time monitoring and status
- Resilience reporting
- Emergency stop functionality
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.main import app
from src.services.chaos_engineering_framework import (
    ChaosEngineeringFramework,
    ChaosExperimentType,
    FailureMode
)


class TestChaosEngineeringAPI:
    """Test chaos engineering API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_services(self):
        """Mock services for testing."""
        with patch('src.api.dependencies.get_services') as mock_get_services:
            mock_services = AsyncMock()
            mock_services.coordinator = AsyncMock()
            mock_services.coordinator.get_agent_health_status.return_value = {
                "detection_agent": {"is_healthy": True},
                "diagnosis_agent": {"is_healthy": True}
            }
            mock_get_services.return_value = mock_services
            yield mock_services
    
    def test_list_chaos_experiments(self, client):
        """Test listing available chaos experiments."""
        response = client.get("/chaos/experiments")
        
        assert response.status_code == 200
        experiments = response.json()
        
        assert isinstance(experiments, list)
        assert len(experiments) > 0
        
        # Check experiment structure
        experiment = experiments[0]
        required_fields = {
            "name", "type", "failure_mode", "target_components",
            "duration_seconds", "intensity", "description", "blast_radius"
        }
        assert set(experiment.keys()).issuperset(required_fields)
    
    def test_create_chaos_experiment(self, client):
        """Test creating a new chaos experiment."""
        experiment_data = {
            "name": "test_custom_experiment",
            "experiment_type": "agent_failure",
            "failure_mode": "complete_failure",
            "target_components": ["test_agent"],
            "duration_seconds": 120,
            "intensity": 0.8,
            "description": "Custom test experiment",
            "expected_behavior": "System should handle failure gracefully",
            "success_criteria": {
                "recovery_time": 60.0,
                "availability": 0.7
            },
            "blast_radius": "single_agent"
        }
        
        response = client.post("/chaos/experiments", json=experiment_data)
        
        assert response.status_code == 200
        result = response.json()
        
        assert result["experiment_id"] == "test_custom_experiment"
        assert result["status"] == "created"
        assert "message" in result
    
    def test_create_experiment_invalid_type(self, client):
        """Test creating experiment with invalid type."""
        experiment_data = {
            "name": "test_invalid",
            "experiment_type": "invalid_type",
            "failure_mode": "complete_failure",
            "target_components": ["test_agent"],
            "duration_seconds": 120,
            "intensity": 0.8,
            "blast_radius": "single_agent"
        }
        
        response = client.post("/chaos/experiments", json=experiment_data)
        
        assert response.status_code == 400
        assert "Invalid experiment type" in response.json()["detail"]
    
    def test_execute_chaos_experiment(self, client, mock_services):
        """Test executing a chaos experiment."""
        # First, get available experiments
        experiments_response = client.get("/chaos/experiments")
        experiments = experiments_response.json()
        experiment_name = experiments[0]["name"]
        
        # Mock the experiment execution
        with patch('src.api.routers.chaos_engineering.get_chaos_framework') as mock_framework:
            framework = AsyncMock()
            mock_framework.return_value = framework
            
            # Mock experiment lookup
            mock_experiment = AsyncMock()
            mock_experiment.name = experiment_name
            framework.experiments = [mock_experiment]
            framework.active_injections = {}
            
            # Mock experiment result
            mock_result = AsyncMock()
            mock_result.experiment = mock_experiment
            mock_result.start_time = datetime.utcnow()
            mock_result.end_time = datetime.utcnow()
            mock_result.success = True
            mock_result.recovery_metrics = {"max_recovery_time": 30.0}
            mock_result.system_behavior = {"failure_detection_time": 15.0}
            mock_result.lessons_learned = ["Good recovery time"]
            mock_result.recommendations = ["Continue monitoring"]
            
            framework.run_chaos_experiment.return_value = mock_result
            
            response = client.post(f"/chaos/experiments/{experiment_name}/execute")
            
            assert response.status_code == 200
            result = response.json()
            
            assert result["experiment_id"] == experiment_name
            assert result["status"] == "completed"
            assert result["success"] is True
            assert "recovery_metrics" in result
            assert "lessons_learned" in result
    
    def test_execute_nonexistent_experiment(self, client, mock_services):
        """Test executing a non-existent experiment."""
        with patch('src.api.routers.chaos_engineering.get_chaos_framework') as mock_framework:
            framework = AsyncMock()
            mock_framework.return_value = framework
            framework.experiments = []
            
            response = client.post("/chaos/experiments/nonexistent/execute")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
    
    def test_get_experiment_status_running(self, client):
        """Test getting status of a running experiment."""
        with patch('src.api.routers.chaos_engineering.get_chaos_framework') as mock_framework:
            framework = AsyncMock()
            mock_framework.return_value = framework
            
            # Mock active injection
            mock_injection = AsyncMock()
            mock_injection.start_time = datetime.utcnow()
            mock_injection.affected_components = ["test_agent"]
            mock_injection.injection_state = {"test": "data"}
            
            framework.active_injections = {"test_experiment": mock_injection}
            
            response = client.get("/chaos/experiments/test_experiment/status")
            
            assert response.status_code == 200
            result = response.json()
            
            assert result["experiment_name"] == "test_experiment"
            assert result["status"] == "running"
            assert "start_time" in result
            assert "duration_seconds" in result
    
    def test_get_experiment_status_completed(self, client):
        """Test getting status of a completed experiment."""
        with patch('src.api.routers.chaos_engineering.get_chaos_framework') as mock_framework:
            framework = AsyncMock()
            mock_framework.return_value = framework
            framework.active_injections = {}
            
            # Mock completed experiment result
            mock_result = AsyncMock()
            mock_result.experiment.name = "test_experiment"
            mock_result.start_time = datetime.utcnow()
            mock_result.end_time = datetime.utcnow()
            mock_result.success = True
            mock_result.recovery_metrics = {"recovery_time": 30.0}
            
            framework.experiment_results = [mock_result]
            
            response = client.get("/chaos/experiments/test_experiment/status")
            
            assert response.status_code == 200
            result = response.json()
            
            assert result["experiment_name"] == "test_experiment"
            assert result["status"] == "completed"
            assert result["success"] is True
    
    def test_stop_chaos_experiment(self, client):
        """Test stopping a running chaos experiment."""
        with patch('src.api.routers.chaos_engineering.get_chaos_framework') as mock_framework:
            framework = AsyncMock()
            mock_framework.return_value = framework
            
            # Mock active injection
            mock_injection = AsyncMock()
            mock_injection.experiment = AsyncMock()
            framework.active_injections = {"test_experiment": mock_injection}
            framework._recover_from_failure = AsyncMock()
            
            response = client.post("/chaos/experiments/test_experiment/stop")
            
            assert response.status_code == 200
            result = response.json()
            
            assert result["experiment_name"] == "test_experiment"
            assert result["status"] == "stopped"
            assert "message" in result
    
    def test_stop_nonexistent_experiment(self, client):
        """Test stopping a non-existent experiment."""
        with patch('src.api.routers.chaos_engineering.get_chaos_framework') as mock_framework:
            framework = AsyncMock()
            mock_framework.return_value = framework
            framework.active_injections = {}
            
            response = client.post("/chaos/experiments/nonexistent/stop")
            
            assert response.status_code == 404
            assert "No active experiment" in response.json()["detail"]
    
    def test_execute_chaos_suite(self, client, mock_services):
        """Test executing the chaos test suite."""
        suite_request = {
            "experiment_filter": ["test_experiment"],
            "blast_radius_filter": "single_agent",
            "max_concurrent": 1
        }
        
        with patch('src.api.routers.chaos_engineering.get_chaos_framework') as mock_framework:
            framework = AsyncMock()
            mock_framework.return_value = framework
            framework.emergency_stop_active = False
            
            # Mock experiments
            mock_experiment = AsyncMock()
            mock_experiment.name = "test_experiment"
            mock_experiment.blast_radius = "single_agent"
            framework.experiments = [mock_experiment]
            
            response = client.post("/chaos/suite/execute", json=suite_request)
            
            assert response.status_code == 200
            result = response.json()
            
            assert "suite_id" in result
            assert result["status"] == "started"
            assert result["total_experiments"] == 1
            assert "estimated_duration_minutes" in result
    
    def test_get_experiment_results(self, client):
        """Test getting experiment results."""
        with patch('src.api.routers.chaos_engineering.get_chaos_framework') as mock_framework:
            framework = AsyncMock()
            mock_framework.return_value = framework
            
            # Mock experiment results
            mock_result = AsyncMock()
            mock_result.experiment.name = "test_experiment"
            mock_result.experiment.experiment_type.value = "agent_failure"
            mock_result.start_time = datetime.utcnow()
            mock_result.end_time = datetime.utcnow()
            mock_result.success = True
            mock_result.recovery_metrics = {}
            mock_result.system_behavior = {}
            mock_result.lessons_learned = []
            mock_result.recommendations = []
            
            framework.experiment_results = [mock_result]
            
            response = client.get("/chaos/results?limit=5&success_only=true")
            
            assert response.status_code == 200
            results = response.json()
            
            assert isinstance(results, list)
            assert len(results) == 1
            assert results[0]["name"] == "test_experiment"
            assert results[0]["success"] is True
    
    def test_generate_resilience_report(self, client):
        """Test generating resilience report."""
        with patch('src.api.routers.chaos_engineering.get_chaos_framework') as mock_framework:
            framework = AsyncMock()
            mock_framework.return_value = framework
            
            # Mock experiment results
            framework.experiment_results = [AsyncMock()]
            
            # Mock report generation
            mock_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_experiments": 1,
                "successful_experiments": 1,
                "failed_experiments": 0,
                "resilience_summary": {"recovery_time": {"avg_seconds": 30.0}},
                "lessons_learned": [{"lesson": "Good performance", "frequency": 1}],
                "recommendations": [{"recommendation": "Continue", "priority": 1}]
            }
            framework.generate_resilience_report.return_value = mock_report
            
            response = client.get("/chaos/resilience-report")
            
            assert response.status_code == 200
            report = response.json()
            
            assert report["total_experiments"] == 1
            assert report["successful_experiments"] == 1
            assert "resilience_summary" in report
            assert "lessons_learned" in report
            assert "recommendations" in report
    
    def test_get_active_experiments(self, client):
        """Test getting active experiments."""
        with patch('src.api.routers.chaos_engineering.get_chaos_framework') as mock_framework:
            framework = AsyncMock()
            mock_framework.return_value = framework
            
            # Mock active injection
            mock_injection = AsyncMock()
            mock_injection.start_time = datetime.utcnow()
            mock_injection.affected_components = ["test_agent"]
            mock_injection.experiment.experiment_type.value = "agent_failure"
            mock_injection.experiment.failure_mode.value = "complete_failure"
            mock_injection.experiment.intensity = 1.0
            
            framework.active_injections = {"test_experiment": mock_injection}
            framework.emergency_stop_active = False
            
            response = client.get("/chaos/active-experiments")
            
            assert response.status_code == 200
            result = response.json()
            
            assert result["total_active"] == 1
            assert result["emergency_stop_active"] is False
            assert len(result["active_experiments"]) == 1
            
            active_exp = result["active_experiments"][0]
            assert active_exp["experiment_name"] == "test_experiment"
            assert "start_time" in active_exp
            assert "duration_seconds" in active_exp
    
    def test_trigger_emergency_stop(self, client):
        """Test triggering emergency stop."""
        with patch('src.api.routers.chaos_engineering.get_chaos_framework') as mock_framework:
            framework = AsyncMock()
            mock_framework.return_value = framework
            
            # Mock active injections
            framework.active_injections = {"test1": AsyncMock(), "test2": AsyncMock()}
            framework.experiments = [AsyncMock()]
            framework._trigger_emergency_stop = AsyncMock()
            
            response = client.post("/chaos/emergency-stop")
            
            assert response.status_code == 200
            result = response.json()
            
            assert result["status"] == "emergency_stop_activated"
            assert result["stopped_experiments"] == 2
            assert "message" in result
    
    def test_get_chaos_metrics(self, client):
        """Test getting chaos engineering metrics."""
        with patch('src.api.routers.chaos_engineering.get_chaos_framework') as mock_framework:
            framework = AsyncMock()
            mock_framework.return_value = framework
            
            # Mock experiment results
            mock_result1 = AsyncMock()
            mock_result1.success = True
            mock_result1.recovery_metrics = {"max_recovery_time": 30.0}
            mock_result1.experiment.experiment_type.value = "agent_failure"
            
            mock_result2 = AsyncMock()
            mock_result2.success = False
            mock_result2.recovery_metrics = {"max_recovery_time": 90.0}
            mock_result2.experiment.experiment_type.value = "network_partition"
            
            framework.experiment_results = [mock_result1, mock_result2]
            framework.active_injections = {}
            framework.emergency_stop_active = False
            
            response = client.get("/chaos/metrics")
            
            assert response.status_code == 200
            metrics = response.json()
            
            assert metrics["total_experiments_run"] == 2
            assert metrics["success_rate"] == 0.5
            assert metrics["average_recovery_time_seconds"] == 60.0
            assert metrics["active_experiments"] == 0
            assert "experiment_type_distribution" in metrics
            assert "available_experiment_types" in metrics
    
    def test_get_chaos_framework_health(self, client):
        """Test getting chaos framework health status."""
        with patch('src.api.routers.chaos_engineering.get_chaos_framework') as mock_framework:
            framework = AsyncMock()
            mock_framework.return_value = framework
            
            framework.emergency_stop_active = False
            framework.experiments = [AsyncMock(), AsyncMock()]
            framework.active_injections = {}
            framework.max_concurrent_experiments = 3
            framework.safety_thresholds = {"max_error_rate": 0.5}
            framework.experiment_results = [AsyncMock()]
            
            response = client.get("/chaos/health")
            
            assert response.status_code == 200
            health = response.json()
            
            assert health["framework_status"] == "healthy"
            assert health["total_experiments_available"] == 2
            assert health["active_experiments"] == 0
            assert health["max_concurrent_experiments"] == 3
            assert "safety_thresholds" in health
            assert "timestamp" in health


class TestChaosEngineeringIntegration:
    """Test chaos engineering integration with system components."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_chaos_framework_initialization(self, client):
        """Test chaos framework initializes properly with API."""
        response = client.get("/chaos/health")
        
        assert response.status_code == 200
        health = response.json()
        
        assert "framework_status" in health
        assert health["total_experiments_available"] > 0
    
    def test_experiment_types_consistency(self, client):
        """Test experiment types are consistent between framework and API."""
        # Get available experiments
        experiments_response = client.get("/chaos/experiments")
        experiments = experiments_response.json()
        
        # Get metrics with available types
        metrics_response = client.get("/chaos/metrics")
        metrics = metrics_response.json()
        
        # Check consistency
        experiment_types_from_experiments = {exp["type"] for exp in experiments}
        available_types_from_metrics = set(metrics["available_experiment_types"])
        
        assert experiment_types_from_experiments.issubset(available_types_from_metrics)
    
    def test_api_error_handling(self, client):
        """Test API error handling for various scenarios."""
        # Test invalid experiment execution
        response = client.post("/chaos/experiments/invalid_experiment/execute")
        assert response.status_code in [404, 500]
        
        # Test invalid experiment status
        response = client.get("/chaos/experiments/invalid_experiment/status")
        assert response.status_code == 404
        
        # Test stopping non-existent experiment
        response = client.post("/chaos/experiments/invalid_experiment/stop")
        assert response.status_code in [404, 500]
    
    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, client):
        """Test handling of concurrent API requests."""
        # Test multiple simultaneous requests to different endpoints
        responses = await asyncio.gather(
            asyncio.to_thread(client.get, "/chaos/experiments"),
            asyncio.to_thread(client.get, "/chaos/metrics"),
            asyncio.to_thread(client.get, "/chaos/health"),
            asyncio.to_thread(client.get, "/chaos/active-experiments"),
            return_exceptions=True
        )
        
        # All requests should succeed
        for response in responses:
            if not isinstance(response, Exception):
                assert response.status_code == 200


class TestChaosEngineeringValidation:
    """Test validation and edge cases for chaos engineering API."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_experiment_creation_validation(self, client):
        """Test validation of experiment creation parameters."""
        # Test missing required fields
        invalid_data = {
            "name": "test",
            # Missing experiment_type
            "failure_mode": "complete_failure",
            "target_components": ["test"]
        }
        
        response = client.post("/chaos/experiments", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_experiment_duration_validation(self, client):
        """Test validation of experiment duration limits."""
        # Test duration too short
        short_duration_data = {
            "name": "test_short",
            "experiment_type": "agent_failure",
            "failure_mode": "complete_failure",
            "target_components": ["test"],
            "duration_seconds": 30,  # Below minimum of 60
            "intensity": 0.5,
            "blast_radius": "single_agent"
        }
        
        response = client.post("/chaos/experiments", json=short_duration_data)
        assert response.status_code == 422
        
        # Test duration too long
        long_duration_data = {
            "name": "test_long",
            "experiment_type": "agent_failure",
            "failure_mode": "complete_failure",
            "target_components": ["test"],
            "duration_seconds": 2000,  # Above maximum of 1800
            "intensity": 0.5,
            "blast_radius": "single_agent"
        }
        
        response = client.post("/chaos/experiments", json=long_duration_data)
        assert response.status_code == 422
    
    def test_experiment_intensity_validation(self, client):
        """Test validation of experiment intensity limits."""
        # Test intensity out of range
        invalid_intensity_data = {
            "name": "test_intensity",
            "experiment_type": "agent_failure",
            "failure_mode": "complete_failure",
            "target_components": ["test"],
            "duration_seconds": 120,
            "intensity": 1.5,  # Above maximum of 1.0
            "blast_radius": "single_agent"
        }
        
        response = client.post("/chaos/experiments", json=invalid_intensity_data)
        assert response.status_code == 422
    
    def test_results_pagination(self, client):
        """Test results pagination and filtering."""
        # Test limit parameter
        response = client.get("/chaos/results?limit=5")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) <= 5
        
        # Test filtering by experiment type
        response = client.get("/chaos/results?experiment_type=agent_failure")
        assert response.status_code == 200
        
        # Test success-only filter
        response = client.get("/chaos/results?success_only=true")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__])