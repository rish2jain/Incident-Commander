"""
Tests for Milestone 2 agents: Prediction, Resolution, and Communication.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact
from src.models.agent import AgentRecommendation, AgentStatus, AgentType
from src.services.aws import AWSServiceFactory
from src.services.rag_memory import ScalableRAGMemory

from agents.prediction.agent import PredictionAgent
from agents.resolution.agent import SecureResolutionAgent
from agents.communication.agent import ResilientCommunicationAgent


@pytest.fixture
def sample_incident():
    """Create a sample incident for testing."""
    from src.models.incident import IncidentMetadata
    
    business_impact = BusinessImpact(
        service_tier=ServiceTier.TIER_1,
        affected_users=10000,
        revenue_impact_per_minute=500.0
    )
    
    metadata = IncidentMetadata(
        source_system="test",
        tags={}
    )
    
    return Incident(
        title="Test Database Performance Issue",
        description="Database response times are degraded",
        severity=IncidentSeverity.HIGH,
        service_name="database",
        business_impact=business_impact,
        metadata=metadata
    )


@pytest.fixture
def mock_aws_factory():
    """Create a mock AWS service factory."""
    factory = Mock()
    
    # Mock CloudWatch client
    mock_cloudwatch = AsyncMock()
    mock_cloudwatch.get_metric_statistics.return_value = {
        "Datapoints": [
            {
                "Timestamp": datetime.utcnow() - timedelta(minutes=5),
                "Average": 75.0
            },
            {
                "Timestamp": datetime.utcnow(),
                "Average": 85.0
            }
        ]
    }
    factory.get_cloudwatch_client.return_value = mock_cloudwatch
    
    return factory


@pytest.fixture
def mock_rag_memory():
    """Create a mock RAG memory service."""
    memory = Mock()
    memory.search_similar_incidents.return_value = []
    return memory


class TestPredictionAgent:
    """Test the Prediction Agent."""
    
    @pytest.mark.asyncio
    async def test_prediction_agent_initialization(self, mock_aws_factory, mock_rag_memory):
        """Test prediction agent initialization."""
        agent = PredictionAgent(mock_aws_factory, mock_rag_memory)
        
        assert agent.name == "prediction-agent"
        assert agent.target_accuracy == 0.8
        assert agent.prediction_window == timedelta(minutes=30)
        assert len(agent.data_sources) == 3
    
    @pytest.mark.asyncio
    async def test_prediction_agent_process_incident(self, mock_aws_factory, mock_rag_memory, sample_incident):
        """Test prediction agent incident processing."""
        agent = PredictionAgent(mock_aws_factory, mock_rag_memory)
        
        recommendations = await agent.process_incident(sample_incident)
        
        # The agent returns a list of recommendations
        assert isinstance(recommendations, list)
        # May be empty if no significant predictions found
        if recommendations:
            recommendation = recommendations[0]
            assert hasattr(recommendation, 'agent_name')
            assert recommendation.agent_name == AgentType.PREDICTION
            assert hasattr(recommendation, 'incident_id')
            assert recommendation.incident_id == sample_incident.id
            assert hasattr(recommendation, 'confidence')
            assert recommendation.confidence >= 0.0
            assert recommendation.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_prediction_agent_future_incidents(self, mock_aws_factory, mock_rag_memory):
        """Test prediction agent future incident prediction."""
        agent = PredictionAgent(mock_aws_factory, mock_rag_memory)
        
        predictions = await agent.predict_future_incidents()
        
        assert isinstance(predictions, list)
        # Predictions may be empty if no significant patterns detected
    
    @pytest.mark.asyncio
    async def test_prediction_agent_health_status(self, mock_aws_factory, mock_rag_memory):
        """Test prediction agent health status."""
        agent = PredictionAgent(mock_aws_factory, mock_rag_memory)
        
        health_status = await agent.get_health_status()
        
        assert "agent_id" in health_status
        assert "status" in health_status
        assert "capabilities" in health_status
        assert "performance_targets" in health_status
        assert "data_sources" in health_status


class TestResolutionAgent:
    """Test the Resolution Agent."""
    
    @pytest.mark.asyncio
    async def test_resolution_agent_initialization(self, mock_aws_factory):
        """Test resolution agent initialization."""
        agent = SecureResolutionAgent(mock_aws_factory)
        
        assert agent.agent_id == "resolution-agent"
        assert agent.target_resolution_time == timedelta(minutes=3)
        assert agent.max_concurrent_actions == 3
        assert len(agent.action_templates) > 0
    
    @pytest.mark.asyncio
    async def test_resolution_agent_process_incident(self, mock_aws_factory, sample_incident):
        """Test resolution agent incident processing."""
        agent = SecureResolutionAgent(mock_aws_factory)
        
        recommendation = await agent.process_incident(sample_incident)
        
        # The agent returns a custom recommendation structure
        assert hasattr(recommendation, 'agent_id')
        assert recommendation.agent_id == "resolution-agent"
        assert hasattr(recommendation, 'incident_id')
        assert recommendation.incident_id == sample_incident.id
        assert hasattr(recommendation, 'confidence')
        assert recommendation.confidence >= 0.0
        assert recommendation.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_resolution_agent_action_templates(self, mock_aws_factory):
        """Test resolution agent action templates."""
        agent = SecureResolutionAgent(mock_aws_factory)
        
        # Test that we have templates for common incident types
        expected_templates = [
            "cpu_exhaustion", "memory_leak", "service_degradation",
            "performance_degradation", "storage_exhaustion"
        ]
        
        for template in expected_templates:
            assert template in agent.action_templates
    
    @pytest.mark.asyncio
    async def test_resolution_agent_health_status(self, mock_aws_factory):
        """Test resolution agent health status."""
        agent = SecureResolutionAgent(mock_aws_factory)
        
        health_status = await agent.get_health_status()
        
        assert "agent_id" in health_status
        assert "status" in health_status
        assert "capabilities" in health_status
        assert "capacity" in health_status
        assert "action_templates" in health_status
        assert "security_settings" in health_status


class TestCommunicationAgent:
    """Test the Communication Agent."""
    
    @pytest.mark.asyncio
    async def test_communication_agent_initialization(self):
        """Test communication agent initialization."""
        agent = ResilientCommunicationAgent()
        
        assert agent.agent_id == "communication-agent"
        assert agent.target_delivery_time == timedelta(seconds=10)
        assert agent.template_manager is not None
        assert agent.channel_manager is not None
        assert agent.stakeholder_manager is not None
    
    @pytest.mark.asyncio
    async def test_communication_agent_process_incident(self, sample_incident):
        """Test communication agent incident processing."""
        agent = ResilientCommunicationAgent()
        
        recommendation = await agent.process_incident(sample_incident)
        
        # The agent returns a custom recommendation structure
        assert hasattr(recommendation, 'agent_id')
        assert recommendation.agent_id == "communication-agent"
        assert hasattr(recommendation, 'incident_id')
        assert recommendation.incident_id == sample_incident.id
        assert hasattr(recommendation, 'confidence')
        assert recommendation.confidence >= 0.0
        assert recommendation.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_communication_agent_resolution_update(self, sample_incident):
        """Test communication agent resolution update."""
        agent = ResilientCommunicationAgent()
        
        resolution_actions = [
            {"type": "scale_service", "target_service": "database", "success": True}
        ]
        
        results = await agent.send_resolution_update(sample_incident, resolution_actions)
        
        assert isinstance(results, list)
        # Results may be empty if no channels are configured for testing
    
    @pytest.mark.asyncio
    async def test_communication_agent_approval_request(self, sample_incident):
        """Test communication agent approval request."""
        agent = ResilientCommunicationAgent()
        
        proposed_action = {
            "description": "Restart database cluster",
            "risk_level": "high",
            "estimated_impact": "5 minute downtime",
            "approval_reason": "High-risk action requires approval"
        }
        
        results = await agent.request_human_approval(sample_incident, proposed_action)
        
        assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_communication_agent_health_status(self):
        """Test communication agent health status."""
        agent = ResilientCommunicationAgent()
        
        health_status = await agent.get_health_status()
        
        assert "agent_id" in health_status
        assert "status" in health_status
        assert "capabilities" in health_status
        assert "channel_status" in health_status
        assert "delivery_stats" in health_status
        assert "available_templates" in health_status


class TestAgentIntegration:
    """Test integration between the new agents."""
    
    @pytest.mark.asyncio
    async def test_agent_status_consistency(self, mock_aws_factory, mock_rag_memory):
        """Test that all agents have consistent status reporting."""
        agents = [
            PredictionAgent(mock_aws_factory, mock_rag_memory),
            SecureResolutionAgent(mock_aws_factory),
            ResilientCommunicationAgent()
        ]
        
        for agent in agents:
            # Test initial status
            assert agent.status == AgentStatus.HEALTHY
            assert agent.last_activity is None
            
            # Test health status method
            health_status = await agent.get_health_status()
            assert "agent_id" in health_status
            assert "status" in health_status
            assert "capabilities" in health_status
    
    @pytest.mark.asyncio
    async def test_agent_recommendation_format(self, mock_aws_factory, mock_rag_memory, sample_incident):
        """Test that all agents return properly formatted recommendations."""
        agents = [
            PredictionAgent(mock_aws_factory, mock_rag_memory),
            SecureResolutionAgent(mock_aws_factory),
            ResilientCommunicationAgent()
        ]
        
        for agent in agents:
            recommendation = await agent.process_incident(sample_incident)
            
            # Verify recommendation structure (custom format)
            assert hasattr(recommendation, 'agent_id')
            assert recommendation.agent_id == agent.agent_id
            assert hasattr(recommendation, 'incident_id')
            assert recommendation.incident_id == sample_incident.id
            assert hasattr(recommendation, 'confidence')
            assert isinstance(recommendation.confidence, float)
            assert 0.0 <= recommendation.confidence <= 1.0
            assert hasattr(recommendation, 'reasoning')
            assert isinstance(recommendation.reasoning, str)
            assert hasattr(recommendation, 'actions')
            assert isinstance(recommendation.actions, list)
            assert hasattr(recommendation, 'metadata')
            assert isinstance(recommendation.metadata, dict)
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, mock_aws_factory, mock_rag_memory):
        """Test that agents handle errors gracefully."""
        # Create an invalid incident to trigger error handling
        invalid_incident = Mock()
        invalid_incident.id = "test-invalid"
        invalid_incident.title = None  # This should cause errors
        
        agents = [
            PredictionAgent(mock_aws_factory, mock_rag_memory),
            SecureResolutionAgent(mock_aws_factory),
            ResilientCommunicationAgent()
        ]
        
        for agent in agents:
            try:
                recommendation = await agent.process_incident(invalid_incident)
                
                # Even with errors, should return a recommendation
                assert hasattr(recommendation, 'confidence')
                assert recommendation.confidence == 0.0  # Should indicate failure
                assert hasattr(recommendation, 'reasoning')
                assert "error" in recommendation.reasoning.lower()
                
            except Exception as e:
                # If exception is raised, it should be handled gracefully
                pytest.fail(f"Agent {agent.agent_id} did not handle error gracefully: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])