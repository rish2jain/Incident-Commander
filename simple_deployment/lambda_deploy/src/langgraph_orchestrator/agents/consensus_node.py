"""Consensus node for LangGraph orchestration."""

from __future__ import annotations

import asyncio
from statistics import mean
from typing import Iterable, List, Optional

from src.langgraph_orchestrator.state_schema import (
    AgentNodeExecutionResult,
    AgentNodeResultModel,
    IncidentStateModel,
    StateTimelineEvent,
)
from src.models.agent import AgentRecommendation, AgentType, ConsensusDecision
from src.services.byzantine_consensus import (
    ByzantineFaultTolerantConsensus,
    get_byzantine_consensus_engine,
)
from src.utils.logging import get_logger

# Configuration: PBFT proposal timeout in seconds (adjustable for network latency)
PBFT_PROPOSAL_TIMEOUT = 2.0


class ConsensusNode:
    """LangGraph node coordinating PBFT consensus across agent outputs."""

    def __init__(
        self,
        consensus_engine: Optional[ByzantineFaultTolerantConsensus] = None,
    ) -> None:
        self._logger = get_logger("langgraph.consensus")
        if consensus_engine is not None:
            self._consensus_engine = consensus_engine
        else:
            try:
                self._consensus_engine = get_byzantine_consensus_engine()
            except Exception as exc:  # noqa: BLE001 - dependency free fallback
                self._logger.warning(
                    "Unable to initialize PBFT consensus engine",
                    extra={"error": str(exc)},
                )
                self._consensus_engine = None

    async def run(self, state: IncidentStateModel) -> AgentNodeExecutionResult:
        incident = state.incident
        recommendations = self._collect_recommendations(state)

        if not recommendations:
            decision = ConsensusDecision(
                incident_id=incident.id,
                selected_action="noop",
                action_type="noop",
                final_confidence=0.0,
                consensus_method="empty",
                decision_rationale="No agent recommendations available",
            )
            node_result = AgentNodeResultModel(
                agent="consensus",
                recommendations=[],
                metrics={"participating_agents": []},
            )
            timeline_event = StateTimelineEvent(
                phase="consensus",
                agent="consensus",
                message="No recommendations to evaluate",
                metadata={"incident_id": incident.id},
            )
            return AgentNodeExecutionResult(
                output=node_result,
                timeline_event=timeline_event,
                context_delta={},
                state_overrides={"consensus": decision.model_dump(mode="python")},
            )

        primary = max(recommendations, key=lambda rec: rec.confidence)
        decision: Optional[ConsensusDecision] = None

        if self._consensus_engine is not None:
            try:
                decision = await asyncio.wait_for(
                    self._consensus_engine.propose_action(incident, primary),
                    timeout=PBFT_PROPOSAL_TIMEOUT,
                )
                for rec in recommendations:
                    decision.add_recommendation(rec)
                decision.consensus_method = "pbft"
            except (asyncio.TimeoutError, Exception) as exc:  # noqa: BLE001 - resiliency over strictness
                self._logger.warning(
                    "PBFT consensus unavailable, using weighted fallback",
                    extra={"incident_id": incident.id, "error": str(exc)},
                )
                decision = self._fallback_decision(incident_id=incident.id, recommendations=recommendations)
        else:
            decision = self._fallback_decision(incident_id=incident.id, recommendations=recommendations)

        participating_agents = [
            rec.agent_name if isinstance(rec.agent_name, str) else rec.agent_name.value
            for rec in recommendations
        ]
        participating_agents = list(dict.fromkeys(participating_agents))
        node_result = AgentNodeResultModel(
            agent="consensus",
            recommendations=[primary],
            metrics={
                "participating_agents": participating_agents,
                "final_confidence": round(decision.final_confidence, 3),
                "method": decision.consensus_method,
            },
            metadata={"total_recommendations": len(recommendations)},
        )

        timeline_event = StateTimelineEvent(
            phase="consensus",
            agent="consensus",
            message=(
                f"Consensus chose action {decision.selected_action} "
                f"({decision.action_type}) with confidence {decision.final_confidence:.2f}"
            ),
            metadata={
                "incident_id": incident.id,
                "method": decision.consensus_method,
                "participants": participating_agents,
            },
        )

        context_delta = {
            "consensus_action": decision.selected_action,
            "consensus_confidence": decision.final_confidence,
        }

        return AgentNodeExecutionResult(
            output=node_result,
            timeline_event=timeline_event,
            context_delta=context_delta,
            state_overrides={"consensus": decision.model_dump(mode="python")},
        )

    @staticmethod
    def _collect_recommendations(state: IncidentStateModel) -> List[AgentRecommendation]:
        # Only collect recommendations from pre-consensus phases
        sections = [state.detection, state.diagnosis, state.prediction]
        recommendations: List[AgentRecommendation] = []
        for section in sections:
            if section:
                recommendations.extend(section.recommendations)
        return recommendations

    @staticmethod
    def _fallback_decision(
        *, incident_id: str, recommendations: Iterable[AgentRecommendation]
    ) -> ConsensusDecision:
        recommendations_list = list(recommendations)
        primary = max(recommendations_list, key=lambda rec: rec.confidence)
        action_type_value = ConsensusNode._to_action_type_value(primary.action_type)
        decision = ConsensusDecision(
            incident_id=incident_id,
            selected_action=primary.action_id,
            action_type=action_type_value,
            final_confidence=min(1.0, mean(rec.confidence for rec in recommendations_list)),
            consensus_method="weighted_fallback",
            decision_rationale="Weighted mean of agent confidences",
        )
        for rec in recommendations_list:
            decision.add_recommendation(rec)
        return decision

    @staticmethod
    def _to_action_type_value(action_type: object) -> str:
        return action_type.value if hasattr(action_type, "value") else str(action_type)
