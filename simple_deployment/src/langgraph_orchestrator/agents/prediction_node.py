"""Prediction node implementation for LangGraph orchestration."""

from __future__ import annotations

from src.langgraph_orchestrator.state_schema import (
    AgentNodeExecutionResult,
    AgentNodeResultModel,
    IncidentStateModel,
    StateTimelineEvent,
)
from src.models.agent import AgentType
from src.services.agents.heuristic_agents import PredictionHeuristicAgent
from src.utils.logging import get_logger


class PredictionNode:
    """LangGraph node responsible for incident prediction and forecasting."""

    def __init__(self) -> None:
        self._logger = get_logger("langgraph.prediction")
        self._agent_factory = lambda: PredictionHeuristicAgent()

    async def run(self, state: IncidentStateModel) -> AgentNodeExecutionResult:
        """Execute prediction logic and return normalized output."""
        incident = state.incident
        agent = self._agent_factory()
        agent.set_context(state.context)

        recommendations = await agent.process_incident(incident)
        artifacts = agent.artifacts

        node_result = AgentNodeResultModel(
            agent=AgentType.PREDICTION.value,
            recommendations=recommendations,
            metrics=artifacts.metrics,
            metadata={
                "prediction_model": "langgraph-heuristic-v1",
                "business_impact_enabled": incident.business_impact is not None,
            },
        )

        timeline_event = StateTimelineEvent(
            phase="prediction",
            agent=AgentType.PREDICTION.value,
            message=artifacts.timeline_message,
            metadata=artifacts.timeline_metadata,
        )

        # Defend against None or non-dict context_delta
        from collections.abc import Mapping

        if artifacts.context_delta is None:
            context_delta = {}
        elif isinstance(artifacts.context_delta, Mapping):
            context_delta = dict(artifacts.context_delta)
        else:
            context_delta = {"context_delta": artifacts.context_delta}

        context_delta.setdefault("prediction_completed_at", timeline_event.timestamp.isoformat())

        return AgentNodeExecutionResult(
            output=node_result,
            timeline_event=timeline_event,
            context_delta=context_delta,
        )
