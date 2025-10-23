"""Resolution node implementing action planning in LangGraph."""

from __future__ import annotations

from src.langgraph_orchestrator.state_schema import (
    AgentNodeExecutionResult,
    AgentNodeResultModel,
    IncidentStateModel,
    StateTimelineEvent,
)
from src.models.agent import AgentType
from src.services.agents import ResolutionHeuristicAgent
from src.utils.logging import get_logger


class ResolutionNode:
    """LangGraph node that translates consensus into executable actions."""

    def __init__(self) -> None:
        self._logger = get_logger("langgraph.resolution")
        self._agent_factory = ResolutionHeuristicAgent

    async def run(self, state: IncidentStateModel) -> AgentNodeExecutionResult:
        incident = state.incident
        agent = self._agent_factory()
        agent.set_context(state.context)
        agent.set_consensus(state.consensus)

        recommendations = await agent.process_incident(incident)
        artifacts = agent.artifacts

        node_result = AgentNodeResultModel(
            agent=AgentType.RESOLUTION.value,
            recommendations=recommendations,
            metrics=artifacts.metrics,
            metadata={"runbook_version": "v1-alpha"},
        )

        timeline_event = StateTimelineEvent(
            phase="resolution",
            agent=AgentType.RESOLUTION.value,
            message=artifacts.timeline_message,
            metadata=artifacts.timeline_metadata,
        )

        return AgentNodeExecutionResult(
            output=node_result,
            timeline_event=timeline_event,
            context_delta=dict(artifacts.context_delta),
        )
