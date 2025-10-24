"""Resolution node implementation for LangGraph orchestration."""

from __future__ import annotations

from src.langgraph_orchestrator.state_schema import (
    AgentNodeExecutionResult,
    AgentNodeResultModel,
    IncidentStateModel,
    StateTimelineEvent,
)
from src.models.agent import AgentType
from src.services.agents.heuristic_agents import ResolutionHeuristicAgent
from src.utils.logging import get_logger


class ResolutionNode:
    """LangGraph node responsible for incident resolution."""

    def __init__(self) -> None:
        self._logger = get_logger("langgraph.resolution")
        self._agent_factory = lambda: ResolutionHeuristicAgent()

    async def run(self, state: IncidentStateModel) -> AgentNodeExecutionResult:
        """Execute resolution logic and return normalized output."""
        incident = state.incident
        agent = self._agent_factory()
        agent.set_context(state.context)

        # Pass consensus decision to resolution agent if available
        if state.consensus:
            agent.set_consensus(state.consensus)

        recommendations = await agent.process_incident(incident)
        artifacts = agent.artifacts

        node_result = AgentNodeResultModel(
            agent=AgentType.RESOLUTION.value,
            recommendations=recommendations,
            metrics=artifacts.metrics,
            metadata={
                "resolution_model": "langgraph-heuristic-v1",
                "consensus_available": state.consensus is not None,
            },
        )

        timeline_event = StateTimelineEvent(
            phase="resolution",
            agent=AgentType.RESOLUTION.value,
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

        context_delta.setdefault("resolution_completed_at", timeline_event.timestamp.isoformat())

        return AgentNodeExecutionResult(
            output=node_result,
            timeline_event=timeline_event,
            context_delta=context_delta,
        )
