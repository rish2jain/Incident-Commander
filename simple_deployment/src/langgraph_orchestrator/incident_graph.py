"""LangGraph-based orchestration for Incident Commander."""

from __future__ import annotations

import asyncio
from typing import Dict, Optional

try:  # pragma: no cover - exercised in integration tests
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover - fallback when langgraph is absent
    from src.langgraph_orchestrator.utils.local_state_graph import END, START, StateGraph

from src.langgraph_orchestrator.agents import (
    CommunicationNode,
    ConsensusNode,
    DetectionNode,
    DiagnosisNode,
    PredictionNode,
    ResolutionNode,
)
from src.langgraph_orchestrator.state_schema import IncidentGraphState, IncidentStateModel
from src.langgraph_orchestrator.utils.routing import merge_state_updates
from src.models.incident import Incident
from src.services.byzantine_consensus import ByzantineFaultTolerantConsensus
from src.services.message_bus import ResilientMessageBus
from src.utils.logging import get_logger


class IncidentResponseGraph:
    """Primary entry point for LangGraph-based incident orchestration."""

    def __init__(
        self,
        *,
        message_bus: Optional[ResilientMessageBus] = None,
        consensus_engine: Optional[ByzantineFaultTolerantConsensus] = None,
    ) -> None:
        self._logger = get_logger("langgraph.incident_graph")
        self._message_bus = message_bus
        self._consensus_engine = consensus_engine

        self._detection_node = DetectionNode(self._message_bus)
        self._diagnosis_node = DiagnosisNode()
        self._prediction_node = PredictionNode()
        self._consensus_node = ConsensusNode(self._consensus_engine)
        self._resolution_node = ResolutionNode()
        self._communication_node = CommunicationNode(self._message_bus)

        self._graph = StateGraph(IncidentGraphState)
        self._build_graph()
        self._app = self._graph.compile()

    async def run(self, incident: Incident, *, context: Optional[Dict[str, object]] = None) -> IncidentStateModel:
        """Execute the LangGraph workflow for the provided incident."""
        context = context or {}
        initial_state: IncidentGraphState = {
            "incident": incident,
            "context": context,
            "timeline": [],
        }

        self._logger.info(
            "Running LangGraph orchestration",
            extra={"incident_id": incident.id, "context_keys": list(context.keys())},
        )

        final_state = await self._app.ainvoke(initial_state)
        return IncidentStateModel.from_graph_state(final_state)

    def _build_graph(self) -> None:
        self._graph.add_node("detection", self._run_detection)
        self._graph.add_node("analysis", self._run_analysis)
        self._graph.add_node("consensus", self._run_consensus)
        self._graph.add_node("resolution", self._run_resolution)
        self._graph.add_node("communication", self._run_communication)

        self._graph.add_edge(START, "detection")
        self._graph.add_edge("detection", "analysis")
        self._graph.add_edge("analysis", "consensus")
        self._graph.add_edge("consensus", "resolution")
        self._graph.add_edge("resolution", "communication")
        self._graph.add_edge("communication", END)

    async def _run_detection(self, state: IncidentGraphState) -> IncidentGraphState:
        incident_state = IncidentStateModel.from_graph_state(state)
        result = await self._detection_node.run(incident_state)
        return result.to_state_update("detection", state)

    async def _run_analysis(self, state: IncidentGraphState) -> IncidentGraphState:
        incident_state = IncidentStateModel.from_graph_state(state)
        diagnosis_task = asyncio.create_task(self._diagnosis_node.run(incident_state))
        prediction_task = asyncio.create_task(self._prediction_node.run(incident_state))
        diagnosis_result, prediction_result = await asyncio.gather(diagnosis_task, prediction_task)

        diagnosis_update = diagnosis_result.to_state_update("diagnosis", state)
        intermediate_state = merge_state_updates(state, diagnosis_update)
        prediction_update = prediction_result.to_state_update("prediction", intermediate_state)

        merged_update: IncidentGraphState = dict(diagnosis_update)
        for key, value in prediction_update.items():
            if key == "context" and "context" in merged_update:
                context = dict(merged_update["context"])
                context.update(value)
                merged_update["context"] = context
            else:
                merged_update[key] = value
        return merged_update

    async def _run_consensus(self, state: IncidentGraphState) -> IncidentGraphState:
        incident_state = IncidentStateModel.from_graph_state(state)
        result = await self._consensus_node.run(incident_state)
        return result.to_state_update("consensus", state)

    async def _run_resolution(self, state: IncidentGraphState) -> IncidentGraphState:
        incident_state = IncidentStateModel.from_graph_state(state)
        result = await self._resolution_node.run(incident_state)
        return result.to_state_update("resolution", state)

    async def _run_communication(self, state: IncidentGraphState) -> IncidentGraphState:
        incident_state = IncidentStateModel.from_graph_state(state)
        result = await self._communication_node.run(incident_state)
        return result.to_state_update("communication", state)
