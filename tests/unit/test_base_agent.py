"""
Unit tests for BaseAgent functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from src.interfaces.agent import BaseAgent
from src.models.agent import AgentType, AgentStatus, AgentMessage
from src.models.incident import Incident


class TestAgent(BaseAgent):
    """Test implementation of BaseAgent for testing."""
    
    def __init__(self, name: str = "test_agent"):
        super().__init__(AgentType.DETECTION, name)
    
    async def process_incident(self, incident):
        return []
    
    async def handle_message(self, message):
        return None
    
    async def health_check(self):
        return self.is_healthy


class TestBaseAgent:
    """Test cases for BaseAgent functionality."""
    
    def test_agent_initialization(self):
        """Test agent initializes with correct defaults."""
        agent = TestAgent("test")
        
        assert agent.agent_type == AgentType.DETECTION
        assert agent.name == "test"
        assert agent.is_healthy is True
        assert agent.status == AgentStatus.HEALTHY
        assert agent.processing_count == 0
        assert agent.error_count == 0
        assert isinstance(agent.metadata, dict)
        assert isinstance(agent.last_heartbeat, datetime)
        assert isinstance(agent.last_activity, datetime)
    
    def test_update_status_success(self):
        """Test successful status update."""
        agent = TestAgent()
        initial_processing_count = agent.processing_count
        
        agent._update_status_success(test_param="test_value")
        
        assert agent.status == AgentStatus.HEALTHY
        assert agent.processing_count == initial_processing_count + 1
        assert agent.metadata["test_param"] == "test_value"
        assert isinstance(agent.last_activity, datetime)
    
    def test_update_status_error(self):
        """Test error status update."""
        agent = TestAgent()
        initial_error_count = agent.error_count
        
        agent._update_status_error("Test error", error_code=500)
        
        assert agent.status == AgentStatus.ERROR
        assert agent.error_count == initial_error_count + 1
        assert agent.metadata["last_error"] == "Test error"
        assert agent.metadata["error_code"] == 500
        assert isinstance(agent.last_activity, datetime)
    
    def test_error_threshold_unhealthy(self):
        """Test agent becomes unhealthy after too many errors."""
        agent = TestAgent()
        
        # Trigger multiple errors to exceed threshold
        for i in range(12):  # Threshold is 10
            agent._update_status_error(f"Error {i}")
        
        assert agent.is_healthy is False
        assert agent.error_count == 12
    
    async def test_get_status(self):
        """Test status retrieval."""
        agent = TestAgent("status_test")
        
        status = await agent.get_status()
        
        assert status["agent_type"] == AgentType.DETECTION.value
        assert status["name"] == "status_test"
        assert status["is_healthy"] is True
        assert "last_heartbeat" in status
        assert status["processing_count"] == 0
        assert status["error_count"] == 0
    
    def test_update_heartbeat(self):
        """Test heartbeat update."""
        agent = TestAgent()
        old_heartbeat = agent.last_heartbeat
        
        agent.update_heartbeat()
        
        assert agent.last_heartbeat > old_heartbeat
    
    def test_increment_processing_count(self):
        """Test processing count increment."""
        agent = TestAgent()
        initial_count = agent.processing_count
        
        agent.increment_processing_count()
        
        assert agent.processing_count == initial_count + 1
    
    def test_increment_error_count(self):
        """Test error count increment and health status."""
        agent = TestAgent()
        initial_count = agent.error_count
        
        # Increment errors but stay below threshold
        for _ in range(5):
            agent.increment_error_count()
        
        assert agent.error_count == initial_count + 5
        assert agent.is_healthy is True
        
        # Exceed threshold
        for _ in range(10):
            agent.increment_error_count()
        
        assert agent.is_healthy is False


@pytest.mark.asyncio
class TestBaseAgentAsync:
    """Async test cases for BaseAgent."""
    
    async def test_abstract_methods_implemented(self):
        """Test that abstract methods are properly implemented."""
        agent = TestAgent()
        
        # These should not raise NotImplementedError
        result = await agent.process_incident(Mock())
        assert result == []
        
        result = await agent.handle_message(Mock())
        assert result is None
        
        result = await agent.health_check()
        assert result is True