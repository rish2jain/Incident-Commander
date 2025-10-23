"""Diagnosis node implementation for LangGraph orchestration."""

from __future__ import annotations

from src.langgraph_orchestrator.state_schema import (
    AgentNodeExecutionResult,
    AgentNodeResultModel,
    IncidentStateModel,
    StateTimelineEvent,
)
from src.models.agent import AgentType
from src.services.agents.heuristic_agents import DiagnosisHeuristicAgent
from src.utils.logging import get_logger


class DiagnosisNode:
    """LangGraph node responsible for incident diagnosis."""

    def __init__(self) -> None:
        self._logger = get_logger("langgraph.diagnosis")
        self._agent_factory = lambda: DiagnosisHeuristicAgent()

    async def run(self, state: IncidentStateModel) -> AgentNodeExecutionResult:
        """Execute diagnosis logic and return normalized output."""
        incident = state.incident
        agent = self._agent_factory()
        agent.set_context(state.context)

        recommendations = await agent.process_incident(incident)
        artifacts = agent.artifacts

        node_result = AgentNodeResultModel(
            agent=AgentType.DIAGNOSIS.value,
            recommendations=recommendations,
            metrics=artifacts.metrics,
            metadata={
                "diagnosis_model": "langgraph-heuristic-v1",
                "log_sources": state.context.get("log_sources", []),
            },
        )

        timeline_event = StateTimelineEvent(
            phase="diagnosis",
            agent=AgentType.DIAGNOSIS.value,
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

        context_delta.setdefault("diagnosis_completed_at", timeline_event.timestamp.isoformat())

        return AgentNodeExecutionResult(
            output=node_result,
            timeline_event=timeline_event,
            context_delta=context_delta,
        )
