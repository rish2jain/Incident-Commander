import asyncio
from datetime import datetime, timedelta

import pytest

from src.models.agent import AgentMessage, AgentType
from src.services.message_bus import MessagePriority, MessageEnvelope, ResilientMessageBus


class StubSQSClient:
    def __init__(self):
        self.queues = {}

    async def get_queue_url(self, QueueName):
        if QueueName not in self.queues:
            raise self._not_found()
        return {"QueueUrl": QueueName}

    async def create_queue(self, QueueName, Attributes):
        self.queues[QueueName] = {"Attributes": Attributes, "Messages": []}
        return {"QueueUrl": QueueName}

    async def send_message(self, QueueUrl, MessageBody, MessageAttributes=None):
        queue = self.queues.setdefault(QueueUrl, {"Attributes": {}, "Messages": []})
        queue["Messages"].append(MessageBody)

    async def delete_message(self, QueueUrl, ReceiptHandle):
        return None

    async def receive_message(self, QueueUrl, MaxNumberOfMessages=1, WaitTimeSeconds=0, MessageAttributeNames=None):
        return {"Messages": []}

    async def get_queue_attributes(self, QueueUrl, AttributeNames):
        queue = self.queues.setdefault(QueueUrl, {"Attributes": {}, "Messages": []})
        return {"Attributes": {"ApproximateNumberOfMessages": str(len(queue["Messages"]))}}

    async def close(self):
        return None

    @staticmethod
    def _not_found():
        from botocore.exceptions import ClientError

        return ClientError(
            {
                "Error": {
                    "Code": "AWS.SimpleQueueService.NonExistentQueue",
                    "Message": "Queue does not exist"
                }
            },
            "GetQueueUrl"
        )


class StubAWSFactory:
    def __init__(self):
        self.client = StubSQSClient()

    async def create_client(self, service_name: str, **kwargs):
        return self.client

    async def close_client(self, client):
        await client.close()

    async def cleanup(self):
        await self.close_client(self.client)


@pytest.mark.asyncio
async def test_send_message_falls_back_to_sqs(monkeypatch):
    factory = StubAWSFactory()
    bus = ResilientMessageBus(factory)

    async def failing_send(_):
        raise RuntimeError("redis unavailable")

    sent_envelopes = []

    async def capture_sqs(envelope):
        sent_envelopes.append(envelope)

    monkeypatch.setattr(bus, "_send_via_redis", failing_send)
    monkeypatch.setattr(bus, "_send_via_sqs", capture_sqs)

    message = AgentMessage(
        sender_agent=AgentType.DETECTION,
        recipient_agent=AgentType.RESOLUTION,
        message_type="test",
        payload={},
        correlation_id="corr-123"
    )

    message_id = await bus.send_message(message)

    assert sent_envelopes, "SQS fallback should capture envelope"
    assert sent_envelopes[0].message_id == message_id
    assert bus._message_stats["sent"] == 1

    await bus.shutdown()


@pytest.mark.asyncio
async def test_failed_handler_schedules_retry(monkeypatch):
    factory = StubAWSFactory()
    bus = ResilientMessageBus(factory)

    envelope = MessageEnvelope(
        message_id="msg-1",
        sender_agent="detection",
        recipient_agent="resolution",
        message_type="update",
        payload={},
        priority=MessagePriority.MEDIUM,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        correlation_id="corr-1"
    )

    async def failing_handler(_):
        raise RuntimeError("processing failed")

    bus._message_handlers["resolution"] = failing_handler

    redis_calls = []

    async def capture_retry(env):
        redis_calls.append(env.message_id)

    monkeypatch.setattr(bus, "_send_via_redis", capture_retry)

    async def instant_sleep(_):
        return None

    monkeypatch.setattr("src.services.message_bus.asyncio.sleep", instant_sleep)

    await bus._process_message("resolution", envelope)

    await asyncio.sleep(0)

    # Allow scheduled retry task to execute
    pending = list(bus._retry_tasks)
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)

    assert redis_calls == ["msg-1"], "Retry should requeue message via Redis"
    assert bus._message_stats["retried"] == 1
    assert envelope.retry_count == 1

    await bus.shutdown()
