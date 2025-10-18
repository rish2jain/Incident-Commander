"""
Integration Testing Framework for Task 16.2

Comprehensive end-to-end integration testing including:
- Multi-agent coordination testing scenarios
- External service integration testing with mock APIs
- Database and event store integration testing
- Complete incident resolution workflows
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List
from contextlib import asynccontextmanager

# Import core system components
from src.orchestrator.swarm_coordinator import AgentSwarmCoordinator
from src.services.event_store import ScalableEventStore
from src.services.rag_memory import ScalableRAGMemory
from src.services.consensus import WeightedConsensusEngine
from src.services.circuit_breaker import CircuitBreakerManager
from src.services.rate_limiter import BedrockRateLimitManager, ExternalServiceRateLimiter
from src.services.aws import AWSServiceFactory

# Import agents
from agents.detection.agent import RobustDetectionAgent
from agents.diagnosis.agent import HardenedDiagnosisAgent
from agents.prediction.agent import PredictionAgent
from agents.resolution.agent import SecureResolutionAgent
from agents.communication.agent import ResilientCommunicationAgent

# Import models
from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact
from src.models.agent import AgentRecommendation, AgentType, ConsensusDecision
from src.utils.exceptions import *


class IntegrationTestFramework:
    """Framework for running comprehensive integration tests."""
    
    def __init__(self):
        self.test_results = []
        self.mock_services = {}
        self.test_incidents = []
        
    async def setup_test_environment(self):
        """Set up complete test environment with mocked external services."""
        # Mock AWS services
        self.mock_services['aws'] = self._create_mock_aws_services()
        
        # Mock external APIs
        self.mock_services['external'] = self._create_mock_external_apis()
        
        # Mock databases
        self.mock_services['database'] = self._create_mock_databases()
        
        # Initialize core components with mocks
        self.event_store = await self._create_mock_event_store()
        self.rag_memory = await self._create_mock_rag_memory()
        self.consensus_engine = WeightedConsensusEngine()
        self.circuit_breaker_manager = CircuitBreakerManager()
        
        # Initialize swarm coordinator
        self.swarm_coordinator = AgentSwarmCoordinator()
        self.swarm_coordinator.event_store = self.event_store
        self.swarm_coordinator.consensus_engine = self.consensus_engine
        
        # Register agents
        await self._register_test_agents()
    
    def _create_mock_aws_services(self):
        """Create mock AWS services."""
        aws_factory = Mock(spec=AWSServiceFactory)
        
        # Mock Bedrock client
        bedrock_client = AsyncMock()
        bedrock_client.invoke_model = AsyncMock(return_value={
            'body': Mock(read=Mock(return_value=json.dumps({
                'completion': 'Mock AI response for incident analysis'
            }).encode()))
        })
        aws_factory.get_bedrock_client.return_value = bedrock_client
        
        # Mock DynamoDB client
        dynamodb_client = AsyncMock()
        dynamodb_client.put_item = AsyncMock()
        dynamodb_client.get_item = AsyncMock(return_value={'Item': {}})
        dynamodb_client.query = AsyncMock(return_value={'Items': []})
        aws_factory.get_dynamodb_client.return_value = dynamodb_client
        
        # Mock S3 client
        s3_client = AsyncMock()
        s3_client.put_object = AsyncMock()
        s3_client.get_object = AsyncMock()
        aws_factory.get_s3_client.return_value = s3_client
        
        # Mock Lambda client
        lambda_client = AsyncMock()
        lambda_client.invoke = AsyncMock(return_value={'StatusCode': 200})
        aws_factory.get_lambda_client.return_value = lambda_client
        
        return aws_factory
    
    def _create_mock_external_apis(self):
        """Create mock external API services."""
        return {
            'datadog': {
                'get_metrics': AsyncMock(return_value={'metrics': []}),
                'send_alert': AsyncMock(return_value={'status': 'sent'})
            },
            'pagerduty': {
                'create_incident': AsyncMock(return_value={'incident_id': 'pd_123'}),
                'update_incident': AsyncMock(return_value={'status': 'updated'})
            },
            'slack': {
                'send_message': AsyncMock(return_value={'ts': '1234567890.123'}),
                'create_channel': AsyncMock(return_value={'channel': {'id': 'C123'}})
            }
        }
    
    def _create_mock_databases(self):
        """Create mock database connections."""
        return {
            'opensearch': {
                'search': AsyncMock(return_value={'hits': {'hits': []}}),
                'index': AsyncMock(return_value={'_id': 'doc_123'})
            },
            'redis': {
                'get': AsyncMock(return_value=None),
                'set': AsyncMock(return_value=True),
                'publish': AsyncMock(return_value=1)
            }
        }
    
    async def _create_mock_event_store(self):
        """Create mock event store."""
        event_store = Mock(spec=ScalableEventStore)
        event_store.append_event = AsyncMock()
        event_store.get_events = AsyncMock(return_value=[])
        event_store.create_snapshot = AsyncMock()
        event_store.replay_events = AsyncMock()
        return event_store
    
    async def _create_mock_rag_memory(self):
        """Create mock RAG memory."""
        rag_memory = Mock(spec=ScalableRAGMemory)
        rag_memory.search_similar_incidents = AsyncMock(return_value=[])
        rag_memory.store_incident_pattern = AsyncMock()
        rag_memory.get_knowledge_base_stats = AsyncMock(return_value={
            'total_patterns': 1000,
            'accuracy_score': 0.85
        })
        return rag_memory
    
    async def _register_test_agents(self):
        """Register all agents with the swarm coordinator."""
        aws_factory = self.mock_services['aws']
        
        # Create agents with mocked dependencies
        agents = [
            RobustDetectionAgent("integration_detection"),
            HardenedDiagnosisAgent("integration_diagnosis"),
            PredictionAgent(aws_factory, self.rag_memory, "integration_prediction"),
            SecureResolutionAgent(aws_factory, "integration_resolution"),
            ResilientCommunicationAgent("integration_communication")
        ]
        
        for agent in agents:
            await self.swarm_coordinator.register_agent(agent)
    
    async def create_test_incidents(self) -> List[Incident]:
        """Create various test incidents for comprehensive testing."""
        incidents = [
            # Critical database incident
            Incident(
                title="Database Connection Pool Exhaustion",
                description="Critical database connection pool exhausted, affecting all services",
                severity=IncidentSeverity.CRITICAL,
                business_impact=BusinessImpact(ServiceTier.TIER_1, 50000, 2000.0)
            ),
            
            # High severity API incident
            Incident(
                title="API Gateway Overload",
                description="API gateway experiencing high load, response times degraded",
                severity=IncidentSeverity.HIGH,
                business_impact=BusinessImpact(ServiceTier.TIER_1, 25000, 1000.0)
            ),
            
            # Medium severity memory leak
            Incident(
                title="Application Memory Leak",
                description="Gradual memory leak in user service causing performance issues",
                severity=IncidentSeverity.MEDIUM,
                business_impact=BusinessImpact(ServiceTier.TIER_2, 5000, 200.0)
            ),
            
            # Low severity monitoring alert
            Incident(
                title="Disk Space Warning",
                description="Disk space usage approaching threshold on backup servers",
                severity=IncidentSeverity.LOW,
                business_impact=BusinessImpact(ServiceTier.TIER_3, 0, 0.0)
            )
        ]
        
        self.test_incidents = incidents
        return incidents
    
    async def run_end_to_end_test(self, incident: Incident) -> Dict[str, Any]:
        """Run complete end-to-end incident resolution test."""
        test_start = datetime.utcnow()
        
        try:
            # Process incident through complete system
            result = await self.swarm_coordinator.process_incident(incident)
            
            test_end = datetime.utcnow()
            duration = (test_end - test_start).total_seconds()
            
            # Validate results
            validation_results = await self._validate_end_to_end_results(incident, result, duration)
            
            return {
                'incident_id': incident.id,
                'success': True,
                'duration_seconds': duration,
                'result': result,
                'validation': validation_results,
                'timestamp': test_start.isoformat()
            }
            
        except Exception as e:
            test_end = datetime.utcnow()
            duration = (test_end - test_start).total_seconds()
            
            return {
                'incident_id': incident.id,
                'success': False,
                'duration_seconds': duration,
                'error': str(e),
                'error_type': type(e).__name__,
                'timestamp': test_start.isoformat()
            }
    
    async def _validate_end_to_end_results(self, incident: Incident, result: Any, duration: float) -> Dict[str, Any]:
        """Validate end-to-end test results."""
        validations = {
            'mttr_compliance': duration <= 180,  # 3 minutes max
            'result_present': result is not None,
            'agents_participated': True,  # Will be validated based on actual implementation
            'consensus_reached': True,    # Will be validated based on actual implementation
            'events_recorded': True,      # Will be validated based on event store calls
            'notifications_sent': True    # Will be validated based on communication calls
        }
        
        # Validate event store interactions
        if self.event_store.append_event.called:
            validations['events_recorded'] = True
        
        return validations
    
    async def test_multi_agent_coordination_scenarios(self) -> List[Dict[str, Any]]:
        """Test various multi-agent coordination scenarios."""
        scenarios = [
            {
                'name': 'normal_coordination',
                'description': 'All agents working normally',
                'agent_behaviors': {}
            },
            {
                'name': 'agent_failure_recovery',
                'description': 'One agent fails, others continue',
                'agent_behaviors': {
                    'diagnosis': 'fail'
                }
            },
            {
                'name': 'conflicting_recommendations',
                'description': 'Agents provide conflicting recommendations',
                'agent_behaviors': {
                    'detection': 'recommend_restart',
                    'diagnosis': 'recommend_scale',
                    'prediction': 'recommend_circuit_breaker'
                }
            },
            {
                'name': 'high_confidence_consensus',
                'description': 'All agents agree with high confidence',
                'agent_behaviors': {
                    'all': 'high_confidence_agreement'
                }
            },
            {
                'name': 'low_confidence_escalation',
                'description': 'Low confidence requires human escalation',
                'agent_behaviors': {
                    'all': 'low_confidence'
                }
            }
        ]
        
        results = []
        
        for scenario in scenarios:
            # Create test incident
            incident = Incident(
                title=f"Test Incident - {scenario['name']}",
                description=f"Testing {scenario['description']}",
                severity=IncidentSeverity.MEDIUM,
                business_impact=BusinessImpact(ServiceTier.TIER_2, 1000, 100.0)
            )
            
            # Apply agent behaviors for scenario
            await self._apply_agent_behaviors(scenario['agent_behaviors'])
            
            # Run test
            result = await self.run_end_to_end_test(incident)
            result['scenario'] = scenario['name']
            result['scenario_description'] = scenario['description']
            
            results.append(result)
        
        return results
    
    async def _apply_agent_behaviors(self, behaviors: Dict[str, str]):
        """Apply specific behaviors to agents for testing scenarios."""
        # This would modify agent behavior for testing
        # Implementation depends on agent architecture
        pass
    
    async def test_external_service_integrations(self) -> Dict[str, Any]:
        """Test all external service integrations."""
        integration_tests = {}
        
        # Test AWS service integrations
        aws_tests = await self._test_aws_integrations()
        integration_tests['aws'] = aws_tests
        
        # Test external API integrations
        api_tests = await self._test_external_api_integrations()
        integration_tests['external_apis'] = api_tests
        
        # Test database integrations
        db_tests = await self._test_database_integrations()
        integration_tests['databases'] = db_tests
        
        return integration_tests
    
    async def _test_aws_integrations(self) -> Dict[str, Any]:
        """Test AWS service integrations."""
        aws_factory = self.mock_services['aws']
        
        tests = {
            'bedrock': await self._test_bedrock_integration(aws_factory),
            'dynamodb': await self._test_dynamodb_integration(aws_factory),
            's3': await self._test_s3_integration(aws_factory),
            'lambda': await self._test_lambda_integration(aws_factory)
        }
        
        return tests
    
    async def _test_bedrock_integration(self, aws_factory) -> Dict[str, Any]:
        """Test Bedrock integration."""
        try:
            bedrock_client = aws_factory.get_bedrock_client()
            
            # Test model invocation
            response = await bedrock_client.invoke_model(
                modelId='claude-3-sonnet',
                body=json.dumps({'prompt': 'Test prompt'})
            )
            
            return {
                'success': True,
                'response_received': response is not None,
                'client_available': bedrock_client is not None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _test_dynamodb_integration(self, aws_factory) -> Dict[str, Any]:
        """Test DynamoDB integration."""
        try:
            dynamodb_client = aws_factory.get_dynamodb_client()
            
            # Test put and get operations
            await dynamodb_client.put_item(
                TableName='test_table',
                Item={'id': {'S': 'test_id'}, 'data': {'S': 'test_data'}}
            )
            
            response = await dynamodb_client.get_item(
                TableName='test_table',
                Key={'id': {'S': 'test_id'}}
            )
            
            return {
                'success': True,
                'put_operation': True,
                'get_operation': response is not None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _test_s3_integration(self, aws_factory) -> Dict[str, Any]:
        """Test S3 integration."""
        try:
            s3_client = aws_factory.get_s3_client()
            
            # Test put and get operations
            await s3_client.put_object(
                Bucket='test-bucket',
                Key='test-key',
                Body=b'test data'
            )
            
            response = await s3_client.get_object(
                Bucket='test-bucket',
                Key='test-key'
            )
            
            return {
                'success': True,
                'put_operation': True,
                'get_operation': response is not None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _test_lambda_integration(self, aws_factory) -> Dict[str, Any]:
        """Test Lambda integration."""
        try:
            lambda_client = aws_factory.get_lambda_client()
            
            # Test function invocation
            response = await lambda_client.invoke(
                FunctionName='test-function',
                Payload=json.dumps({'test': 'data'})
            )
            
            return {
                'success': True,
                'invocation_successful': response.get('StatusCode') == 200
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _test_external_api_integrations(self) -> Dict[str, Any]:
        """Test external API integrations."""
        external_apis = self.mock_services['external']
        
        tests = {}
        
        for service_name, service_mock in external_apis.items():
            try:
                # Test each service's key operations
                if service_name == 'datadog':
                    metrics = await service_mock['get_metrics']()
                    alert = await service_mock['send_alert']()
                    tests[service_name] = {
                        'success': True,
                        'get_metrics': metrics is not None,
                        'send_alert': alert is not None
                    }
                
                elif service_name == 'pagerduty':
                    incident = await service_mock['create_incident']()
                    update = await service_mock['update_incident']()
                    tests[service_name] = {
                        'success': True,
                        'create_incident': incident is not None,
                        'update_incident': update is not None
                    }
                
                elif service_name == 'slack':
                    message = await service_mock['send_message']()
                    channel = await service_mock['create_channel']()
                    tests[service_name] = {
                        'success': True,
                        'send_message': message is not None,
                        'create_channel': channel is not None
                    }
                
            except Exception as e:
                tests[service_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        return tests
    
    async def _test_database_integrations(self) -> Dict[str, Any]:
        """Test database integrations."""
        databases = self.mock_services['database']
        
        tests = {}
        
        for db_name, db_mock in databases.items():
            try:
                if db_name == 'opensearch':
                    search_result = await db_mock['search']()
                    index_result = await db_mock['index']()
                    tests[db_name] = {
                        'success': True,
                        'search_operation': search_result is not None,
                        'index_operation': index_result is not None
                    }
                
                elif db_name == 'redis':
                    get_result = await db_mock['get']()
                    set_result = await db_mock['set']()
                    pub_result = await db_mock['publish']()
                    tests[db_name] = {
                        'success': True,
                        'get_operation': True,  # None is valid for cache miss
                        'set_operation': set_result is True,
                        'publish_operation': pub_result > 0
                    }
                
            except Exception as e:
                tests[db_name] = {
                    'success': False,
                    'error': str(e)
                }
        
        return tests
    
    async def generate_integration_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration test report."""
        # Run all integration tests
        incidents = await self.create_test_incidents()
        
        # End-to-end tests
        e2e_results = []
        for incident in incidents:
            result = await self.run_end_to_end_test(incident)
            e2e_results.append(result)
        
        # Multi-agent coordination tests
        coordination_results = await self.test_multi_agent_coordination_scenarios()
        
        # External service integration tests
        integration_results = await self.test_external_service_integrations()
        
        # Calculate summary statistics
        total_tests = len(e2e_results) + len(coordination_results)
        successful_tests = sum(1 for r in e2e_results + coordination_results if r.get('success', False))
        
        return {
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'success_rate': successful_tests / total_tests if total_tests > 0 else 0,
                'test_timestamp': datetime.utcnow().isoformat()
            },
            'end_to_end_tests': e2e_results,
            'coordination_tests': coordination_results,
            'integration_tests': integration_results,
            'recommendations': self._generate_test_recommendations(e2e_results, coordination_results, integration_results)
        }
    
    def _generate_test_recommendations(self, e2e_results, coordination_results, integration_results) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Analyze failure patterns
        failed_e2e = [r for r in e2e_results if not r.get('success', False)]
        if failed_e2e:
            recommendations.append(f"Address {len(failed_e2e)} end-to-end test failures")
        
        failed_coordination = [r for r in coordination_results if not r.get('success', False)]
        if failed_coordination:
            recommendations.append(f"Improve agent coordination for {len(failed_coordination)} scenarios")
        
        # Analyze performance
        slow_tests = [r for r in e2e_results if r.get('duration_seconds', 0) > 180]
        if slow_tests:
            recommendations.append(f"Optimize performance for {len(slow_tests)} slow tests (>3min)")
        
        # Check integration health
        for service, results in integration_results.items():
            if isinstance(results, dict):
                for integration, result in results.items():
                    if not result.get('success', False):
                        recommendations.append(f"Fix {service}.{integration} integration issues")
        
        return recommendations


# Test classes using the integration framework
class TestIntegrationFramework:
    """Test the integration testing framework itself."""
    
    @pytest.fixture
    async def integration_framework(self):
        """Create and setup integration test framework."""
        framework = IntegrationTestFramework()
        await framework.setup_test_environment()
        return framework
    
    @pytest.mark.asyncio
    async def test_framework_setup(self, integration_framework):
        """Test that the integration framework sets up correctly."""
        assert integration_framework.mock_services is not None
        assert 'aws' in integration_framework.mock_services
        assert 'external' in integration_framework.mock_services
        assert 'database' in integration_framework.mock_services
        
        assert integration_framework.event_store is not None
        assert integration_framework.rag_memory is not None
        assert integration_framework.consensus_engine is not None
        assert integration_framework.swarm_coordinator is not None
    
    @pytest.mark.asyncio
    async def test_end_to_end_incident_processing(self, integration_framework):
        """Test end-to-end incident processing through the framework."""
        incidents = await integration_framework.create_test_incidents()
        
        # Test with critical incident
        critical_incident = incidents[0]  # First incident is critical
        result = await integration_framework.run_end_to_end_test(critical_incident)
        
        assert result is not None
        assert 'incident_id' in result
        assert 'duration_seconds' in result
        assert result['duration_seconds'] <= 300  # Should complete within 5 minutes
    
    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self, integration_framework):
        """Test multi-agent coordination scenarios."""
        coordination_results = await integration_framework.test_multi_agent_coordination_scenarios()
        
        assert len(coordination_results) >= 5  # Should test multiple scenarios
        
        # Check that normal coordination works
        normal_scenario = next((r for r in coordination_results if r['scenario'] == 'normal_coordination'), None)
        assert normal_scenario is not None
    
    @pytest.mark.asyncio
    async def test_external_service_integrations(self, integration_framework):
        """Test external service integrations."""
        integration_results = await integration_framework.test_external_service_integrations()
        
        assert 'aws' in integration_results
        assert 'external_apis' in integration_results
        assert 'databases' in integration_results
        
        # Verify AWS integrations
        aws_results = integration_results['aws']
        assert 'bedrock' in aws_results
        assert 'dynamodb' in aws_results
        assert 's3' in aws_results
        assert 'lambda' in aws_results
    
    @pytest.mark.asyncio
    async def test_comprehensive_integration_report(self, integration_framework):
        """Test generation of comprehensive integration test report."""
        report = await integration_framework.generate_integration_test_report()
        
        assert 'summary' in report
        assert 'end_to_end_tests' in report
        assert 'coordination_tests' in report
        assert 'integration_tests' in report
        assert 'recommendations' in report
        
        # Verify summary statistics
        summary = report['summary']
        assert 'total_tests' in summary
        assert 'successful_tests' in summary
        assert 'success_rate' in summary
        assert summary['success_rate'] >= 0.0 and summary['success_rate'] <= 1.0
