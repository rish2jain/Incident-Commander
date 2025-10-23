"""Diagnosis node implementation for LangGraph orchestration."""

from __future__ import annotations

import asyncio

from src.langgraph_orchestrator.state_schema import (
    AgentNodeExecutionResult,
    AgentNodeResultModel,
    IncidentStateModel,
    StateTimelineEvent,
)
from src.models.agent import AgentType
from src.services.agents import DiagnosisHeuristicAgent
from src.utils.logging import get_logger


class DiagnosisNode:
    """LangGraph node responsible for root-cause diagnostics."""

    def __init__(self) -> None:
        self._logger = get_logger("langgraph.diagnosis")
        self._agent_factory = DiagnosisHeuristicAgent

    async def run(self, state: IncidentStateModel) -> AgentNodeExecutionResult:
        """Analyze incident context and return diagnosis recommendation."""
        incident = state.incident
        await asyncio.sleep(0)  # Yield control to highlight async compatibility

        agent = self._agent_factory()
        agent.set_context(state.context)
        recommendations = await agent.process_incident(incident)
        artifacts = agent.artifacts

        node_result = AgentNodeResultModel(
            agent=AgentType.DIAGNOSIS.value,
            recommendations=recommendations,
            metrics=artifacts.metrics,
            metadata={"analysis_engine": "rule-based-lite"},
        )

        timeline_event = StateTimelineEvent(
            phase="diagnosis",
            agent=AgentType.DIAGNOSIS.value,
            message=artifacts.timeline_message,
            metadata=artifacts.timeline_metadata,
        )

        return AgentNodeExecutionResult(
            output=node_result,
            timeline_event=timeline_event,
            context_delta=dict(artifacts.context_delta),
        )
