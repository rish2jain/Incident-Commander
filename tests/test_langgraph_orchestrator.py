"""Tests covering the LangGraph orchestration scaffold (Phase 1 deliverables)."""

import pytest

from src.langgraph_orchestrator import IncidentResponseGraph
from src.models.agent import AgentType
from src.models.incident import (
    BusinessImpact,
    Incident,
    IncidentMetadata,
    IncidentSeverity,
    IncidentStatus,
    ServiceTier,
)
from src.services.agents import (
    CommunicationHeuristicAgent,
    DetectionHeuristicAgent,
    DiagnosisHeuristicAgent,
    PredictionHeuristicAgent,
    ResolutionHeuristicAgent,
)


def _sample_incident() -> Incident:
    return Incident(
        title="Synthetic latency spike",
        description="Checkout latency exceeds SLO with timeout errors",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.DETECTED,
        business_impact=BusinessImpact(service_tier=ServiceTier.TIER_1, affected_users=5000),
        metadata=IncidentMetadata(source_system="synthetic-monitoring"),
    )


@pytest.mark.asyncio
async def test_incident_response_graph_executes_end_to_end():
    graph = IncidentResponseGraph()
    state = await graph.run(
        _sample_incident(),
        context={"telemetry_sources": ["cloudwatch", "app_traces"], "log_sources": ["app"], "alert_count": 4},
    )

    assert state.detection is not None
    assert state.diagnosis is not None
    assert state.prediction is not None
    assert state.consensus is not None
    assert state.resolution is not None
    assert state.communication is not None

    assert state.timeline, "timeline captures node outputs"
    phases = [event.phase for event in state.timeline]
    for expected in ["detection", "diagnosis", "prediction", "consensus", "resolution", "communication"]:
        assert expected in phases

    assert state.consensus.selected_action
    assert state.consensus.final_confidence > 0
    assert state.communication.recommendations, "communication should have recommendations"
    assert len(state.communication.recommendations) > 0, "communication recommendations list should not be empty"
    assert state.communication.recommendations[0].agent_name == AgentType.COMMUNICATION


@pytest.mark.asyncio
async def test_consensus_fallback_handles_missing_recommendations():
    graph = IncidentResponseGraph()
    incident = _sample_incident()

    state = await graph.run(incident, context={})

    assert state.consensus is not None
    assert state.consensus.final_confidence >= 0
    assert state.consensus.consensus_method in {"pbft", "weighted_fallback"}


@pytest.mark.asyncio
async def test_detection_node_matches_detection_agent():
    context = {"telemetry_sources": ["datadog", "synthetic"], "alert_count": 6}
    agent = DetectionHeuristicAgent()
    agent.set_context(context)
    incident_agent = _sample_incident()
    recommendations_agent = await agent.process_incident(incident_agent)

    graph = IncidentResponseGraph()
    state = await graph.run(_sample_incident(), context=context)
    node_rec = state.detection.primary_recommendation

    assert node_rec.action_type == recommendations_agent[0].action_type
    assert node_rec.confidence == pytest.approx(recommendations_agent[0].confidence, rel=1e-6)
    assert node_rec.parameters == recommendations_agent[0].parameters


@pytest.mark.asyncio
async def test_diagnosis_node_matches_diagnosis_agent():
    context = {"log_sources": ["app", "infra"]}
    agent = DiagnosisHeuristicAgent()
    agent.set_context(context)
    incident_agent = _sample_incident()
    recommendations_agent = await agent.process_incident(incident_agent)

    graph = IncidentResponseGraph()
    state = await graph.run(_sample_incident(), context=context)
    node_rec = state.diagnosis.primary_recommendation

    assert node_rec.action_type == recommendations_agent[0].action_type
    assert node_rec.parameters["keywords_triggered"] == recommendations_agent[0].parameters["keywords_triggered"]


@pytest.mark.asyncio
async def test_prediction_node_matches_prediction_agent():
    agent = PredictionHeuristicAgent()
    agent.set_context({})
    incident_agent = _sample_incident()
    recommendations_agent = await agent.process_incident(incident_agent)

    graph = IncidentResponseGraph()
    state = await graph.run(_sample_incident(), context={})
    node_rec = state.prediction.primary_recommendation

    assert node_rec.action_type == recommendations_agent[0].action_type
    assert node_rec.parameters["expected_minutes"] == pytest.approx(
        recommendations_agent[0].parameters["expected_minutes"], rel=1e-6
    )


@pytest.mark.asyncio
async def test_resolution_node_matches_resolution_agent():
    graph = IncidentResponseGraph()
    state = await graph.run(_sample_incident(), context={})

    agent = ResolutionHeuristicAgent()
    agent.set_context(state.context)
    agent.set_consensus(state.consensus)
    recommendations_agent = await agent.process_incident(_sample_incident())

    node_rec = state.resolution.primary_recommendation
    assert node_rec.action_type == recommendations_agent[0].action_type
    assert node_rec.confidence == pytest.approx(recommendations_agent[0].confidence, rel=1e-6)


@pytest.mark.asyncio
async def test_communication_node_matches_communication_agent():
    graph = IncidentResponseGraph()
    state = await graph.run(_sample_incident(), context={})

    resolution_rec = state.resolution.primary_recommendation
    agent = CommunicationHeuristicAgent()
    agent.set_context(state.context)
    agent.set_consensus(state.consensus)
    agent.set_resolution(resolution_rec)
    recommendations_agent = await agent.process_incident(_sample_incident())

    node_rec = state.communication.primary_recommendation
    assert node_rec.action_type == recommendations_agent[0].action_type
    assert node_rec.parameters["audiences"] == recommendations_agent[0].parameters["audiences"]
