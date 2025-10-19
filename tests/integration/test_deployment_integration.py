"""
Integration tests for deployment system.

Tests multi-environment deployment, Bedrock agent configuration,
and deployment validation integration.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from src.services.deployment_pipeline import DeploymentPipeline, Environment
from src.services.bedrock_agent_configurator import BedrockAgentConfigurator, AgentType, KnowledgeBaseType
from src.services.deployment_validator import DeploymentValidator
from src.services.aws import AWSServiceFactory


@pytest.fixture
def mock_aws_factory():
    """Mock AWS service factory for integration tests."""
    factory = Mock(spec=AWSServiceFactory)
    
    # Mock clients
    mock_sts_client = AsyncMock()
    mock_sts_client.get_caller_identity.return_value = {"Account": "123456789012"}
    
    mock_bedrock_client = AsyncMock()
    mock_bedrock_client.create_agent.return_value = {
        "agent": {
            "agentId": "test-agent-123",
            "agentArn": "arn:aws:bedrock:us-east-1:123456789012:agent/test-agent-123"
        }
    }
    mock_bedrock_client.create_knowledge_base.return_value = {
        "knowledgeBase": {"knowledgeBaseId": "test-kb-123"}
    }
    mock_bedrock_client.prepare_agent.return_value = {}
    mock_bedrock_client.create_agent_alias.return_value = {}
    
    mock_dynamodb_client = AsyncMock()
    mock_dynamodb_client.list_tables.return_value = {"TableNames": ["incident-commander-incidents"]}
    
    # Configure factory to return appropriate clients
    def create_client_side_effect(service_name, **kwargs):
        if service_name == 'sts':
            return mock_sts_client
        elif service_name == 'bedrock-agent':
            return mock_bedrock_client
        elif service_name == 'bedrock-agent-runtime':
            return mock_bedrock_client
        elif service_name == 'dynamodb':
            return mock_dynamodb_client
        else:
            return AsyncMock()
    
    factory.create_client.side_effect = create_client_side_effect
    factory.create_resource = AsyncMock()
    
    return factory


@pytest.fixture
def deployment_pipeline(mock_aws_factory):
    """Create deployment pipeline for integration tests."""
    return DeploymentPipeline(mock_aws_factory)


@pytest.fixture
def bedrock_configurator(mock_aws_factory):
    """Create Bedrock configurator for integration tests."""
    return BedrockAgentConfigurator(mock_aws_factory)


@pytest.fixture
def deployment_validator(mock_aws_factory):
    """Create deployment validator for integration tests."""
    return DeploymentValidator(mock_aws_factory)


class TestDeploymentPipelineIntegration:
    """Integration tests for deployment pipeline with AWS services."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_deployment_staging(self, deployment_pipeline):
        """Test complete deployment workflow for staging environment."""
        with patch.object(deployment_pipeline, '_run_cdk_command') as mock_cdk:
            # Mock successful CDK deployment
            mock_cdk.return_value = Mock(
                stdout="✅ IncidentCommanderCore-staging\n✅ IncidentCommanderCompute-staging",
                stderr=""
            )
            
            # Mock AWS account ID retrieval
            with patch.object(deployment_pipeline, '_get_aws_account_id') as mock_account:
                mock_account.return_value = "123456789012"
                
                result = await deployment_pipeline.deploy_environment(Environment.STAGING)
                
                # Verify deployment completed successfully
                assert result.environment == Environment.STAGING
                assert result.deployment_time > 0
                assert len(result.resources_created) > 0
                assert len(result.validation_results) > 0
                assert result.rollback_plan is not None
                
                # Verify CDK commands were called in correct order
                cdk_calls = mock_cdk.call_args_list
                assert len(cdk_calls) >= 2  # At least synth and deploy calls
                
                # Verify synth was called first
                synth_call = cdk_calls[0]
                assert "synth" in synth_call[0][0]
    
    @pytest.mark.asyncio
    async def test_deployment_with_validation_failure(self, deployment_pipeline):
        """Test deployment behavior when validation fails."""
        with patch.object(deployment_pipeline, '_run_cdk_command') as mock_cdk, \
             patch.object(deployment_pipeline, '_validate_deployment') as mock_validate:
            
            # Mock successful CDK deployment
            mock_cdk.return_value = Mock(stdout="Success", stderr="")
            
            # Mock validation failure
            from src.services.deployment_pipeline import ValidationResult
            mock_validate.return_value = [
                ValidationResult(
                    is_valid=False,
                    validation_type="critical_test",
                    message="Critical validation failed",
                    details={"error": "Service not responding"},
                    validated_at=datetime.utcnow()
                )
            ]
            
            # Mock rollback execution
            with patch.object(deployment_pipeline, '_execute_rollback') as mock_rollback:
                mock_rollback.return_value = True
                
                result = await deployment_pipeline.deploy_environment(Environment.PRODUCTION)
                
                # Verify deployment failed and rollback was triggered
                assert result.status.value == "failed"
                assert result.error_message == "Deployment validation failed"
                mock_rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_multi_environment_deployment_sequence(self, deployment_pipeline):
        """Test sequential deployment to multiple environments."""
        environments = [Environment.DEVELOPMENT, Environment.STAGING]
        results = []
        
        with patch.object(deployment_pipeline, '_run_cdk_command') as mock_cdk:
            mock_cdk.return_value = Mock(stdout="Success", stderr="")
            
            # Deploy to each environment sequentially
            for env in environments:
                result = await deployment_pipeline.deploy_environment(env)
                results.append(result)
                
                # Verify each deployment
                assert result.environment == env
                assert result.deployment_time > 0
            
            # Verify deployment history
            history = deployment_pipeline.get_deployment_history()
            assert len(history) == len(environments)
            
            # Verify environments are tracked correctly
            deployed_envs = {r.environment for r in history}
            assert deployed_envs == set(environments)


class TestBedrockAgentIntegration:
    """Integration tests for Bedrock agent configuration."""
    
    @pytest.mark.asyncio
    async def test_configure_detection_agent_with_knowledge_bases(self, bedrock_configurator):
        """Test configuring detection agent with associated knowledge bases."""
        # Mock knowledge base creation
        with patch.object(bedrock_configurator, 'configure_knowledge_base') as mock_kb:
            mock_kb.return_value = "test-kb-123"
            
            # Mock action group configuration
            with patch.object(bedrock_configurator, '_configure_agent_action_groups') as mock_actions:
                mock_actions.return_value = ["action-group-123"]
                
                result = await bedrock_configurator.configure_bedrock_agent(AgentType.DETECTION_AGENT)
                
                # Verify agent was configured
                assert result.agent_id == "test-agent-123"
                assert result.agent_name == "incident-commander-detection-agent"
                assert len(result.knowledge_bases) > 0
                assert len(result.action_groups) > 0
                
                # Verify knowledge bases were configured for detection agent
                expected_kb_types = [KnowledgeBaseType.INCIDENT_PATTERNS, KnowledgeBaseType.SYSTEM_DOCUMENTATION]
                assert mock_kb.call_count == len(expected_kb_types)
    
    @pytest.mark.asyncio
    async def test_configure_all_agent_types(self, bedrock_configurator):
        """Test configuring all agent types in sequence."""
        configured_agents = []
        
        # Mock dependencies
        with patch.object(bedrock_configurator, 'configure_knowledge_base') as mock_kb, \
             patch.object(bedrock_configurator, '_configure_agent_action_groups') as mock_actions:
            
            mock_kb.return_value = "test-kb-123"
            mock_actions.return_value = ["action-group-123"]
            
            # Configure each agent type
            for agent_type in AgentType:
                result = await bedrock_configurator.configure_bedrock_agent(agent_type)
                configured_agents.append(result)
                
                # Verify basic agent configuration
                assert result.agent_id.startswith("test-agent")
                assert agent_type.value in result.agent_name
                assert result.agent_status == "PREPARED"
            
            # Verify all agents were configured
            assert len(configured_agents) == len(AgentType)
            
            # Verify agent registry
            agent_registry = bedrock_configurator.get_configured_agents()
            assert len(agent_registry) == len(AgentType)
    
    @pytest.mark.asyncio
    async def test_knowledge_base_content_ingestion(self, bedrock_configurator):
        """Test knowledge base configuration with content ingestion."""
        # Mock data source creation and ingestion
        with patch.object(bedrock_configurator, '_create_knowledge_base_data_source') as mock_ds, \
             patch.object(bedrock_configurator, '_ingest_knowledge_base_content') as mock_ingest:
            
            mock_ds.return_value = "data-source-123"
            mock_ingest.return_value = None  # Successful ingestion
            
            kb_id = await bedrock_configurator.configure_knowledge_base(KnowledgeBaseType.INCIDENT_PATTERNS)
            
            # Verify knowledge base was created
            assert kb_id == "test-kb-123"
            
            # Verify data source and ingestion were configured
            mock_ds.assert_called_once()
            mock_ingest.assert_called_once_with("test-kb-123", "data-source-123", KnowledgeBaseType.INCIDENT_PATTERNS)
            
            # Verify knowledge base registry
            kb_registry = bedrock_configurator.get_knowledge_bases()
            assert len(kb_registry) > 0
    
    @pytest.mark.asyncio
    async def test_agent_validation_after_configuration(self, bedrock_configurator):
        """Test agent validation after successful configuration."""
        # Mock agent configuration
        with patch.object(bedrock_configurator, 'configure_knowledge_base') as mock_kb, \
             patch.object(bedrock_configurator, '_configure_agent_action_groups') as mock_actions:
            
            mock_kb.return_value = "test-kb-123"
            mock_actions.return_value = ["action-group-123"]
            
            # Configure agent
            result = await bedrock_configurator.configure_bedrock_agent(AgentType.DIAGNOSIS_AGENT)
            
            # Validate agent configuration
            validation_result = await bedrock_configurator.validate_agent_configuration(result.agent_id)
            
            # Verify validation passed
            assert validation_result["is_valid"]
            assert validation_result["agent_status"] == "PREPARED"
            assert validation_result["test_response_received"]


class TestDeploymentValidationIntegration:
    """Integration tests for deployment validation system."""
    
    @pytest.mark.asyncio
    async def test_comprehensive_validation_staging(self, deployment_validator):
        """Test comprehensive validation for staging environment."""
        # Mock resources from deployment
        from src.services.deployment_pipeline import AWSResource
        mock_resources = [
            AWSResource(
                resource_type="AWS::DynamoDB::Table",
                resource_id="incident-commander-incidents",
                resource_arn="arn:aws:dynamodb:us-east-1:123456789012:table/incident-commander-incidents",
                status="Active",
                created_at=datetime.utcnow(),
                tags={"Project": "IncidentCommander"}
            )
        ]
        
        # Mock HTTP session for API validation
        with patch.object(deployment_validator, '_initialize_http_session') as mock_init_http, \
             patch.object(deployment_validator, '_cleanup_http_session') as mock_cleanup_http:
            
            mock_init_http.return_value = None
            mock_cleanup_http.return_value = None
            
            result = await deployment_validator.validate_deployment(
                Environment.STAGING, mock_resources
            )
            
            # Verify validation completed
            assert result.environment == Environment.STAGING
            assert result.total_checks > 0
            assert result.total_duration_seconds > 0
            assert result.overall_status in ["SUCCESS", "PARTIAL_FAILURE", "CRITICAL_FAILURE"]
            
            # Verify validation categories were tested
            categories_tested = {vr.category for vr in result.validation_results}
            expected_categories = {"infrastructure", "services", "security", "performance", "integration"}
            assert len(categories_tested.intersection(expected_categories)) > 0
    
    @pytest.mark.asyncio
    async def test_validation_with_performance_baselines(self, deployment_validator):
        """Test validation that establishes performance baselines."""
        mock_resources = []
        
        # Mock performance validation to return baseline data
        with patch.object(deployment_validator, '_validate_api_performance') as mock_api_perf, \
             patch.object(deployment_validator, '_validate_database_performance') as mock_db_perf:
            
            # Mock successful performance validation with metrics
            mock_api_perf.return_value = (True, "API performance acceptable", {
                "performance_results": {
                    "/health": {
                        "avg_response_time_ms": 150,
                        "status": "good"
                    }
                }
            })
            
            mock_db_perf.return_value = (True, "Database performance acceptable", {
                "query_results": {
                    "scan": {
                        "response_time_ms": 80,
                        "status": "good"
                    }
                }
            })
            
            result = await deployment_validator.validate_deployment(
                Environment.PRODUCTION, mock_resources
            )
            
            # Verify performance baselines were established
            assert len(result.performance_baselines) > 0
            
            # Verify baseline metrics
            baseline_metrics = {pb.metric_name for pb in result.performance_baselines}
            expected_metrics = {"api_response_time_ms", "database_query_time_ms"}
            assert len(baseline_metrics.intersection(expected_metrics)) > 0
    
    @pytest.mark.asyncio
    async def test_validation_failure_scenarios(self, deployment_validator):
        """Test validation behavior with various failure scenarios."""
        mock_resources = []
        
        # Mock critical validation failure
        with patch.object(deployment_validator, '_validate_aws_connectivity') as mock_aws_conn:
            mock_aws_conn.return_value = (False, "AWS connectivity failed", {"error": "Network timeout"})
            
            result = await deployment_validator.validate_deployment(
                Environment.PRODUCTION, mock_resources, custom_checks=["infra_aws_connectivity"]
            )
            
            # Verify critical failure was detected
            assert result.overall_status == "CRITICAL_FAILURE"
            assert result.critical_failures > 0
            assert result.failed_checks > 0
            
            # Verify failure details
            failed_validations = [vr for vr in result.validation_results if not vr.is_passed]
            assert len(failed_validations) > 0
            assert any("AWS connectivity failed" in vr.message for vr in failed_validations)


class TestFullSystemIntegration:
    """Integration tests for complete deployment system."""
    
    @pytest.mark.asyncio
    async def test_deploy_configure_validate_workflow(self, deployment_pipeline, bedrock_configurator, deployment_validator):
        """Test complete workflow: deploy -> configure agents -> validate."""
        # Step 1: Deploy infrastructure
        with patch.object(deployment_pipeline, '_run_cdk_command') as mock_cdk:
            mock_cdk.return_value = Mock(stdout="Deployment successful", stderr="")
            
            deployment_result = await deployment_pipeline.deploy_environment(Environment.STAGING)
            assert deployment_result.status.value == "completed"
        
        # Step 2: Configure Bedrock agents
        with patch.object(bedrock_configurator, 'configure_knowledge_base') as mock_kb, \
             patch.object(bedrock_configurator, '_configure_agent_action_groups') as mock_actions:
            
            mock_kb.return_value = "test-kb-123"
            mock_actions.return_value = ["action-group-123"]
            
            agent_result = await bedrock_configurator.configure_bedrock_agent(AgentType.DETECTION_AGENT)
            assert agent_result.agent_status == "PREPARED"
        
        # Step 3: Validate complete deployment
        validation_result = await deployment_validator.validate_deployment(
            Environment.STAGING, deployment_result.resources_created
        )
        
        # Verify end-to-end workflow
        assert validation_result.environment == Environment.STAGING
        assert validation_result.total_checks > 0
        
        # Verify system state consistency
        assert len(deployment_pipeline.get_deployment_history()) > 0
        assert len(bedrock_configurator.get_configured_agents()) > 0
        assert len(deployment_validator.get_validation_history()) > 0
    
    @pytest.mark.asyncio
    async def test_rollback_after_validation_failure(self, deployment_pipeline, deployment_validator):
        """Test rollback execution after validation failure."""
        # Step 1: Deploy with validation failure
        with patch.object(deployment_pipeline, '_run_cdk_command') as mock_cdk, \
             patch.object(deployment_validator, 'validate_deployment') as mock_validate:
            
            mock_cdk.return_value = Mock(stdout="Deployment successful", stderr="")
            
            # Mock validation failure
            from src.services.deployment_validator import IntegrationValidationResult
            mock_validate.return_value = IntegrationValidationResult(
                environment=Environment.PRODUCTION,
                validation_id="test-validation",
                overall_status="CRITICAL_FAILURE",
                total_checks=5,
                passed_checks=2,
                failed_checks=3,
                critical_failures=2,
                validation_results=[],
                performance_baselines=[],
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                total_duration_seconds=30.0
            )
            
            # Mock rollback execution
            with patch.object(deployment_pipeline, '_execute_rollback') as mock_rollback:
                mock_rollback.return_value = True
                
                deployment_result = await deployment_pipeline.deploy_environment(Environment.PRODUCTION)
                
                # Verify deployment failed and rollback was executed
                assert deployment_result.status.value == "failed"
                mock_rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_environment_operations(self, deployment_pipeline, bedrock_configurator):
        """Test concurrent operations across different environments."""
        # Mock all external dependencies
        with patch.object(deployment_pipeline, '_run_cdk_command') as mock_cdk, \
             patch.object(bedrock_configurator, 'configure_knowledge_base') as mock_kb, \
             patch.object(bedrock_configurator, '_configure_agent_action_groups') as mock_actions:
            
            mock_cdk.return_value = Mock(stdout="Success", stderr="")
            mock_kb.return_value = "test-kb-123"
            mock_actions.return_value = ["action-group-123"]
            
            # Start concurrent operations
            tasks = [
                deployment_pipeline.deploy_environment(Environment.DEVELOPMENT),
                deployment_pipeline.deploy_environment(Environment.STAGING),
                bedrock_configurator.configure_bedrock_agent(AgentType.DETECTION_AGENT),
                bedrock_configurator.configure_bedrock_agent(AgentType.DIAGNOSIS_AGENT)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all operations completed successfully
            assert len(results) == 4
            for result in results:
                assert not isinstance(result, Exception)
            
            # Verify system state
            deployment_results = results[:2]
            agent_results = results[2:]
            
            for deployment_result in deployment_results:
                assert deployment_result.status.value == "completed"
            
            for agent_result in agent_results:
                assert agent_result.agent_status == "PREPARED"


@pytest.mark.slow
class TestPerformanceIntegration:
    """Performance-focused integration tests."""
    
    @pytest.mark.asyncio
    async def test_deployment_performance_targets(self, deployment_pipeline):
        """Test deployment completes within performance targets."""
        start_time = datetime.utcnow()
        
        with patch.object(deployment_pipeline, '_run_cdk_command') as mock_cdk:
            mock_cdk.return_value = Mock(stdout="Success", stderr="")
            
            result = await deployment_pipeline.deploy_environment(Environment.DEVELOPMENT)
            
            end_time = datetime.utcnow()
            actual_duration = (end_time - start_time).total_seconds()
            
            # Verify deployment completed within timeout
            timeout = deployment_pipeline.deployment_timeouts[Environment.DEVELOPMENT] * 60  # Convert to seconds
            assert actual_duration < timeout
            
            # Verify recorded deployment time is reasonable
            assert result.deployment_time > 0
            assert result.deployment_time < timeout
    
    @pytest.mark.asyncio
    async def test_validation_performance_targets(self, deployment_validator):
        """Test validation completes within performance targets."""
        mock_resources = []
        
        start_time = datetime.utcnow()
        
        result = await deployment_validator.validate_deployment(
            Environment.STAGING, mock_resources
        )
        
        end_time = datetime.utcnow()
        actual_duration = (end_time - start_time).total_seconds()
        
        # Verify validation completed within reasonable time (should be < 5 minutes)
        assert actual_duration < 300
        
        # Verify recorded validation time matches
        assert abs(result.total_duration_seconds - actual_duration) < 5  # Allow 5 second variance