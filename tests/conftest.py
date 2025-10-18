"""
Test configuration and fixtures for Incident Commander.
"""

import os
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from typing import AsyncGenerator, Generator

# Set up test environment variables before any imports
os.environ.setdefault('AWS_ACCESS_KEY_ID', 'test-access-key')
os.environ.setdefault('AWS_SECRET_ACCESS_KEY', 'test-secret-key')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')
os.environ.setdefault('AWS_REGION', 'us-east-1')
os.environ.setdefault('ENVIRONMENT', 'test')
os.environ.setdefault('DEBUG', 'true')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379')
os.environ.setdefault('AWS_ENDPOINT_URL', 'http://localhost:4566')


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_aws_service_factory():
    """Mock AWS service factory for testing."""
    from src.services.aws import AWSServiceFactory
    
    factory = MagicMock(spec=AWSServiceFactory)
    factory.get_bedrock_client = AsyncMock()
    factory.get_dynamodb_client = AsyncMock()
    factory.get_s3_client = AsyncMock()
    factory.get_kinesis_client = AsyncMock()
    factory.get_cloudwatch_client = AsyncMock()
    
    return factory


@pytest.fixture
async def mock_redis_client():
    """Mock Redis client for testing."""
    import redis.asyncio as redis
    
    client = AsyncMock(spec=redis.Redis)
    client.ping = AsyncMock(return_value=True)
    client.set = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)
    client.delete = AsyncMock(return_value=1)
    client.exists = AsyncMock(return_value=False)
    client.lpush = AsyncMock(return_value=1)
    client.rpop = AsyncMock(return_value=None)
    client.llen = AsyncMock(return_value=0)
    
    return client


@pytest.fixture
def mock_incident():
    """Create a mock incident for testing."""
    from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
    from datetime import datetime
    
    return Incident(
        id="test-incident-123",
        title="Test Database Connection Timeout",
        description="Database connections are timing out",
        severity=IncidentSeverity.HIGH,
        service_tier=ServiceTier.TIER_1,
        business_impact=BusinessImpact.CUSTOMER_FACING,
        metadata=IncidentMetadata(
            source="test",
            tags=["database", "timeout"],
            affected_services=["user-service", "payment-service"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    )


@pytest.fixture
def mock_agent_message():
    """Create a mock agent message for testing."""
    from src.models.agent import AgentMessage, AgentType
    from datetime import datetime
    
    return AgentMessage(
        id="test-message-123",
        sender=AgentType.DETECTION,
        recipient=AgentType.DIAGNOSIS,
        content={"alert": "High CPU usage detected"},
        timestamp=datetime.utcnow(),
        priority=1,
        correlation_id="test-correlation-123"
    )


@pytest.fixture
async def mock_message_bus():
    """Mock message bus for testing."""
    from src.services.message_bus import ResilientMessageBus
    
    bus = AsyncMock(spec=ResilientMessageBus)
    bus.send_message = AsyncMock()
    bus.receive_message = AsyncMock()
    bus.health_check = AsyncMock(return_value=True)
    
    return bus


@pytest.fixture
def mock_circuit_breaker():
    """Mock circuit breaker for testing."""
    from src.services.circuit_breaker import AgentCircuitBreakerImpl
    
    breaker = MagicMock(spec=AgentCircuitBreakerImpl)
    breaker.call = AsyncMock()
    breaker.is_open = False
    breaker.failure_count = 0
    
    return breaker


# Auto-use fixtures for common test setup
@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables automatically."""
    # Ensure test environment is properly configured
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['DEBUG'] = 'true'
    
    # Mock external service endpoints
    os.environ['DATADOG_API_KEY'] = 'test-datadog-key'
    os.environ['PAGERDUTY_API_KEY'] = 'test-pagerduty-key'
    os.environ['SLACK_BOT_TOKEN'] = 'test-slack-token'
    
    yield
    
    # Cleanup if needed
    pass


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    import logging
    
    logger = MagicMock(spec=logging.Logger)
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.debug = MagicMock()
    
    return logger


def pytest_configure(config):
    """Register custom markers for strict marker enforcement."""

    config.addinivalue_line(
        "markers",
        "manual: marks tests that exercise hackathon/demo flows",
    )
