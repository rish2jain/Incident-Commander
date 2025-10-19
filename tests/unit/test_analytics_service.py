"""Tests for analytics insights service."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

from src.models.agent import ConsensusDecision
from src.models.incident import (
    Incident,
    IncidentSeverity,
    BusinessImpact,
    IncidentMetadata,
    ServiceTier,
)
from src.orchestrator.swarm_coordinator import (
    AgentSwarmCoordinator,
    IncidentProcessingState,
    ProcessingPhase,
)
from src.services.analytics import AnalyticsService


def _make_incident(identifier: str, team: str) -> Incident:
    return Incident(
        id=identifier,
        title="Test Incident",
        description="Test description",
        severity=IncidentSeverity.HIGH,
        business_impact=BusinessImpact(
            service_tier=ServiceTier.TIER_2,
            affected_users=450,
            revenue_impact_per_minute=120.0,
            sla_breach_risk=0.4,
            reputation_impact=0.3,
        ),
        metadata=IncidentMetadata(
            source_system="unit-test",
            tags={"team": team},
            alert_ids=[f"alert-{identifier}"],
        ),
    )


def _stub_coordinator(monkeypatch):
    class DummyBus:
        async def subscribe(self, *_, **__):
            return None

        async def unsubscribe(self, *_, **__):
            return None

        async def shutdown(self):
            return None

        def update_service_factory(self, *_):
            return None

    monkeypatch.setattr(
        "src.orchestrator.swarm_coordinator.get_message_bus",
        lambda service_factory: DummyBus(),
    )
    return AgentSwarmCoordinator(service_factory=MagicMock())


def test_analytics_service_builds_scorecard(monkeypatch):
    coordinator = _stub_coordinator(monkeypatch)
    service = AnalyticsService()

    for idx, team in enumerate(["payments", "platform"], start=1):
        incident = _make_incident(f"inc-{idx}", team)
        state = IncidentProcessingState(
            incident_id=incident.id,
            incident=incident,
            phase=ProcessingPhase.COMPLETED,
            agent_executions={},
            start_time=datetime.utcnow() - timedelta(minutes=5 * idx),
            end_time=datetime.utcnow(),
        )
        decision = ConsensusDecision(
            incident_id=incident.id,
            selected_action="scale_out" if idx == 1 else "restart_service",
            action_type="scale",
            final_confidence=0.82 + (idx * 0.05),
            requires_human_approval=(idx == 2),
            conflicts_detected=False,
        )
        state.consensus_decision = decision
        coordinator.processing_states[incident.id] = state

    insights = service.build_insights(coordinator)

    assert insights["resilience_scorecard"]["incident_count"] == 2
    assert insights["slo_impact"]["slo_met"] >= 0
    assert insights["benchmarks"]["total_teams_tracked"] == 2
