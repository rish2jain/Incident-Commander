"""
Integration tests for Redis failover to SQS with retry and DLQ behavior.
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.message_bus import ResilientMessageBus
from src.models.agent import AgentMessage
from src.utils.exceptions import MessageBusError


class TestRedisFailover:
    """Test Redis failover scenarios and SQS fallback behavior."""
    
    @pytest.fixture
    async def message_bus(self):
        """Create message bus for testing."""
        # Mock Redis client that will fail
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = ConnectionError("Redis unavailable")
        
        # Mock SQS client for fallback
        mock_sqs = MagicMock()
        
        bus = ResilientMessageBus(redis_client=mock_redis)
        bus._sqs_client = mock_sqs
        
        return bus
    
    @pytest.fixture
    def sample_message(self):
        """Create sample agent message for testing."""
        return AgentMessage(
            sender_agent="test_sender",
            recipient_agent="test_recipient", 
            message_type="test_message",
            payload={"test": "data"},
            correlation_id="test-correlation-123"
        )
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure_triggers_sqs_fallback(self, message_bus, sample_message):
        """Test that Redis connection failure triggers SQS fallback."""
        # Configure SQS mock to succeed
        message_bus._sqs_client.send_message.return_value = {
            'MessageId': 'test-message-id',
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }
        
        # Attempt to send message - should fallback to SQS
        await message_bus.send_with_resilience(sample_message, "test_recipient")
        
        # Verify SQS was called as fallback
        message_bus._sqs_client.send_message.assert_called_once()
        call_args = message_bus._sqs_client.send_message.call_args
        
        assert 'QueueUrl' in call_args.kwargs
        assert 'MessageBody' in call_args.kwargs
        assert sample_message.correlation_id in call_args.kwargs['MessageBody']
    
    @pytest.mark.asyncio
    async def test_redis_timeout_triggers_sqs_fallback(self, message_bus, sample_message):
        """Test that Redis timeout triggers SQS fallback."""
        # Configure Redis to timeout
        message_bus._redis_client.lpush.side_effect = asyncio.TimeoutError("Redis timeout")
        
        # Configure SQS mock to succeed
        message_bus._sqs_client.send_message.return_value = {
            'MessageId': 'test-message-id',
            'ResponseMetadata': {'HTTPStatusCode': 200}
        }
        
        # Send message - should fallback to SQS after timeout
        await message_bus.send_with_resilience(sample_message, "test_recipient")
        
        # Verify SQS fallback was used
        message_bus._sqs_client.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_retry_behavior_with_exponential_backoff(self, message_bus, sample_message):
        """Test retry behavior with exponential backoff."""
        retry_attempts = []
        
        async def mock_send_with_delay(*args, **kwargs):
            retry_attempts.append(time.time())
            if len(retry_attempts) < 3:
                raise ConnectionError("Redis still unavailable")
            return True
        
        # Mock successful send after retries
        message_bus._redis_client.lpush = mock_send_with_delay
        
        start_time = time.time()
        await message_bus.send_with_resilience(sample_message, "test_recipient")
        
        # Verify retry attempts with exponential backoff
        assert len(retry_attempts) == 3
        
        # Check backoff timing (should increase exponentially)
        if len(retry_attempts) >= 2:
            first_delay = retry_attempts[1] - retry_attempts[0]
            second_delay = retry_attempts[2] - retry_attempts[1]
            assert second_delay > first_delay  # Exponential increase
    
    @pytest.mark.asyncio
    async def test_dlq_behavior_after_max_retries(self, message_bus, sample_message):
        """Test that messages go to DLQ after max retries."""
        # Configure both Redis and SQS to fail
        message_bus._redis_client.lpush.side_effect = ConnectionError("Redis unavailable")
        message_bus._sqs_client.send_message.side_effect = Exception("SQS also unavailable")
        
        # Mock DLQ
        message_bus._sqs_client.send_message_to_dlq = MagicMock()
        
        # Attempt to send message - should end up in DLQ
        with pytest.raises(MessageBusError):
            await message_bus.send_with_resilience(sample_message, "test_recipient")
        
        # Verify message was sent to DLQ
        message_bus._sqs_client.send_message_to_dlq.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_recovery_after_outage(self, sample_message):
        """Test Redis recovery after temporary outage."""
        # Create message bus with initially failing Redis
        mock_redis = AsyncMock()
        failure_count = 0
        
        async def mock_redis_with_recovery(*args, **kwargs):
            nonlocal failure_count
            failure_count += 1
            if failure_count <= 2:
                raise ConnectionError("Redis temporarily unavailable")
            return True  # Redis recovers
        
        mock_redis.lpush = mock_redis_with_recovery
        mock_redis.ping = mock_redis_with_recovery
        
        bus = ResilientMessageBus(redis_client=mock_redis)
        
        # First attempt should fail and use SQS
        bus._sqs_client = MagicMock()
        bus._sqs_client.send_message.return_value = {'MessageId': 'test-id'}
        
        await bus.send_with_resilience(sample_message, "test_recipient")
        
        # Verify SQS was used initially
        bus._sqs_client.send_message.assert_called()
        
        # Reset SQS mock
        bus._sqs_client.reset_mock()
        
        # Second attempt should succeed with Redis (after recovery)
        await bus.send_with_resilience(sample_message, "test_recipient")
        
        # Verify Redis was used (SQS not called)
        bus._sqs_client.send_message.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_message_ordering_during_failover(self, message_bus):
        """Test message ordering is preserved during failover."""
        messages = []
        for i in range(5):
            msg = AgentMessage(
                sender_agent="test_sender",
                recipient_agent="test_recipient",
                message_type="ordered_message",
                payload={"sequence": i},
                correlation_id=f"test-{i}"
            )
            messages.append(msg)
        
        # Configure SQS to capture message order
        sent_messages = []
        
        def capture_message(*args, **kwargs):
            sent_messages.append(kwargs['MessageBody'])
            return {'MessageId': f'msg-{len(sent_messages)}'}
        
        message_bus._sqs_client.send_message.side_effect = capture_message
        
        # Send messages in order
        for msg in messages:
            await message_bus.send_with_resilience(msg, "test_recipient")
        
        # Verify messages were sent in correct order
        assert len(sent_messages) == 5
        for i, sent_msg in enumerate(sent_messages):
            assert f'"sequence": {i}' in sent_msg
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration_with_failover(self, message_bus, sample_message):
        """Test circuit breaker integration with Redis failover."""
        from src.services.circuit_breaker import circuit_breaker_manager
        
        # Get circuit breaker for message bus
        circuit_breaker = circuit_breaker_manager.get_service_circuit_breaker("message_bus")
        
        # Configure Redis to fail consistently
        message_bus._redis_client.lpush.side_effect = ConnectionError("Redis down")
        
        # Configure SQS to succeed
        message_bus._sqs_client.send_message.return_value = {'MessageId': 'test-id'}
        
        # Send multiple messages to trigger circuit breaker
        for _ in range(6):  # Exceed failure threshold
            await message_bus.send_with_resilience(sample_message, "test_recipient")
        
        # Verify circuit breaker opened for Redis
        assert circuit_breaker.failure_count >= 5
        
        # Verify SQS was used as fallback
        assert message_bus._sqs_client.send_message.call_count >= 6
    
    @pytest.mark.asyncio
    async def test_message_deduplication_during_failover(self, message_bus, sample_message):
        """Test message deduplication during Redis failover."""
        # Configure message bus to track sent messages
        sent_message_ids = set()
        
        def track_sqs_messages(*args, **kwargs):
            message_body = kwargs['MessageBody']
            # Extract correlation ID for deduplication
            import json
            msg_data = json.loads(message_body)
            correlation_id = msg_data.get('correlation_id')
            
            if correlation_id in sent_message_ids:
                raise Exception("Duplicate message detected")
            
            sent_message_ids.add(correlation_id)
            return {'MessageId': f'msg-{correlation_id}'}
        
        message_bus._sqs_client.send_message.side_effect = track_sqs_messages
        
        # Send same message multiple times (simulating retry scenarios)
        for _ in range(3):
            await message_bus.send_with_resilience(sample_message, "test_recipient")
        
        # Verify only one unique message was sent
        assert len(sent_message_ids) == 1
        assert sample_message.correlation_id in sent_message_ids
    
    @pytest.mark.asyncio
    async def test_performance_during_redis_outage(self, message_bus, sample_message):
        """Test performance characteristics during Redis outage."""
        # Configure Redis to fail with delay (simulating network timeout)
        async def slow_redis_failure(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms delay
            raise ConnectionError("Redis timeout")
        
        message_bus._redis_client.lpush = slow_redis_failure
        
        # Configure fast SQS fallback
        message_bus._sqs_client.send_message.return_value = {'MessageId': 'test-id'}
        
        # Measure failover time
        start_time = time.time()
        await message_bus.send_with_resilience(sample_message, "test_recipient")
        failover_time = time.time() - start_time
        
        # Verify failover completed within reasonable time (< 1 second)
        assert failover_time < 1.0
        
        # Verify SQS was used
        message_bus._sqs_client.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_redis_failover_integration_scenario():
    """Integration test simulating complete Redis failover scenario."""
    
    # Simulate Redis cluster failure
    with patch('redis.asyncio.Redis') as mock_redis_class:
        # Configure Redis to fail
        mock_redis = AsyncMock()
        mock_redis.ping.side_effect = ConnectionError("Redis cluster down")
        mock_redis.lpush.side_effect = ConnectionError("Redis cluster down")
        mock_redis_class.return_value = mock_redis
        
        # Create message bus
        bus = ResilientMessageBus()
        
        # Mock SQS for fallback
        bus._sqs_client = MagicMock()
        bus._sqs_client.send_message.return_value = {'MessageId': 'fallback-msg'}
        
        # Create test message
        test_message = AgentMessage(
            sender_agent="detection_agent",
            recipient_agent="diagnosis_agent",
            message_type="incident_detected",
            payload={"incident_id": "test-incident-123"},
            correlation_id="integration-test-correlation"
        )
        
        # Send message during Redis outage
        await bus.send_with_resilience(test_message, "diagnosis_agent")
        
        # Verify SQS fallback was used
        bus._sqs_client.send_message.assert_called_once()
        
        # Verify message content was preserved
        call_args = bus._sqs_client.send_message.call_args
        message_body = call_args.kwargs['MessageBody']
        assert "test-incident-123" in message_body
        assert "integration-test-correlation" in message_body