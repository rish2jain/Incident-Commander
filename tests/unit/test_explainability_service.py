"""Unit tests for explainability services and timeline ledger."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from src.models.agent import AgentRecommendation, AgentType, ActionType, RiskLevel, ConsensusDecision
from src.models.incident import (
    Incident,
    IncidentSeverity,
    BusinessImpact,
    IncidentMetadata,
    ServiceTier,
)
from src.orchestrator.swarm_coordinator import (
    AgentExecution,
    IncidentProcessingState,
    ProcessingPhase,
    AgentSwarmCoordinator,
)
from src.services.explainability import ExplainabilityService


def _make_incident() -> Incident:
    return Incident(
        id="inc-123",
        title="Database latency spike",
        description="Customer transactions backing up",
        severity=IncidentSeverity.CRITICAL,
        business_impact=BusinessImpact(
            service_tier=ServiceTier.TIER_1,
            affected_users=1200,
            revenue_impact_per_minute=480.0,
            sla_breach_risk=0.7,
            reputation_impact=0.6,
        ),
        metadata=IncidentMetadata(
            source_system="unit-test",
            tags={"service": "payments", "environment": "prod"},
            alert_ids=["alert-1"],
            correlation_id="corr-1",
        ),
    )


def _recommendations(incident_id: str):
    primary = AgentRecommendation(
        agent_name=AgentType.DIAGNOSIS,
        incident_id=incident_id,
        action_type=ActionType.RESTART_SERVICE,
        action_id="restart_db",
        confidence=0.87,
        risk_level=RiskLevel.MEDIUM,
        estimated_impact="Restores connectivity",
        reasoning="Detected connection pool exhaustion",
        urgency=0.9,
    )
    supporting = AgentRecommendation(
        agent_name=AgentType.RESOLUTION,
        incident_id=incident_id,
        action_type=ActionType.RESTART_SERVICE,
        action_id="restart_db",
        confidence=0.82,
        risk_level=RiskLevel.LOW,
        estimated_impact="Automated restart with rollback",
        reasoning="Previous incidents resolved via restart",
        urgency=0.7,
    )
    alternative = AgentRecommendation(
        agent_name=AgentType.PREDICTION,
        incident_id=incident_id,
        action_type=ActionType.SCALE_UP,
        action_id="scale_out_read_replicas",
        confidence=0.71,
        risk_level=RiskLevel.LOW,
        estimated_impact="Adds read replicas to absorb load",
        reasoning="Forecast shows demand spike persists",
        urgency=0.6,
    )
    return primary, supporting, alternative


def test_explainability_service_generates_rationale_and_counterfactuals():
    incident = _make_incident()
    state = IncidentProcessingState(
        incident_id=incident.id,
        incident=incident,
        phase=ProcessingPhase.DETECTION,
        agent_executions={},
    )

    state.record_event("incident_started", "Incident detected", phase="detection")

    execution = AgentExecution(
        agent_name="diag_agent",
        agent_type=AgentType.DIAGNOSIS,
        status="completed",
        start_time=datetime.utcnow() - timedelta(seconds=30),
        end_time=datetime.utcnow(),
    )

    primary, supporting, alternative = _recommendations(incident.id)
    execution.recommendations = [primary, supporting]
    state.agent_executions[execution.agent_name] = execution

    decision = ConsensusDecision(
        incident_id=incident.id,
        selected_action="restart_db",
        action_type=ActionType.RESTART_SERVICE.value,
        final_confidence=0.91,
        participating_agents=["diag_agent", "resolution_agent", "prediction_agent"],
        agent_recommendations=[primary, supporting, alternative],
        consensus_method="weighted_voting",
        decision_rationale="Primary root cause traced to connection pool exhaustion",
        fallback_actions=["Throttle traffic if restart fails"],
    )
    state.consensus_decision = decision

    service = ExplainabilityService()
    package = service.build_explainability_package(state)

    assert package["incident_id"] == incident.id
    assert package["rationale_summary"]["headline"].startswith("Selected action restart_db")
    assert pytest.approx(package["confidence_profile"]["final_confidence"], 0.01) == 0.91

    counterfactuals = package["counterfactuals"]
    assert len(counterfactuals) == 1
    assert counterfactuals[0]["alternative_action"] == "scale_out_read_replicas"
    assert counterfactuals[0]["average_confidence"] > 0.7
    assert package["ledger_summary"]["total_events"] == 1


def test_incident_timeline_filters_by_agent(monkeypatch):
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

    coordinator = AgentSwarmCoordinator(service_factory=MagicMock())

    incident = _make_incident()
    state = IncidentProcessingState(
        incident_id=incident.id,
        incident=incident,
        phase=ProcessingPhase.DETECTION,
        agent_executions={},
    )

    state.record_event("incident_started", "Incident detected", phase="detection")
    state.record_event("agent_started", "Detector engaged", phase="detection", agent="detector")
    state.record_event("agent_completed", "Diagnosis finished", phase="diagnosis", agent="diagnoser")

    coordinator.processing_states[incident.id] = state

    filtered = coordinator.get_incident_timeline(incident.id, agent="diagnoser")
    assert filtered is not None
    assert len(filtered["timeline"]) == 1
    assert filtered["summary"]["total_events"] == 3
