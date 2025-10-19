"""
Unit tests for deployment pipeline functionality.

Tests deployment automation, validation, and multi-environment deployment.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.services.deployment_pipeline import (
    DeploymentPipeline, Environment, DeploymentStatus, 
    AWSResource, ValidationResult, RollbackPlan, DeploymentResult
)
from src.services.aws import AWSServiceFactory


@pytest.fixture
def mock_aws_factory():
    """Mock AWS service factory."""
    factory = Mock(spec=AWSServiceFactory)
    factory.create_client = AsyncMock()
    factory.create_resource = AsyncMock()
    return factory


@pytest.fixture
def deployment_pipeline(mock_aws_factory):
    """Create deployment pipeline instance."""
    return DeploymentPipeline(mock_aws_factory)


@pytest.fixture
def sample_aws_resources():
    """Sample AWS resources for testing."""
    return [
        AWSResource(
            resource_type="AWS::DynamoDB::Table",
            resource_id="incident-commander-incidents",
            resource_arn="arn:aws:dynamodb:us-east-1:123456789012:table/incident-commander-incidents",
            status="Active",
            created_at=datetime.utcnow(),
            tags={"Project": "IncidentCommander"}
        ),
        AWSResource(
            resource_type="AWS::S3::Bucket",
            resource_id="incident-commander-artifacts",
            resource_arn="arn:aws:s3:::incident-commander-artifacts",
            status="Active",
            created_at=datetime.utcnow(),
            tags={"Project": "IncidentCommander"}
        )
    ]


class TestDeploymentPipeline:
    """Test deployment pipeline core functionality."""
    
    @pytest.mark.asyncio
    async def test_deploy_environment_development(self, deployment_pipeline, mock_aws_factory):
        """Test deployment to development environment."""
        # Mock CDK command execution
        with patch.object(deployment_pipeline, '_run_cdk_command') as mock_cdk:
            mock_cdk.return_value = Mock(stdout="Stack deployed successfully", stderr="")
            
            # Mock resource parsing
            with patch.object(deployment_pipeline, '_parse_stack_outputs') as mock_parse:
                mock_parse.return_value = []
                
                # Mock validation
                with patch.object(deployment_pipeline, '_validate_deployment') as mock_validate:
                    mock_validate.return_value = [
                        ValidationResult(
                            is_valid=True,
                            validation_type="test",
                            message="Test passed",
                            details={},
                            validated_at=datetime.utcnow()
                        )
                    ]
                    
                    result = await deployment_pipeline.deploy_environment(Environment.DEVELOPMENT)
                    
                    assert result.environment == Environment.DEVELOPMENT
                    assert result.status == DeploymentStatus.COMPLETED
                    assert result.deployment_time > 0
                    assert result.rollback_plan is not None
    
    @pytest.mark.asyncio
    async def test_deploy_environment_failure_with_rollback(self, deployment_pipeline):
        """Test deployment failure triggers rollback."""
        # Mock CDK command failure
        with patch.object(deployment_pipeline, '_run_cdk_command') as mock_cdk:
            mock_cdk.side_effect = Exception("CDK deployment failed")
            
            # Mock rollback execution
            with patch.object(deployment_pipeline, '_execute_rollback') as mock_rollback:
                mock_rollback.return_value = True
                
                result = await deployment_pipeline.deploy_environment(Environment.STAGING)
                
                assert result.status == DeploymentStatus.FAILED
                assert result.error_message is not None
                mock_rollback.assert_called_once()
    
    def test_get_stack_names_ordering(self, deployment_pipeline):
        """Test stack names are returned in correct deployment order."""
        stack_names = deployment_pipeline._get_stack_names(Environment.PRODUCTION)
        
        # Verify core stack comes first
        assert stack_names[0].endswith("Core-production")
        # Verify networking comes before compute
        core_index = next(i for i, name in enumerate(stack_names) if "Core" in name)
        networking_index = next(i for i, name in enumerate(stack_names) if "Networking" in name)
        compute_index = next(i for i, name in enumerate(stack_names) if "Compute" in name)
        
        assert core_index < networking_index < compute_index
    
    def test_environment_configurations(self, deployment_pipeline):
        """Test environment-specific configurations are correct."""
        dev_config = deployment_pipeline._environment_configs[Environment.DEVELOPMENT]
        prod_config = deployment_pipeline._environment_configs[Environment.PRODUCTION]
        
        # Development should have minimal resources
        assert dev_config["min_capacity"] == 1
        assert dev_config["backup_retention_days"] == 7
        assert not dev_config["auto_scaling_enabled"]
        
        # Production should have high availability
        assert prod_config["min_capacity"] >= 3
        assert prod_config["backup_retention_days"] == 2555  # 7 years
        assert prod_config["auto_scaling_enabled"]
        assert prod_config["multi_az"]
    
    @pytest.mark.asyncio
    async def test_create_rollback_plan(self, deployment_pipeline):
        """Test rollback plan creation."""
        with patch.object(deployment_pipeline, '_get_current_deployment_version') as mock_version:
            mock_version.return_value = "v1.0.0-test"
            
            rollback_plan = await deployment_pipeline._create_rollback_plan(
                Environment.STAGING, "test-deployment-123"
            )
            
            assert rollback_plan.rollback_id.startswith("rollback_")
            assert rollback_plan.previous_version == "v1.0.0-test"
            assert len(rollback_plan.rollback_steps) > 0
            assert rollback_plan.estimated_duration_minutes > 0
    
    def test_deployment_status_tracking(self, deployment_pipeline):
        """Test deployment status tracking functionality."""
        # Create mock deployment result
        deployment_result = DeploymentResult(
            deployment_id="test-123",
            environment=Environment.DEVELOPMENT,
            status=DeploymentStatus.IN_PROGRESS,
            resources_created=[],
            validation_results=[],
            rollback_plan=None,
            deployment_time=0.0,
            started_at=datetime.utcnow(),
            completed_at=None,
            error_message=None
        )
        
        # Add to active deployments
        deployment_pipeline._active_deployments["test-123"] = deployment_result
        
        # Test retrieval
        retrieved = deployment_pipeline.get_deployment_status("test-123")
        assert retrieved is not None
        assert retrieved.deployment_id == "test-123"
        
        # Test non-existent deployment
        not_found = deployment_pipeline.get_deployment_status("non-existent")
        assert not_found is None
    
    def test_deployment_history_management(self, deployment_pipeline):
        """Test deployment history management."""
        # Add multiple deployments to history
        for i in range(5):
            deployment_result = DeploymentResult(
                deployment_id=f"test-{i}",
                environment=Environment.DEVELOPMENT,
                status=DeploymentStatus.COMPLETED,
                resources_created=[],
                validation_results=[],
                rollback_plan=None,
                deployment_time=float(i * 10),
                started_at=datetime.utcnow() - timedelta(hours=i),
                completed_at=datetime.utcnow() - timedelta(hours=i) + timedelta(minutes=10),
                error_message=None
            )
            deployment_pipeline._deployment_history.append(deployment_result)
        
        # Test history retrieval with limit
        history = deployment_pipeline.get_deployment_history(3)
        assert len(history) == 3
        
        # Test full history
        full_history = deployment_pipeline.get_deployment_history()
        assert len(full_history) == 5
    
    def test_environment_status(self, deployment_pipeline):
        """Test environment status reporting."""
        # Add deployment to history
        deployment_result = DeploymentResult(
            deployment_id="test-env-status",
            environment=Environment.PRODUCTION,
            status=DeploymentStatus.COMPLETED,
            resources_created=[],
            validation_results=[],
            rollback_plan=None,
            deployment_time=120.0,
            started_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow(),
            error_message=None
        )
        deployment_pipeline._deployment_history.append(deployment_result)
        
        status = deployment_pipeline.get_environment_status(Environment.PRODUCTION)
        
        assert status["environment"] == "production"
        assert status["latest_deployment"]["deployment_id"] == "test-env-status"
        assert status["latest_deployment"]["status"] == "completed"
        assert "configuration" in status
        assert "deployment_timeout_minutes" in status


class TestDeploymentValidation:
    """Test deployment validation functionality."""
    
    @pytest.mark.asyncio
    async def test_validate_resources_success(self, deployment_pipeline, sample_aws_resources):
        """Test successful resource validation."""
        result = await deployment_pipeline._validate_resources(sample_aws_resources)
        
        assert result.is_valid
        assert result.validation_type == "resource_creation"
        assert "All 2 resources created successfully" in result.message
        assert result.details["total_resources"] == 2
        assert result.details["failed_resources"] == 0
    
    @pytest.mark.asyncio
    async def test_validate_resources_failure(self, deployment_pipeline):
        """Test resource validation with failures."""
        failed_resources = [
            AWSResource(
                resource_type="AWS::DynamoDB::Table",
                resource_id="failed-table",
                resource_arn="arn:aws:dynamodb:us-east-1:123456789012:table/failed-table",
                status="Failed",
                created_at=datetime.utcnow(),
                tags={}
            )
        ]
        
        result = await deployment_pipeline._validate_resources(failed_resources)
        
        assert not result.is_valid
        assert "1 resources failed to create" in result.message
        assert result.details["failed_resources"] == 1
        assert "failed-table" in result.details["failed_resource_ids"]
    
    @pytest.mark.asyncio
    async def test_validate_service_health(self, deployment_pipeline):
        """Test service health validation."""
        result = await deployment_pipeline._validate_service_health(Environment.DEVELOPMENT)
        
        assert result.is_valid
        assert result.validation_type == "service_health"
        assert "All services are healthy" in result.message
        assert result.details["healthy_services"] == 4
    
    @pytest.mark.asyncio
    async def test_validate_api_endpoints_mock(self, deployment_pipeline):
        """Test API endpoint validation (mocked)."""
        # Mock HTTP session
        deployment_pipeline._http_session = Mock()
        
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        
        deployment_pipeline._http_session.request = Mock(return_value=mock_response)
        
        result = await deployment_pipeline._validate_api_endpoints(Environment.DEVELOPMENT)
        
        assert result.is_valid
        assert result.validation_type == "api_endpoints"
        assert "All API endpoints are responding" in result.message


class TestRollbackFunctionality:
    """Test deployment rollback functionality."""
    
    @pytest.mark.asyncio
    async def test_execute_rollback_success(self, deployment_pipeline):
        """Test successful rollback execution."""
        # Create deployment result with rollback plan
        rollback_plan = RollbackPlan(
            rollback_id="rollback-123",
            previous_version="v1.0.0",
            rollback_steps=["Stop services", "Restore configuration", "Restart services"],
            estimated_duration_minutes=10,
            created_at=datetime.utcnow()
        )
        
        deployment_result = DeploymentResult(
            deployment_id="test-rollback",
            environment=Environment.STAGING,
            status=DeploymentStatus.FAILED,
            resources_created=[],
            validation_results=[],
            rollback_plan=rollback_plan,
            deployment_time=60.0,
            started_at=datetime.utcnow() - timedelta(minutes=5),
            completed_at=datetime.utcnow(),
            error_message="Deployment failed"
        )
        
        success = await deployment_pipeline._execute_rollback(deployment_result)
        
        assert success
        assert deployment_result.status == DeploymentStatus.ROLLED_BACK
    
    @pytest.mark.asyncio
    async def test_execute_rollback_no_plan(self, deployment_pipeline):
        """Test rollback execution without rollback plan."""
        deployment_result = DeploymentResult(
            deployment_id="test-no-rollback",
            environment=Environment.STAGING,
            status=DeploymentStatus.FAILED,
            resources_created=[],
            validation_results=[],
            rollback_plan=None,
            deployment_time=60.0,
            started_at=datetime.utcnow() - timedelta(minutes=5),
            completed_at=datetime.utcnow(),
            error_message="Deployment failed"
        )
        
        success = await deployment_pipeline._execute_rollback(deployment_result)
        
        assert not success


class TestCDKIntegration:
    """Test CDK integration functionality."""
    
    @pytest.mark.asyncio
    async def test_run_cdk_command_success(self, deployment_pipeline):
        """Test successful CDK command execution."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful process
            mock_process = Mock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"Success", b""))
            mock_subprocess.return_value = mock_process
            
            result = await deployment_pipeline._run_cdk_command(
                ["cdk", "synth"], 
                cwd=deployment_pipeline.cdk_app_path.parent,
                env={},
                timeout_minutes=5
            )
            
            assert result.returncode == 0
            assert "Success" in result.stdout
    
    @pytest.mark.asyncio
    async def test_run_cdk_command_failure(self, deployment_pipeline):
        """Test CDK command execution failure."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock failed process
            mock_process = Mock()
            mock_process.returncode = 1
            mock_process.communicate = AsyncMock(return_value=(b"", b"CDK Error"))
            mock_subprocess.return_value = mock_process
            
            with pytest.raises(Exception):
                await deployment_pipeline._run_cdk_command(
                    ["cdk", "deploy"], 
                    cwd=deployment_pipeline.cdk_app_path.parent,
                    env={},
                    timeout_minutes=5
                )
    
    @pytest.mark.asyncio
    async def test_run_cdk_command_timeout(self, deployment_pipeline):
        """Test CDK command timeout handling."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock process that times out
            mock_process = Mock()
            mock_process.kill = Mock()
            mock_process.wait = AsyncMock()
            mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
            mock_subprocess.return_value = mock_process
            
            with pytest.raises(Exception):
                await deployment_pipeline._run_cdk_command(
                    ["cdk", "deploy"], 
                    cwd=deployment_pipeline.cdk_app_path.parent,
                    env={},
                    timeout_minutes=0.01  # Very short timeout
                )
    
    def test_parse_stack_outputs_core_stack(self, deployment_pipeline):
        """Test parsing outputs from core stack."""
        mock_stdout = "Stack deployed successfully"
        
        resources = asyncio.run(deployment_pipeline._parse_stack_outputs(
            "IncidentCommanderCore-production", mock_stdout
        ))
        
        # Should create KMS key and IAM role for core stack
        assert len(resources) == 2
        assert any(r.resource_type == "AWS::KMS::Key" for r in resources)
        assert any(r.resource_type == "AWS::IAM::Role" for r in resources)
    
    def test_parse_stack_outputs_storage_stack(self, deployment_pipeline):
        """Test parsing outputs from storage stack."""
        mock_stdout = "Stack deployed successfully"
        
        resources = asyncio.run(deployment_pipeline._parse_stack_outputs(
            "IncidentCommanderStorage-staging", mock_stdout
        ))
        
        # Should create DynamoDB table and S3 bucket for storage stack
        assert len(resources) == 2
        assert any(r.resource_type == "AWS::DynamoDB::Table" for r in resources)
        assert any(r.resource_type == "AWS::S3::Bucket" for r in resources)


class TestMultiEnvironmentDeployment:
    """Test multi-environment deployment scenarios."""
    
    @pytest.mark.asyncio
    async def test_development_deployment_configuration(self, deployment_pipeline):
        """Test development environment specific configuration."""
        config = deployment_pipeline._environment_configs[Environment.DEVELOPMENT]
        
        assert config["min_capacity"] == 1
        assert config["max_capacity"] == 3
        assert not config["enable_detailed_monitoring"]
        assert config["backup_retention_days"] == 7
        assert not config.get("auto_scaling_enabled", False)
        assert not config.get("multi_az", False)
    
    @pytest.mark.asyncio
    async def test_staging_deployment_configuration(self, deployment_pipeline):
        """Test staging environment specific configuration."""
        config = deployment_pipeline._environment_configs[Environment.STAGING]
        
        assert config["min_capacity"] == 2
        assert config["max_capacity"] == 10
        assert config["enable_detailed_monitoring"]
        assert config["backup_retention_days"] == 30
        assert config["auto_scaling_enabled"]
        assert config["multi_az"]
    
    @pytest.mark.asyncio
    async def test_production_deployment_configuration(self, deployment_pipeline):
        """Test production environment specific configuration."""
        config = deployment_pipeline._environment_configs[Environment.PRODUCTION]
        
        assert config["min_capacity"] >= 3
        assert config["max_capacity"] >= 50
        assert config["enable_detailed_monitoring"]
        assert config["backup_retention_days"] == 2555  # 7 years
        assert config["auto_scaling_enabled"]
        assert config["multi_az"]
        assert config["encryption_required"]
        assert config["backup_required"]
    
    def test_deployment_timeout_configuration(self, deployment_pipeline):
        """Test deployment timeout configuration by environment."""
        timeouts = deployment_pipeline.deployment_timeouts
        
        assert timeouts[Environment.DEVELOPMENT] == 15
        assert timeouts[Environment.STAGING] == 30
        assert timeouts[Environment.PRODUCTION] == 45
        
        # Production should have longest timeout due to complexity
        assert (timeouts[Environment.PRODUCTION] > 
                timeouts[Environment.STAGING] > 
                timeouts[Environment.DEVELOPMENT])


@pytest.mark.integration
class TestDeploymentIntegration:
    """Integration tests for deployment pipeline."""
    
    @pytest.mark.asyncio
    async def test_full_deployment_workflow(self, deployment_pipeline):
        """Test complete deployment workflow integration."""
        # This would be a more comprehensive integration test
        # that tests the entire deployment pipeline end-to-end
        
        # Mock all external dependencies
        with patch.object(deployment_pipeline, '_run_cdk_command') as mock_cdk, \
             patch.object(deployment_pipeline, '_validate_deployment') as mock_validate:
            
            mock_cdk.return_value = Mock(stdout="Success", stderr="")
            mock_validate.return_value = [
                ValidationResult(
                    is_valid=True,
                    validation_type="integration_test",
                    message="Integration test passed",
                    details={},
                    validated_at=datetime.utcnow()
                )
            ]
            
            # Test deployment to all environments
            for environment in Environment:
                result = await deployment_pipeline.deploy_environment(environment)
                
                assert result.environment == environment
                assert result.status in [DeploymentStatus.COMPLETED, DeploymentStatus.FAILED]
                assert result.deployment_time >= 0
                assert result.rollback_plan is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_deployments(self, deployment_pipeline):
        """Test handling of concurrent deployments to different environments."""
        with patch.object(deployment_pipeline, '_run_cdk_command') as mock_cdk, \
             patch.object(deployment_pipeline, '_validate_deployment') as mock_validate:
            
            mock_cdk.return_value = Mock(stdout="Success", stderr="")
            mock_validate.return_value = [
                ValidationResult(
                    is_valid=True,
                    validation_type="concurrent_test",
                    message="Concurrent test passed",
                    details={},
                    validated_at=datetime.utcnow()
                )
            ]
            
            # Start concurrent deployments
            tasks = [
                deployment_pipeline.deploy_environment(Environment.DEVELOPMENT),
                deployment_pipeline.deploy_environment(Environment.STAGING)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Both deployments should complete successfully
            assert len(results) == 2
            for result in results:
                assert isinstance(result, DeploymentResult)
                assert result.status == DeploymentStatus.COMPLETED