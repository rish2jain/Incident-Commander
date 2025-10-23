"""Updated comprehensive unit tests aligned with current architecture."""

import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from agents.detection.agent import RobustDetectionAgent
from agents.diagnosis.agent import HardenedDiagnosisAgent
from src.models.agent import (
    ActionType,
    AgentRecommendation,
    AgentType,
    RiskLevel,
)
from src.models.incident import (
    BusinessImpact,
    Incident,
    IncidentMetadata,
    IncidentSeverity,
    ServiceTier,
)
from src.services.circuit_breaker import (
    CircuitBreakerManagerImpl,
    CircuitBreakerState,
    ResilientCircuitBreaker,
)
from src.services.consensus import BasicWeightedConsensusEngine
from src.services.rate_limiter import (
    BedrockRateLimitManager,
    ExternalServiceRateLimiter,
    RequestPriority,
)
from src.utils.exceptions import CircuitBreakerOpenError, RateLimitError


@pytest.fixture
def sample_incident() -> Incident:
    """Create a reusable incident instance."""
    return Incident(
        title="Database Connection Failure",
        description="Connection pool exhausted with cascading retries",
        severity=IncidentSeverity.HIGH,
        business_impact=BusinessImpact(
            service_tier=ServiceTier.TIER_1,
            affected_users=5_000,
            revenue_impact_per_minute=750.0,
        ),
        metadata=IncidentMetadata(source_system="unit_test", tags={"env": "test"}),
    )


class TestAgents:
    """Validate core agent behaviours using lightweight stubs."""

    @pytest.mark.asyncio
    async def test_detection_agent_escalates_high_severity(self, sample_incident: Incident):
        agent = RobustDetectionAgent("detector_test")

        with patch.object(agent, "should_drop_alerts", AsyncMock(return_value=False)):
            recommendations = await agent.process_incident(sample_incident)

        assert recommendations, "Detection agent should emit at least one recommendation"
        assert recommendations[0].action_type == ActionType.ESCALATE_INCIDENT

    @pytest.mark.asyncio
    async def test_diagnosis_agent_generates_root_cause(self, sample_incident: Incident):
        agent = HardenedDiagnosisAgent("diagnosis_test")
        agent.rag_memory = SimpleNamespace(
            search_similar_incidents=AsyncMock(return_value=[]),
            store_incident_pattern=AsyncMock(return_value=None),
            get_knowledge_base_stats=AsyncMock(return_value={}),
        )

        recommendation = AgentRecommendation(
            agent_name=AgentType.DIAGNOSIS,
            incident_id=sample_incident.id,
            action_type=ActionType.ESCALATE_INCIDENT,
            action_id="diagnosis_database_error",
            confidence=0.92,
            risk_level=RiskLevel.MEDIUM,
            estimated_impact="Provides actionable diagnosis",
            reasoning="Correlated errors across database cluster",
            urgency=0.6,
        )

        with patch.object(
            agent,
            "trace_root_cause",
            AsyncMock(
                return_value={
                    "root_cause_hypothesis": {
                        "primary_cause": "database_error",
                        "confidence": 0.92,
                        "evidence": ["error spikes", "lock contention"],
                    }
                }
            ),
        ), patch.object(
            agent,
            "_generate_diagnosis_recommendations",
            AsyncMock(return_value=[recommendation]),
        ):
            recommendations = await agent.process_incident(sample_incident)

        assert recommendations and recommendations[0].action_type == ActionType.ESCALATE_INCIDENT


class TestConsensusEngine:
    """Ensure consensus engine honours confidence weighting."""

    @pytest.mark.asyncio
    async def test_consensus_prefers_high_confidence_action(self, sample_incident: Incident):
        engine = BasicWeightedConsensusEngine()

        restart = AgentRecommendation(
            agent_name=AgentType.DETECTION,
            incident_id=sample_incident.id,
            action_type=ActionType.RESTART_SERVICE,
            action_id="restart_primary_db",
            confidence=0.9,
            risk_level=RiskLevel.MEDIUM,
            estimated_impact="Short downtime for restart",
            reasoning="CPU saturation and hung connections detected",
            urgency=0.75,
        )

        scale = AgentRecommendation(
            agent_name=AgentType.PREDICTION,
            incident_id=sample_incident.id,
            action_type=ActionType.INCREASE_CAPACITY,
            action_id="scale_read_replicas",
            confidence=0.55,
            risk_level=RiskLevel.LOW,
            estimated_impact="Additional replicas mitigate risk",
            reasoning="Projected read load exceeds thresholds",
            urgency=0.4,
        )

        decision = await engine.reach_consensus(sample_incident, [restart, scale])

        assert decision.selected_action == "restart_primary_db"
        expected_confidence = restart.confidence * engine.agent_weights[AgentType.DETECTION.value]
        assert decision.final_confidence == pytest.approx(expected_confidence)


class TestCircuitBreakers:
    """Validate circuit breaker transitions and manager dashboard."""

    @pytest.mark.asyncio
    async def test_resilient_circuit_breaker_transitions(self):
        breaker = ResilientCircuitBreaker(
            name="service_test",
            failure_threshold=2,
            timeout_seconds=1,
            success_threshold=1,
        )

        assert breaker.state == CircuitBreakerState.CLOSED

        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.CLOSED

        breaker.record_failure()
        assert breaker.state == CircuitBreakerState.OPEN

        with pytest.raises(CircuitBreakerOpenError):
            await breaker.call(AsyncMock(return_value="ignored"))

        breaker._last_failure_time = datetime.utcnow() - timedelta(seconds=2)

        success_call = AsyncMock(return_value="success")
        result = await breaker.call(success_call)
        assert result == "success"
        assert breaker.state in {CircuitBreakerState.HALF_OPEN, CircuitBreakerState.CLOSED}

        # Second successful call should close the breaker
        breaker._last_failure_time = datetime.utcnow() - timedelta(seconds=2)
        result = await breaker.call(success_call)
        assert result == "success"
        assert breaker.state == CircuitBreakerState.CLOSED

    def test_circuit_breaker_manager_dashboard(self):
        manager = CircuitBreakerManagerImpl()
        datadog_cb = manager.get_circuit_breaker("datadog")

        for _ in range(3):
            datadog_cb.record_failure()

        dashboard = manager.get_health_dashboard()

        assert "datadog" in dashboard["services"]
        assert dashboard["services"]["datadog"]["status"] in {"degraded", "unhealthy"}


class TestRateLimiters:
    """Validate rate limiter behaviour without external calls."""

    @pytest.mark.asyncio
    async def test_bedrock_rate_limiter_grants_tokens(self):
        limiter = BedrockRateLimitManager()
        selected_model = await limiter.request_model_access(
            preferred_model="anthropic.claude-3-sonnet-20240229-v1:0",
            complexity_score=0.4,
        )

        assert selected_model in limiter.model_buckets
        status = limiter.get_status()
        assert status["queue_length"] >= 0

    @pytest.mark.asyncio
    async def test_external_rate_limiter_handles_queueing(self):
        limiter = ExternalServiceRateLimiter()

        service = "slack"
        # Drain tokens quickly to trigger queueing path
        bucket = limiter.service_buckets[service]
        bucket.tokens = 0

        with pytest.raises(RateLimitError):
            await limiter.request_service_access(service, priority=RequestPriority.MEDIUM)

        # High priority requests are queued and retried
        with patch.object(bucket, "consume", AsyncMock(side_effect=[False, True])):
            allowed = await limiter.request_service_access(service, priority=RequestPriority.CRITICAL)
            assert allowed is True

        status = limiter.get_service_status(service)
        assert status["service"] == service
        assert status["queue_length"] >= 0
