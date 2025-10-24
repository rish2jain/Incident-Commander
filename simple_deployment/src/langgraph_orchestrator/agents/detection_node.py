"""Detection node implementation for LangGraph orchestration."""

from __future__ import annotations

from typing import Optional

from src.langgraph_orchestrator.state_schema import (
    AgentNodeExecutionResult,
    AgentNodeResultModel,
    IncidentStateModel,
    StateTimelineEvent,
)
from src.models.agent import AgentType
from src.services.agents import DetectionHeuristicAgent
from src.services.message_bus import ResilientMessageBus
from src.utils.logging import get_logger


class DetectionNode:
    """LangGraph node responsible for incident detection insights."""

    def __init__(self, message_bus: Optional[ResilientMessageBus] = None) -> None:
        self._message_bus = message_bus
        self._logger = get_logger("langgraph.detection")
        self._agent_factory = lambda: DetectionHeuristicAgent(message_bus=self._message_bus)

    async def run(self, state: IncidentStateModel) -> AgentNodeExecutionResult:
        """Execute detection logic and return normalized output."""
        incident = state.incident
        agent = self._agent_factory()
        agent.set_context(state.context)

        recommendations = await agent.process_incident(incident)
        artifacts = agent.artifacts

        node_result = AgentNodeResultModel(
            agent=AgentType.DETECTION.value,
            recommendations=recommendations,
            metrics=artifacts.metrics,
            metadata={
                "detection_model": "langgraph-heuristic-v1",
                "telemetry_sources": state.context.get("telemetry_sources", []),
            },
        )

        timeline_event = StateTimelineEvent(
            phase="detection",
            agent=AgentType.DETECTION.value,
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

        context_delta.setdefault("detection_completed_at", timeline_event.timestamp.isoformat())

        return AgentNodeExecutionResult(
            output=node_result,
            timeline_event=timeline_event,
            context_delta=context_delta,
        )
