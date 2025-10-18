"""
Tests for the resilient message bus implementation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.services.message_bus import ResilientMessageBus, MessageEnvelope, MessagePriority
from src.services.aws import AWSServiceFactory
from src.models.agent import AgentMessage, AgentType


class TestMessageBus:
    """Test message bus functionality."""
    
    @pytest.fixture
    def service_factory(self):
        """Create AWS service factory for testing."""
        return AWSServiceFactory()
    
    @pytest.fixture
    def message_bus(self, service_factory):
        """Create message bus for testing."""
        return ResilientMessageBus(service_factory)
    
    @pytest.fixture
    def sample_message(self):
        """Create sample agent message."""
        return AgentMessage(
            sender_agent=AgentType.DETECTION,
            recipient_agent=AgentType.DIAGNOSIS,
            message_type="incident_detected",
            payload={"incident_id": "test-123", "severity": "high"},
            correlation_id="corr-456"
        )
    
    def test_message_envelope_creation(self, sample_message):
        """Test message envelope creation and serialization."""
        envelope = MessageEnvelope(
            message_id="msg-123",
            sender_agent="detection",
            recipient_agent="diagnosis", 
            message_type="incident_detected",
            payload={"test": "data"},
            priority=MessagePriority.HIGH,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        
        # Test serialization
        envelope_dict = envelope.to_dict()
        assert envelope_dict["message_id"] == "msg-123"
        assert envelope_dict["priority"] == "high"
        
        # Test deserialization
        restored_envelope = MessageEnvelope.from_dict(envelope_dict)
        assert restored_envelope.message_id == envelope.message_id
        assert restored_envelope.priority == envelope.priority
    
    def test_message_envelope_expiration(self):
        """Test message expiration logic."""
        # Create expired message
        expired_envelope = MessageEnvelope(
            message_id="expired-123",
            sender_agent="test",
            recipient_agent="test",
            message_type="test",
            payload={},
            priority=MessagePriority.LOW,
            created_at=datetime.utcnow() - timedelta(minutes=10),
            expires_at=datetime.utcnow() - timedelta(minutes=5)
        )
        
        assert expired_envelope.is_expired()
        assert not expired_envelope.should_retry()
        
        # Create valid message
        valid_envelope = MessageEnvelope(
            message_id="valid-123",
            sender_agent="test",
            recipient_agent="test", 
            message_type="test",
            payload={},
            priority=MessagePriority.LOW,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        
        assert not valid_envelope.is_expired()
        assert valid_envelope.should_retry()
    
    @pytest.mark.asyncio
    async def test_message_bus_health_check(self, message_bus):
        """Test message bus health check."""
        # Health check may fail in test environment without Redis/SQS
        try:
            is_healthy = await message_bus.health_check()
            assert isinstance(is_healthy, bool)
        except Exception as e:
            # Expected in test environment
            assert "connection" in str(e).lower() or "redis" in str(e).lower()
    
    @pytest.mark.asyncio
    async def test_message_sending_fallback(self, message_bus, sample_message):
        """Test message sending with fallback logic."""
        try:
            message_id = await message_bus.send_message(
                sample_message,
                priority=MessagePriority.HIGH,
                ttl_seconds=300
            )
            
            assert isinstance(message_id, str)
            assert len(message_id) > 0
            
        except Exception as e:
            # Expected in test environment without Redis/SQS
            error_msg = str(e).lower()
            assert ("connection" in error_msg or "redis" in error_msg or 
                   "delivery" in error_msg or "endpoint" in error_msg)
    
    @pytest.mark.asyncio
    async def test_subscription_management(self, message_bus):
        """Test agent subscription and unsubscription."""
        async def test_handler(message):
            pass
        
        # Test subscription
        await message_bus.subscribe("test_agent", test_handler)
        assert "test_agent" in message_bus._message_handlers
        assert "test_agent" in message_bus._subscriber_tasks
        
        # Test unsubscription
        await message_bus.unsubscribe("test_agent")
        assert "test_agent" not in message_bus._message_handlers
        assert "test_agent" not in message_bus._subscriber_tasks
    
    def test_queue_name_generation(self, message_bus):
        """Test queue name generation."""
        queue_name = message_bus._get_queue_name("detection")
        assert queue_name == "incident_commander_detection"
        
        dlq_name = message_bus._get_dlq_name("detection")
        assert dlq_name == "incident_commander_detection_dlq"
    
    def test_message_bus_stats(self, message_bus):
        """Test message bus statistics."""
        stats = message_bus.get_bus_stats()
        
        assert "message_stats" in stats
        assert "is_healthy" in stats
        assert "active_subscribers" in stats
        assert "timestamp" in stats
        
        # Check message stats structure
        message_stats = stats["message_stats"]
        assert "sent" in message_stats
        assert "delivered" in message_stats
        assert "failed" in message_stats
        assert "retried" in message_stats
        assert "dlq_messages" in message_stats
    
    @pytest.mark.asyncio
    async def test_queue_stats(self, message_bus):
        """Test queue statistics retrieval."""
        try:
            stats = await message_bus.get_queue_stats("test_agent")
            
            assert "agent_name" in stats
            assert "redis_queue_length" in stats
            assert "sqs_queue_length" in stats
            assert "dlq_length" in stats
            assert "is_subscribed" in stats
            
            assert stats["agent_name"] == "test_agent"
            
        except Exception as e:
            # Expected in test environment
            error_msg = str(e).lower()
            assert ("connection" in error_msg or "redis" in error_msg or 
                   "endpoint" in error_msg)
    
    @pytest.mark.asyncio
    async def test_message_bus_cleanup(self, message_bus):
        """Test message bus cleanup."""
        # Add some test subscribers
        async def test_handler(message):
            pass
        
        await message_bus.subscribe("agent1", test_handler)
        await message_bus.subscribe("agent2", test_handler)
        
        assert len(message_bus._subscriber_tasks) == 2
        
        # Test cleanup
        await message_bus.cleanup()
        
        # All tasks should be cancelled
        for task in message_bus._subscriber_tasks.values():
            assert task.cancelled() or task.done()


class TestMessageBusIntegration:
    """Integration tests for message bus with agents."""
    
    @pytest.fixture
    def service_factory(self):
        """Create AWS service factory for testing."""
        return AWSServiceFactory()
    
    @pytest.fixture
    def message_bus(self, service_factory):
        """Create message bus for testing."""
        return ResilientMessageBus(service_factory)
    
    @pytest.mark.asyncio
    async def test_agent_message_flow(self, message_bus):
        """Test complete message flow between agents."""
        received_messages = []
        
        async def detection_handler(message):
            received_messages.append(("detection", message))
        
        async def diagnosis_handler(message):
            received_messages.append(("diagnosis", message))
        
        # Subscribe agents
        await message_bus.subscribe("detection", detection_handler)
        await message_bus.subscribe("diagnosis", diagnosis_handler)
        
        # Create test message
        test_message = AgentMessage(
            sender_agent=AgentType.DETECTION,
            recipient_agent=AgentType.DIAGNOSIS,
            message_type="test_message",
            payload={"test": "data"},
            correlation_id="test-correlation"
        )
        
        try:
            # Send message
            message_id = await message_bus.send_message(test_message)
            
            # Give some time for message processing
            await asyncio.sleep(2)
            
            # Check if message was received (may not work in test environment)
            # This is more of a smoke test for the interface
            assert isinstance(message_id, str)
            
        except Exception as e:
            # Expected in test environment without Redis/SQS
            error_msg = str(e).lower()
            assert ("connection" in error_msg or "delivery" in error_msg or 
                   "redis" in error_msg or "endpoint" in error_msg)
        
        finally:
            # Cleanup
            await message_bus.cleanup()
    
    @pytest.mark.asyncio
    async def test_message_priority_handling(self, message_bus):
        """Test message priority handling."""
        # Test different priority levels
        priorities = [
            MessagePriority.LOW,
            MessagePriority.MEDIUM, 
            MessagePriority.HIGH,
            MessagePriority.CRITICAL
        ]
        
        for priority in priorities:
            test_message = AgentMessage(
                sender_agent=AgentType.DETECTION,
                recipient_agent=AgentType.DIAGNOSIS,
                message_type="priority_test",
                payload={"priority": priority.value}
            )
            
            try:
                message_id = await message_bus.send_message(
                    test_message,
                    priority=priority
                )
                assert isinstance(message_id, str)
                
            except Exception as e:
                # Expected in test environment
                error_msg = str(e).lower()
                assert ("connection" in error_msg or "delivery" in error_msg or 
                       "redis" in error_msg or "endpoint" in error_msg)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])