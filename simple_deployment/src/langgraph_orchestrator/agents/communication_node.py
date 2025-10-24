"""Communication node for LangGraph orchestration."""

from __future__ import annotations

from typing import Optional

from src.langgraph_orchestrator.state_schema import (
    AgentNodeExecutionResult,
    AgentNodeResultModel,
    IncidentStateModel,
    StateTimelineEvent,
)
from src.models.agent import AgentMessage, AgentType
from src.services.agents import CommunicationHeuristicAgent
from src.services.message_bus import MessagePriority, ResilientMessageBus
from src.utils.logging import get_logger


class CommunicationNode:
    """LangGraph node that crafts stakeholder communications."""

    def __init__(self, message_bus: Optional[ResilientMessageBus] = None) -> None:
        self._message_bus = message_bus
        self._logger = get_logger("langgraph.communication")
        self._agent_factory = CommunicationHeuristicAgent

    async def run(self, state: IncidentStateModel) -> AgentNodeExecutionResult:
        incident = state.incident
        consensus = state.consensus
        resolution = state.resolution.primary_recommendation if state.resolution else None

        agent = self._agent_factory()
        agent.set_context(state.context)
        agent.set_consensus(consensus)
        agent.set_resolution(resolution)

        recommendations = await agent.process_incident(incident)
        artifacts = agent.artifacts

        # Guard against empty recommendations list
        if not recommendations:
            node_result = AgentNodeResultModel(
                agent=AgentType.COMMUNICATION.value,
                recommendations=[],
                metrics=artifacts.metrics,
                metadata={"audiences": []},
            )
        else:
            node_result = AgentNodeResultModel(
                agent=AgentType.COMMUNICATION.value,
                recommendations=recommendations,
                metrics=artifacts.metrics,
                metadata={"audiences": recommendations[0].parameters["audiences"]},
            )

        timeline_event = StateTimelineEvent(
            phase="communication",
            agent=AgentType.COMMUNICATION.value,
            message=artifacts.timeline_message,
            metadata=artifacts.timeline_metadata,
        )

        context_delta = dict(artifacts.context_delta)

        summary = context_delta.get("communication_summary")
        if summary:
            await self._emit_bus_signal(incident_id=incident.id, summary=summary)

        return AgentNodeExecutionResult(
            output=node_result,
            timeline_event=timeline_event,
            context_delta=context_delta,
        )

    async def _emit_bus_signal(self, *, incident_id: str, summary: str) -> None:
        if not self._message_bus:
            return

        message = AgentMessage(
            sender_agent=AgentType.COMMUNICATION,
            recipient_agent=None,
            message_type="incident.communication",
            payload={"incident_id": incident_id, "summary": summary},
            correlation_id=incident_id,
        )

        try:
            await self._message_bus.send_message(
                message,
                priority=MessagePriority.MEDIUM,
                ttl_seconds=900,
            )
        except Exception as exc:  # noqa: BLE001
            self._logger.warning(
                "Failed to publish communication message",
                extra={"incident_id": incident_id, "error": str(exc)},
            )
