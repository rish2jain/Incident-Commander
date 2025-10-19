"""
Integration tests for Phase 1 - Platform Stabilization features.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.services.aws import AWSServiceFactory, retry_with_backoff, RetryConfig
from src.services.localstack_fixtures import LocalStackManager, get_localstack_manager
from src.services.auth_middleware import (
    SecurityConfig, JWTManager, APIKeyManager, RateLimiter
)
from src.services.finops_controller import FinOpsController, CostCategory, ServiceTier
from src.services.opentelemetry_integration import OpenTelemetryManager
from src.services.metrics_endpoint import MetricsEndpointService


class TestAWSServiceFactory:
    """Test AWS service factory with retry logic and connection pooling."""
    
    @pytest.fixture
    def aws_factory(self):
        """Create AWS service factory for testing."""
        return AWSServiceFactory()
    
    @pytest.mark.asyncio
    async def test_create_client_with_retry(self, aws_factory):
        """Test client creation with retry logic."""
        # Mock successful client creation
        with patch('aioboto3.Session') as mock_session:
            mock_client = AsyncMock()
            mock_session.return_value.client.return_value = mock_client
            
            client = await aws_factory.create_client('dynamodb')
            
            assert client is not None
            assert client in aws_factory._active_clients
    
    @pytest.mark.asyncio
    async def test_missing_aws_clients(self, aws_factory):
        """Test that missing AWS clients are now implemented."""
        # Test Step Functions client
        with patch('aioboto3.Session') as mock_session:
            mock_client = AsyncMock()
            mock_session.return_value.client.return_value = mock_client
            
            stepfunctions_client = await aws_factory.get_stepfunctions_client()
            assert stepfunctions_client is not None
            
            inspector_client = await aws_factory.get_inspector_client()
            assert inspector_client is not None
            
            cost_explorer_client = await aws_factory.get_cost_explorer_client()
            assert cost_explorer_client is not None
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff(self):
        """Test retry logic with exponential backoff."""
        call_count = 0
        
        async def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"
        
        retry_config = RetryConfig(max_retries=3, base_delay=0.1)
        result = await retry_with_backoff(failing_function, retry_config)
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_health_check_service(self, aws_factory):
        """Test service-specific health checks."""
        with patch.object(aws_factory, 'get_stepfunctions_client') as mock_client:
            mock_sf_client = AsyncMock()
            mock_sf_client.list_state_machines.return_value = {'stateMachines': []}
            mock_client.return_value = mock_sf_client
            
            is_healthy = await aws_factory.health_check_service('stepfunctions')
            assert is_healthy is True
            
            mock_sf_client.list_state_machines.assert_called_once()


class TestLocalStackIntegration:
    """Test LocalStack fixtures and offline testing infrastructure."""
    
    @pytest.fixture
    def localstack_manager(self):
        """Create LocalStack manager for testing."""
        return LocalStackManager()
    
    def test_localstack_detection(self, localstack_manager):
        """Test LocalStack environment detection."""
        # Should detect LocalStack from localhost endpoint
        assert localstack_manager.is_localstack is True
    
    @pytest.mark.asyncio
    async def test_dynamodb_initialization(self, localstack_manager):
        """Test DynamoDB table initialization in LocalStack."""
        with patch.object(localstack_manager, 'get_service_factory') as mock_factory:
            mock_client = AsyncMock()
            mock_client.describe_table.side_effect = Exception("ResourceNotFoundException")
            mock_client.create_table.return_value = None
            
            mock_service_factory = Mock()
            mock_service_factory.get_dynamodb_client.return_value = mock_client
            mock_factory.return_value = mock_service_factory
            
            await localstack_manager.initialize_dynamodb()
            
            assert 'dynamodb' in localstack_manager._initialized_services
    
    @pytest.mark.asyncio
    async def test_kinesis_initialization(self, localstack_manager):
        """Test Kinesis stream initialization in LocalStack."""
        with patch.object(localstack_manager, 'get_service_factory') as mock_factory:
            mock_client = AsyncMock()
            mock_client.describe_stream.side_effect = Exception("ResourceNotFoundException")
            mock_client.create_stream.return_value = None
            
            mock_service_factory = Mock()
            mock_service_factory.get_kinesis_client.return_value = mock_client
            mock_factory.return_value = mock_service_factory
            
            await localstack_manager.initialize_kinesis()
            
            assert 'kinesis' in localstack_manager._initialized_services
    
    @pytest.mark.asyncio
    async def test_step_functions_initialization(self, localstack_manager):
        """Test Step Functions state machine initialization in LocalStack."""
        with patch.object(localstack_manager, 'get_service_factory') as mock_factory:
            mock_client = AsyncMock()
            mock_client.describe_state_machine.side_effect = Exception("StateMachineDoesNotExist")
            mock_client.create_state_machine.return_value = None
            
            mock_service_factory = Mock()
            mock_service_factory.get_stepfunctions_client.return_value = mock_client
            mock_factory.return_value = mock_service_factory
            
            await localstack_manager.initialize_step_functions()
            
            assert 'stepfunctions' in localstack_manager._initialized_services


class TestAuthenticationMiddleware:
    """Test authentication and authorization middleware."""
    
    @pytest.fixture
    def security_config(self):
        """Create security configuration for testing."""
        return SecurityConfig(
            jwt_secret_key="test-secret-key",
            api_rate_limit=60,
            cors_origins=["http://localhost:3000"],
            require_auth=True,
            demo_api_key="test-demo-key"
        )
    
    @pytest.fixture
    def jwt_manager(self, security_config):
        """Create JWT manager for testing."""
        return JWTManager(security_config)
    
    @pytest.fixture
    def api_key_manager(self, security_config):
        """Create API key manager for testing."""
        return APIKeyManager(security_config)
    
    @pytest.fixture
    def rate_limiter(self):
        """Create rate limiter for testing."""
        return RateLimiter(requests_per_minute=60)
    
    def test_jwt_token_creation(self, jwt_manager):
        """Test JWT token creation and verification."""
        user_id = "test-user"
        scopes = ["read", "write"]
        
        token = jwt_manager.create_token(user_id, scopes)
        assert token is not None
        
        payload = jwt_manager.verify_token(token)
        assert payload['sub'] == user_id
        assert payload['scopes'] == scopes
    
    def test_api_key_generation(self, api_key_manager):
        """Test API key generation and verification."""
        name = "test-service"
        scopes = ["demo", "read"]
        
        api_key = api_key_manager.generate_api_key(name, scopes)
        assert api_key is not None
        
        key_data = api_key_manager.verify_api_key(api_key)
        assert key_data['name'] == name
        assert key_data['scopes'] == scopes
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, rate_limiter):
        """Test rate limiting functionality."""
        identifier = "test-client"
        
        # Should allow initial requests
        for _ in range(5):
            allowed = await rate_limiter.is_allowed(identifier)
            assert allowed is True
        
        # Should have remaining requests
        remaining = await rate_limiter.get_remaining_requests(identifier)
        assert remaining == 55  # 60 - 5


class TestFinOpsIntegration:
    """Test FinOps controller integration."""
    
    @pytest.fixture
    def finops_controller(self):
        """Create FinOps controller for testing."""
        return FinOpsController()
    
    @pytest.mark.asyncio
    async def test_budget_limit_checking(self, finops_controller):
        """Test budget limit checking functionality."""
        from decimal import Decimal
        
        category = CostCategory.BEDROCK_INFERENCE
        estimated_cost = Decimal('50.00')
        
        # Should be within budget initially
        within_budget = await finops_controller.check_budget_limits(category, estimated_cost)
        assert within_budget is True
    
    @pytest.mark.asyncio
    async def test_adaptive_model_routing(self, finops_controller):
        """Test adaptive model routing based on complexity and cost."""
        task_complexity = "simple"
        context = {"estimated_input_tokens": 500, "estimated_output_tokens": 200}
        
        selected_model = await finops_controller.adaptive_model_routing(task_complexity, context)
        
        # Should select Haiku for simple tasks
        assert "haiku" in selected_model.lower()
    
    @pytest.mark.asyncio
    async def test_dynamic_detection_sampling(self, finops_controller):
        """Test dynamic detection sampling based on risk and cost."""
        incident_risk_level = "high"
        system_load = 0.7
        
        sampling_config = await finops_controller.dynamic_detection_sampling(
            incident_risk_level, system_load
        )
        
        assert "sampling_rate" in sampling_config
        assert "sampling_interval_seconds" in sampling_config
        assert sampling_config["risk_level"] == incident_risk_level
    
    def test_finops_metrics(self, finops_controller):
        """Test FinOps metrics collection."""
        metrics = finops_controller.get_finops_metrics()
        
        assert "budget_status" in metrics
        assert "optimization_metrics" in metrics
        assert "model_routing" in metrics
        assert "cost_categories" in metrics


class TestObservabilityIntegration:
    """Test OpenTelemetry and observability integration."""
    
    @pytest.fixture
    def otel_manager(self):
        """Create OpenTelemetry manager for testing."""
        manager = OpenTelemetryManager()
        # Don't initialize for testing to avoid conflicts
        return manager
    
    def test_otel_manager_creation(self, otel_manager):
        """Test OpenTelemetry manager creation."""
        assert otel_manager is not None
        assert otel_manager.initialized is False
    
    def test_metric_instruments_creation(self, otel_manager):
        """Test metric instruments are properly defined."""
        # Initialize to create instruments
        otel_manager.initialize()
        
        assert otel_manager.incident_counter is not None
        assert otel_manager.agent_duration_histogram is not None
        assert otel_manager.consensus_latency_histogram is not None
        assert otel_manager.business_impact_gauge is not None
        assert otel_manager.cost_gauge is not None
    
    def test_observability_metrics(self, otel_manager):
        """Test observability metrics collection."""
        metrics = otel_manager.get_observability_metrics()
        
        assert "tracing" in metrics
        assert "metrics" in metrics
        assert "instrumentation" in metrics


class TestMetricsEndpoint:
    """Test metrics endpoint service."""
    
    @pytest.fixture
    def metrics_service(self):
        """Create metrics endpoint service for testing."""
        return MetricsEndpointService()
    
    @pytest.mark.asyncio
    async def test_metrics_collection(self, metrics_service):
        """Test metrics collection functionality."""
        # Mock the collection process
        with patch.object(metrics_service, '_collect_finops_metrics') as mock_finops, \
             patch.object(metrics_service, '_collect_system_health_metrics') as mock_health:
            
            mock_finops.return_value = None
            mock_health.return_value = None
            
            await metrics_service.collect_all_metrics()
            
            mock_finops.assert_called_once()
            mock_health.assert_called_once()
    
    def test_prometheus_metrics_format(self, metrics_service):
        """Test Prometheus metrics format."""
        metrics_content = metrics_service.get_prometheus_metrics()
        
        # Should return valid Prometheus format
        assert isinstance(metrics_content, str)
        # Basic validation - should contain metric names
        assert len(metrics_content) > 0
    
    def test_metrics_summary(self, metrics_service):
        """Test metrics summary for dashboards."""
        # Add a mock snapshot
        from src.services.metrics_endpoint import MetricSnapshot
        
        snapshot = MetricSnapshot(
            timestamp=datetime.utcnow(),
            incidents_total=10,
            incidents_resolved=9,
            mttr_seconds=85.7,
            business_impact_usd=5000.0,
            operational_cost_usd=47.50,
            agent_health_scores={"detection": 0.98, "diagnosis": 0.95},
            guardrail_violations=1,
            circuit_breaker_states={"bedrock": "closed"},
            spend_caps_status={"bedrock_inference": 45.2}
        )
        
        metrics_service.metrics_history.append(snapshot)
        
        summary = metrics_service.get_metrics_summary()
        
        assert "incidents" in summary
        assert "performance" in summary
        assert "business_impact" in summary
        assert "agent_health" in summary


class TestEndToEndIntegration:
    """Test end-to-end integration of all Phase 1 components."""
    
    @pytest.mark.asyncio
    async def test_complete_phase1_workflow(self):
        """Test complete Phase 1 workflow integration."""
        # Initialize LocalStack manager
        localstack_manager = get_localstack_manager()
        assert localstack_manager is not None
        
        # Create AWS service factory
        aws_factory = AWSServiceFactory()
        
        # Test health check
        with patch.object(aws_factory, 'create_client') as mock_create:
            mock_client = AsyncMock()
            mock_client.get_caller_identity.return_value = {"Account": "123456789012"}
            mock_create.return_value = mock_client
            
            is_healthy = await aws_factory.health_check()
            assert is_healthy is True
        
        # Test authentication
        security_config = SecurityConfig(
            jwt_secret_key="test-key",
            require_auth=False  # Disable for testing
        )
        
        jwt_manager = JWTManager(security_config)
        token = jwt_manager.create_token("test-user", ["read"])
        payload = jwt_manager.verify_token(token)
        assert payload['sub'] == "test-user"
        
        # Test FinOps
        finops = FinOpsController()
        metrics = finops.get_finops_metrics()
        assert "budget_status" in metrics
        
        # Test observability
        otel_manager = OpenTelemetryManager()
        otel_metrics = otel_manager.get_observability_metrics()
        assert "tracing" in otel_metrics
        
        # Test metrics endpoint
        metrics_service = MetricsEndpointService()
        summary = metrics_service.get_metrics_summary()
        # Should handle empty metrics gracefully
        assert "error" in summary or "incidents" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])