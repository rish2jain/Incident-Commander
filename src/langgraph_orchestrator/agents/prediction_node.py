"""Prediction node for LangGraph orchestration."""

from __future__ import annotations

from src.langgraph_orchestrator.state_schema import (
    AgentNodeExecutionResult,
    AgentNodeResultModel,
    IncidentStateModel,
    StateTimelineEvent,
)
from src.models.agent import AgentType
from src.services.agents import PredictionHeuristicAgent
from src.utils.logging import get_logger


class PredictionNode:
    """LangGraph node responsible for forecasting incident trajectory."""

    def __init__(self) -> None:
        self._logger = get_logger("langgraph.prediction")
        self._agent_factory = PredictionHeuristicAgent

    async def run(self, state: IncidentStateModel) -> AgentNodeExecutionResult:
        incident = state.incident
        agent = self._agent_factory()
        agent.set_context(state.context)

        recommendations = await agent.process_incident(incident)
        artifacts = agent.artifacts

        node_result = AgentNodeResultModel(
            agent=AgentType.PREDICTION.value,
            recommendations=recommendations,
            metrics=artifacts.metrics,
            metadata={"forecast_model": "business-impact-baseline"},
        )

        timeline_event = StateTimelineEvent(
            phase="prediction",
            agent=AgentType.PREDICTION.value,
            message=artifacts.timeline_message,
            metadata=artifacts.timeline_metadata,
        )

        return AgentNodeExecutionResult(
            output=node_result,
            timeline_event=timeline_event,
            context_delta=dict(artifacts.context_delta),
        )
