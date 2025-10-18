"""Lightweight agent instantiation checks derived from milestone scripts."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from agents.prediction.agent import PredictionAgent
from agents.resolution.agent import SecureResolutionAgent
from agents.communication.agent import ResilientCommunicationAgent
from src.models.incident import BusinessImpact, Incident, IncidentMetadata, ServiceTier


pytestmark = pytest.mark.manual


@pytest.fixture
def mock_incident() -> Incident:
    return Incident(
        id="test-agent-incident",
        title="Synthetic incident",
        description="Generated for agent smoke tests",
        severity="high",
        status="investigating",
        detected_at=datetime.utcnow(),
        business_impact=BusinessImpact(
            service_tier=ServiceTier.TIER_1,
            affected_users=5000,
        ),
        metadata=IncidentMetadata(
            source_system="pytest",
            tags={"service": "demo", "environment": "hackathon"},
        ),
    )


@pytest.fixture
def aws_factory() -> MagicMock:
    factory = MagicMock()
    cloudwatch_client = AsyncMock()
    cloudwatch_client.get_metric_statistics = AsyncMock(return_value={"Datapoints": []})
    factory.get_cloudwatch_client = AsyncMock(return_value=cloudwatch_client)
    factory.get_sts_client = AsyncMock(return_value=AsyncMock())
    return factory


@pytest.fixture
def rag_memory() -> MagicMock:
    memory = MagicMock()
    memory.search_similar_incidents = AsyncMock(return_value=[])
    return memory


@pytest.mark.asyncio
async def test_prediction_agent_health_snapshot(aws_factory: MagicMock, rag_memory: MagicMock, mock_incident: Incident) -> None:
    agent = PredictionAgent(aws_factory, rag_memory, "test_prediction")

    recommendation = await agent.process_incident(mock_incident)
    assert recommendation, "Prediction agent should return at least one recommendation"

    health = await agent.get_health_status()
    assert health["agent_type"] == "prediction"


@pytest.mark.asyncio
async def test_resolution_agent_starts_without_actions(aws_factory: MagicMock) -> None:
    agent = SecureResolutionAgent(aws_factory, "test_resolution")
    status = await agent.get_health_status()
    assert status["agent_id"] == "test_resolution"
    assert status["capacity"]["active_actions"] == 0


@pytest.mark.asyncio
async def test_communication_agent_health(mock_incident: Incident) -> None:
    agent = ResilientCommunicationAgent("test_communication")

    status = await agent.get_health_status()
    assert status["agent_id"] == "test_communication"
    assert status["active_notifications"] == 0
