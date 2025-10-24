"""
Resilient inter-agent message bus with Redis and SQS integration.
"""

import asyncio
import json
import os
import random
import time
from collections import defaultdict
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import uuid4

import redis.asyncio as redis
import aioboto3
from botocore.exceptions import ClientError

from src.models.agent import AgentMessage, AgentType
from src.services.aws import AWSServiceFactory
from src.services.circuit_breaker import circuit_breaker_manager
from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.exceptions import MessageBusError, MessageDeliveryError


logger = get_logger("message_bus")


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MessageEnvelope:
    """Message envelope with routing and delivery metadata."""
    message_id: str
    sender_agent: str
    recipient_agent: str
    message_type: str
    payload: Dict[str, Any]
    priority: MessagePriority
    created_at: datetime
    expires_at: datetime
    retry_count: int = 0
    max_retries: int = 3
    correlation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "message_id": self.message_id,
            "sender_agent": self.sender_agent,
            "recipient_agent": self.recipient_agent,
            "message_type": self.message_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "correlation_id": self.correlation_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MessageEnvelope":
        """Create from dictionary."""
        return cls(
            message_id=data["message_id"],
            sender_agent=data["sender_agent"],
            recipient_agent=data["recipient_agent"],
            message_type=data["message_type"],
            payload=data["payload"],
            priority=MessagePriority(data["priority"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            correlation_id=data.get("correlation_id")
        )
    
    def is_expired(self) -> bool:
        """Check if message has expired."""
        return datetime.utcnow() > self.expires_at
    
    def should_retry(self) -> bool:
        """Check if message should be retried."""
        return self.retry_count < self.max_retries and not self.is_expired()


class ResilientMessageBus:
    """Resilient message bus with Redis and SQS backends."""
    
    def __init__(self, service_factory: AWSServiceFactory):
        """Initialize message bus."""
        self._service_factory = service_factory
        self._redis_client = None
        self._sqs_client = None
        self._message_breaker = circuit_breaker_manager.get_circuit_breaker("message_bus")

        # Configuration
        self._redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self._queue_prefix = "incident_commander"
        self._dlq_suffix = "_dlq"

        # Message handlers
        self._message_handlers: Dict[str, Callable] = {}
        self._subscriber_tasks: Dict[str, asyncio.Task] = {}
        self._subscriber_failures: Dict[str, int] = defaultdict(int)
        self._retry_tasks: Set[asyncio.Task] = set()
        self._shutdown = False
        self._task_lock = asyncio.Lock()

        # Performance tracking
        self._message_stats = {
            "sent": 0,
            "delivered": 0,
            "failed": 0,
            "retried": 0,
            "dlq_messages": 0
        }
        
        # Circuit breaker for message bus health
        self._consecutive_failures = 0
        self._max_failures = 10
        self._is_healthy = True
    
    async def _get_redis_client(self) -> redis.Redis:
        """Get or create Redis client."""
        if not self._redis_client:
            self._redis_client = redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            try:
                await self._redis_client.ping()
                logger.info("Connected to Redis message bus")
                self._message_breaker.record_success()
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._message_breaker.record_failure()
                raise MessageBusError(f"Redis connection failed: {e}")

        return self._redis_client
    
    async def _get_sqs_client(self):
        """Get or create SQS client."""
        if not self._sqs_client:
            try:
                self._sqs_client = await self._service_factory.create_client('sqs')
                self._message_breaker.record_success()
            except Exception as exc:
                self._message_breaker.record_failure()
                logger.error(f"Failed to create SQS client: {exc}")
                raise
        return self._sqs_client
    
    def _get_queue_name(self, agent_name: str) -> str:
        """Get queue name for agent."""
        return f"{self._queue_prefix}_{agent_name}"
    
    def _get_dlq_name(self, agent_name: str) -> str:
        """Get dead letter queue name for agent."""
        return f"{self._queue_prefix}_{agent_name}{self._dlq_suffix}"
    
    async def send_with_resilience(self, message: AgentMessage, target_agent: str,
                                  priority: MessagePriority = MessagePriority.MEDIUM,
                                  ttl_seconds: int = 300) -> str:
        """
        Send message with resilience, retry logic, and exponential backoff.
        
        Args:
            message: Agent message to send
            target_agent: Target agent name
            priority: Message priority
            ttl_seconds: Time to live in seconds
            
        Returns:
            Message ID
        """
        max_retries = 3
        base_delay = 1.0  # Base delay in seconds
        
        for attempt in range(max_retries + 1):
            try:
                return await self.send_message(message, priority, ttl_seconds)
                
            except Exception as e:
                if attempt == max_retries:
                    # Final attempt failed, send to DLQ
                    await self.send_to_dlq(message, target_agent, str(e))
                    raise MessageBusError(f"All retry attempts failed: {e}")
                
                # Calculate delay with exponential backoff and jitter
                delay = base_delay * (2 ** attempt)
                jitter = delay * 0.1 * (0.5 - asyncio.get_event_loop().time() % 1)  # ±10% jitter
                total_delay = delay + jitter
                
                logger.warning(f"Send attempt {attempt + 1} failed, retrying in {total_delay:.2f}s: {e}")
                await asyncio.sleep(total_delay)
    
    async def send_message(self, message: AgentMessage, 
                          priority: MessagePriority = MessagePriority.MEDIUM,
                          ttl_seconds: int = 300) -> str:
        """
        Send message to recipient agent.
        
        Args:
            message: Agent message to send
            priority: Message priority
            ttl_seconds: Time to live in seconds
            
        Returns:
            Message ID
        """
        try:
            # Create message envelope
            envelope = MessageEnvelope(
                message_id=str(uuid4()),
                sender_agent=message.sender_agent.value if hasattr(message.sender_agent, 'value') else str(message.sender_agent),
                recipient_agent=message.recipient_agent.value if hasattr(message.recipient_agent, 'value') else str(message.recipient_agent),
                message_type=message.message_type,
                payload=message.payload,
                priority=priority,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=ttl_seconds),
                correlation_id=message.correlation_id
            )
            
            # Try Redis first (fast path)
            try:
                await self._send_via_redis(envelope)
                self._message_stats["sent"] += 1
                self._consecutive_failures = 0
                
                logger.debug(f"Sent message {envelope.message_id} via Redis")
                return envelope.message_id
                
            except Exception as redis_error:
                logger.warning(f"Redis send failed, falling back to SQS: {redis_error}")
                
                # Fallback to SQS (reliable path)
                await self._send_via_sqs(envelope)
                self._message_stats["sent"] += 1
                self._consecutive_failures = 0
                
                logger.debug(f"Sent message {envelope.message_id} via SQS")
                return envelope.message_id
            
        except Exception as e:
            self._consecutive_failures += 1
            self._message_stats["failed"] += 1
            
            if self._consecutive_failures >= self._max_failures:
                self._is_healthy = False
                logger.error("Message bus marked as unhealthy due to consecutive failures")
            
            logger.error(f"Failed to send message: {e}")
            raise MessageDeliveryError(f"Message delivery failed: {e}")
    
    async def _send_via_redis(self, envelope: MessageEnvelope) -> None:
        """Send message via Redis."""
        redis_client = await self._get_redis_client()

        queue_name = self._get_queue_name(envelope.recipient_agent)
        message_data = json.dumps(envelope.to_dict())

        try:
            if envelope.priority in [MessagePriority.HIGH, MessagePriority.CRITICAL]:
                await redis_client.lpush(queue_name, message_data)
            else:
                await redis_client.rpush(queue_name, message_data)

            ttl_seconds = max(1, int(envelope.expires_at.timestamp() - datetime.utcnow().timestamp()))
            await redis_client.expire(queue_name, ttl_seconds)
            self._message_breaker.record_success()

        except Exception as exc:
            self._message_breaker.record_failure()
            logger.error(f"Redis send failed: {exc}")
            raise
    
    async def _send_via_sqs(self, envelope: MessageEnvelope) -> None:
        """Send message via SQS."""
        sqs_client = await self._get_sqs_client()
        
        queue_name = self._get_queue_name(envelope.recipient_agent)
        
        try:
            queue_url = await self._get_or_create_sqs_queue(envelope.recipient_agent)
            
            # Send message
            await sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(envelope.to_dict()),
                MessageAttributes={
                    "Priority": {
                        "StringValue": envelope.priority.value,
                        "DataType": "String"
                    },
                    "MessageType": {
                        "StringValue": envelope.message_type,
                        "DataType": "String"
                    }
                }
            )
            self._message_breaker.record_success()
            
        except Exception as e:
            logger.error(f"SQS send failed: {e}")
            self._message_breaker.record_failure()
            raise
    
    async def _get_or_create_sqs_queue(self, agent_name: str, *, dlq: bool = False) -> str:
        """Get or create SQS queue and return URL."""
        sqs_client = await self._get_sqs_client()

        queue_name = self._get_dlq_name(agent_name) if dlq else self._get_queue_name(agent_name)

        try:
            response = await sqs_client.get_queue_url(QueueName=queue_name)
            return response["QueueUrl"]

        except ClientError as e:
            error = e.response.get("Error", {})
            if error.get("Code") != "AWS.SimpleQueueService.NonExistentQueue":
                raise

            attributes = {
                "VisibilityTimeout": "30",
                "MessageRetentionPeriod": "1209600",
                "ReceiveMessageWaitTimeSeconds": "20"
            }

            if not dlq:
                dlq_url = await self._get_or_create_sqs_queue(agent_name, dlq=True)
                dlq_attrs = await sqs_client.get_queue_attributes(
                    QueueUrl=dlq_url,
                    AttributeNames=["QueueArn"]
                )
                dlq_arn = dlq_attrs["Attributes"]["QueueArn"]
                attributes["RedrivePolicy"] = json.dumps({
                    "deadLetterTargetArn": dlq_arn,
                    "maxReceiveCount": "5"
                })

            response = await sqs_client.create_queue(
                QueueName=queue_name,
                Attributes=attributes
            )
            logger.info(f"Created SQS queue {queue_name}")
            return response["QueueUrl"]
    
    async def subscribe(self, agent_name: str, 
                       message_handler: Callable[[AgentMessage], None]) -> None:
        """
        Subscribe agent to receive messages.
        
        Args:
            agent_name: Name of the agent
            message_handler: Function to handle received messages
        """
        self._message_handlers[agent_name] = message_handler
        
        # Start subscriber task
        task = asyncio.create_task(self._message_subscriber(agent_name))
        self._subscriber_tasks[agent_name] = task
        
        logger.info(f"Agent {agent_name} subscribed to message bus")
    
    async def unsubscribe(self, agent_name: str) -> None:
        """Unsubscribe agent from message bus."""
        if agent_name in self._subscriber_tasks:
            task = self._subscriber_tasks[agent_name]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            del self._subscriber_tasks[agent_name]
        
        if agent_name in self._message_handlers:
            del self._message_handlers[agent_name]
        
        logger.info(f"Agent {agent_name} unsubscribed from message bus")
    
    async def _message_subscriber(self, agent_name: str) -> None:
        """Message subscriber loop for an agent."""
        while not self._shutdown:
            try:
                # Try Redis first
                message = await self._receive_from_redis(agent_name)
                
                if not message:
                    # Fallback to SQS
                    message = await self._receive_from_sqs(agent_name)
                
                if message:
                    await self._process_message(agent_name, message)
                    self._subscriber_failures[agent_name] = 0
                else:
                    # No messages, brief pause
                    await asyncio.sleep(0.5)
                
            except asyncio.CancelledError:
                logger.info(f"Message subscriber for {agent_name} cancelled")
                break
            except Exception as e:
                self._subscriber_failures[agent_name] += 1
                failure_count = self._subscriber_failures[agent_name]
                delay = min(30.0, 0.5 * (2 ** failure_count)) + random.uniform(0, 0.5)
                self._message_breaker.record_failure()
                logger.error(f"Error in message subscriber for {agent_name}: {e}. Backing off for {delay:.2f}s")
                await asyncio.sleep(delay)

        logger.info(f"Message subscriber for {agent_name} stopped (shutdown={self._shutdown})")
    
    async def _receive_from_redis(self, agent_name: str) -> Optional[MessageEnvelope]:
        """Receive message from Redis."""
        try:
            redis_client = await self._get_redis_client()
            queue_name = self._get_queue_name(agent_name)
            
            # Non-blocking pop from queue
            message_data = await redis_client.lpop(queue_name)
            
            if message_data:
                envelope = MessageEnvelope.from_dict(json.loads(message_data))
                
                # Check if message expired
                if envelope.is_expired():
                    logger.warning(f"Discarding expired message {envelope.message_id}")
                    return None
                
                self._message_breaker.record_success()
                return envelope
            
            return None
            
        except Exception as e:
            logger.warning(f"Redis receive failed: {e}")
            self._message_breaker.record_failure()
            return None
    
    async def _receive_from_sqs(self, agent_name: str) -> Optional[MessageEnvelope]:
        """Receive message from SQS."""
        try:
            sqs_client = await self._get_sqs_client()
            queue_url = await self._get_or_create_sqs_queue(agent_name)

            # Receive message with long polling
            response = await sqs_client.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=5,
                MessageAttributeNames=["All"]
            )
            
            messages = response.get("Messages", [])
            if messages:
                sqs_message = messages[0]
                envelope = MessageEnvelope.from_dict(json.loads(sqs_message["Body"]))
                
                # Delete message from queue
                await sqs_client.delete_message(
                    QueueUrl=queue_url,
                    ReceiptHandle=sqs_message["ReceiptHandle"]
                )
                
                # Check if message expired
                if envelope.is_expired():
                    logger.warning(f"Discarding expired message {envelope.message_id}")
                    return None
                
                self._message_breaker.record_success()
                return envelope
            
            return None
            
        except Exception as e:
            logger.warning(f"SQS receive failed: {e}")
            self._message_breaker.record_failure()
            return None
    
    async def _process_message(self, agent_name: str, envelope: MessageEnvelope) -> None:
        """Process received message."""
        try:
            # Convert envelope back to AgentMessage
            agent_message = AgentMessage(
                sender_agent=AgentType(envelope.sender_agent),
                recipient_agent=AgentType(envelope.recipient_agent),
                message_type=envelope.message_type,
                payload=envelope.payload,
                correlation_id=envelope.correlation_id
            )
            
            # Call message handler
            handler = self._message_handlers.get(agent_name)
            if handler:
                await handler(agent_message)
                self._message_stats["delivered"] += 1
                self._message_breaker.record_success()
                logger.debug(f"Delivered message {envelope.message_id} to {agent_name}")
            else:
                logger.warning(f"No handler for agent {agent_name}")
                self._message_breaker.record_failure()
                await self._send_to_dlq(envelope, "No message handler")
            
        except Exception as e:
            logger.error(f"Failed to process message {envelope.message_id}: {e}")
            self._message_breaker.record_failure()
            
            # Retry logic
            if envelope.should_retry():
                envelope.retry_count += 1
                self._message_stats["retried"] += 1
                self._schedule_retry(envelope)
            else:
                await self._send_to_dlq(envelope, f"Max retries exceeded: {e}")

    def _schedule_retry(self, envelope: MessageEnvelope) -> None:
        """Schedule a retry with exponential backoff and jitter."""
        if self._shutdown:
            logger.debug(f"Skipping retry for {envelope.message_id}; bus shutting down")
            return

        base_delay = min(300.0, float(2 ** envelope.retry_count))
        jitter = max(0.1, base_delay * 0.1)
        delay = max(0.1, base_delay + random.uniform(-jitter, jitter))

        async def _retry() -> None:
            try:
                await asyncio.sleep(delay)
                await self._send_via_redis(envelope)
                logger.info(
                    f"Retrying message {envelope.message_id} (attempt {envelope.retry_count}) after {delay:.2f}s"
                )
            except Exception as exc:
                await self._send_to_dlq(envelope, f"Retry failed: {exc}")

        task = asyncio.create_task(_retry())

        def _cleanup(t: asyncio.Task) -> None:
            with suppress(Exception):
                t.result()
            self._retry_tasks.discard(t)

        task.add_done_callback(_cleanup)
        self._retry_tasks.add(task)
    
    async def _send_to_dlq(self, envelope: MessageEnvelope, reason: str) -> None:
        """Send message to dead letter queue."""
        try:
            dlq_name = self._get_dlq_name(envelope.recipient_agent)

            dlq_envelope = envelope
            dlq_envelope.payload["dlq_reason"] = reason
            dlq_envelope.payload["dlq_timestamp"] = datetime.utcnow().isoformat()

            try:
                redis_client = await self._get_redis_client()
                await redis_client.lpush(dlq_name, json.dumps(dlq_envelope.to_dict()))
            except Exception:
                sqs_client = await self._get_sqs_client()
                dlq_url = await self._get_or_create_sqs_queue(envelope.recipient_agent, dlq=True)

                await sqs_client.send_message(
                    QueueUrl=dlq_url,
                    MessageBody=json.dumps(dlq_envelope.to_dict())
                )

            self._message_stats["dlq_messages"] += 1
            logger.warning(f"Sent message {envelope.message_id} to DLQ: {reason}")
            
        except Exception as e:
            logger.error(f"Failed to send message to DLQ: {e}")
    
    async def get_queue_stats(self, agent_name: str) -> Dict[str, Any]:
        """Get queue statistics for an agent."""
        stats = {
            "agent_name": agent_name,
            "redis_queue_length": 0,
            "sqs_queue_length": 0,
            "dlq_length": 0,
            "is_subscribed": agent_name in self._message_handlers
        }
        
        try:
            # Redis queue length
            redis_client = await self._get_redis_client()
            queue_name = self._get_queue_name(agent_name)
            stats["redis_queue_length"] = await redis_client.llen(queue_name)
            
            # DLQ length
            dlq_name = self._get_dlq_name(agent_name)
            stats["dlq_length"] = await redis_client.llen(dlq_name)
            
        except Exception as e:
            logger.warning(f"Failed to get Redis queue stats: {e}")
        
        try:
            sqs_client = await self._get_sqs_client()
            queue_url = await self._get_or_create_sqs_queue(agent_name)

            response = await sqs_client.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["ApproximateNumberOfMessages"]
            )

            stats["sqs_queue_length"] = int(response["Attributes"].get("ApproximateNumberOfMessages", "0"))

        except Exception as e:
            logger.warning(f"Failed to get SQS queue stats: {e}")

        return stats

    def update_service_factory(self, service_factory: AWSServiceFactory) -> None:
        """Update AWS service factory used by the message bus."""
        if service_factory is None or service_factory is self._service_factory:
            return
        self._service_factory = service_factory

    async def shutdown(self) -> None:
        """Shutdown message bus, cancelling subscribers and closing connections."""
        if self._shutdown:
            return

        self._shutdown = True

        # Cancel subscriber tasks
        for task in list(self._subscriber_tasks.values()):
            task.cancel()
        for task in list(self._subscriber_tasks.values()):
            with suppress(Exception):
                await task
        self._subscriber_tasks.clear()

        # Cancel retry tasks
        for task in list(self._retry_tasks):
            task.cancel()
        for task in list(self._retry_tasks):
            with suppress(Exception):
                await task
        self._retry_tasks.clear()

        # Close Redis client
        if self._redis_client:
            try:
                await self._redis_client.close()
            except Exception as exc:
                logger.warning(f"Error closing Redis client: {exc}")
            try:
                await self._redis_client.connection_pool.disconnect()
            except Exception:
                pass
            self._redis_client = None

        # Close SQS client via factory helper
        if self._sqs_client:
            await self._service_factory.close_client(self._sqs_client)
            self._sqs_client = None

        logger.info("Message bus shutdown complete")
    
    def get_bus_stats(self) -> Dict[str, Any]:
        """Get overall message bus statistics."""
        return {
            "message_stats": self._message_stats.copy(),
            "is_healthy": self._is_healthy,
            "consecutive_failures": self._consecutive_failures,
            "active_subscribers": len(self._subscriber_tasks),
            "registered_handlers": len(self._message_handlers),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def health_check(self) -> bool:
        """Perform health check on message bus."""
        try:
            # Test Redis connectivity
            redis_client = await self._get_redis_client()
            await redis_client.ping()
            
            # Test SQS connectivity
            sqs_client = await self._get_sqs_client()
            await sqs_client.list_queues(QueueNamePrefix=self._queue_prefix)
            
            self._is_healthy = True
            self._consecutive_failures = 0
            return True
            
        except Exception as e:
            logger.error(f"Message bus health check failed: {e}")
            self._is_healthy = False
            return False
    
    async def send_to_dlq(self, message: AgentMessage, target_agent: str, error_reason: str) -> None:
        """Send message to dead letter queue after all retries failed."""
        try:
            # Create envelope for DLQ
            envelope = MessageEnvelope(
                message_id=str(uuid4()),
                sender_agent=message.sender_agent.value if hasattr(message.sender_agent, 'value') else str(message.sender_agent),
                recipient_agent=target_agent,
                message_type=message.message_type,
                payload={**message.payload, "dlq_reason": error_reason, "dlq_timestamp": datetime.utcnow().isoformat()},
                priority=MessagePriority.LOW,  # DLQ messages are low priority
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=7),  # Keep DLQ messages for 7 days
                correlation_id=message.correlation_id
            )
            
            await self._send_to_dlq(envelope, error_reason)
            
        except Exception as e:
            logger.error(f"Failed to send message to DLQ: {e}")
    
    async def cleanup(self) -> None:
        """Cleanup message bus resources with proper task cancellation."""
        logger.info("Starting message bus cleanup")
        await self.shutdown()
        logger.info("Message bus cleanup completed")


# Global message bus instance
message_bus: Optional[ResilientMessageBus] = None


def get_message_bus(service_factory: AWSServiceFactory) -> ResilientMessageBus:
    """Get or create global message bus instance."""
    global message_bus
    if message_bus is None:
        message_bus = ResilientMessageBus(service_factory)
    else:
        message_bus.update_service_factory(service_factory)
    return message_bus
