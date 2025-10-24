"""Explainability and trust services for incident processing."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from statistics import mean
from typing import Dict, Any, List, Optional

from src.models.agent import AgentRecommendation, RiskLevel
from src.orchestrator.swarm_coordinator import IncidentProcessingState
from src.schemas.incident import (
    ExplainabilityPackageSchema,
    RationaleSummary,
    ConfidenceProfile,
    CounterfactualOption,
    TimelineEventSchema,
    TimelineSummarySchema,
)


class ExplainabilityService:
    """Generates explainability artifacts for incidents."""

    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}

    def build_explainability_package(self, state: IncidentProcessingState) -> Dict[str, Any]:
        """Assemble full explainability payload for an incident."""
        timeline = [TimelineEventSchema(**event) for event in state.get_timeline()]
        summary = state.summarize_timeline()
        package = ExplainabilityPackageSchema(
            incident_id=state.incident_id,
            rationale_summary=self._generate_rationale_summary(state),
            confidence_profile=self._build_confidence_profile(state),
            counterfactuals=self._build_counterfactuals(state),
            timeline=timeline,
            ledger_summary=TimelineSummarySchema(**summary),
            last_updated=datetime.utcnow(),
            consensus_ready=state.consensus_decision is not None,
        )
        payload = package.model_dump()
        self._cache[state.incident_id] = payload
        return payload

    def get_cached_package(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Return cached package if previously generated."""
        return self._cache.get(incident_id)

    def _generate_rationale_summary(self, state: IncidentProcessingState) -> RationaleSummary:
        decision = state.consensus_decision
        if not decision:
            return RationaleSummary(
                headline="Consensus decision pending",
                confidence=0.0,
                requires_human_approval=True,
                rationale_points=["Consensus engine has not finalized a decision yet."],
                risk_assessment="Awaiting recommendations",
                fallback_plan=["Escalate to human operator"],
            )

        supporting_recs = self._filter_recommendations(
            decision.agent_recommendations,
            decision.selected_action
        )

        rationale_points = [decision.decision_rationale] if decision.decision_rationale else []
        rationale_points.extend([
            f"{rec.agent_name} highlighted {rec.reasoning} (confidence {rec.confidence:.2f})"
            for rec in supporting_recs[:3]
        ])

        fallback = decision.fallback_actions or ["Escalate to human operator if conditions change"]

        return RationaleSummary(
            headline=f"Selected action {decision.selected_action} with {decision.final_confidence:.2f} confidence",
            confidence=decision.final_confidence,
            requires_human_approval=decision.requires_human_approval,
            rationale_points=rationale_points,
            risk_assessment=decision.risk_assessment or "Risk evaluation captured in consensus process",
            fallback_plan=fallback,
        )

    def _build_confidence_profile(self, state: IncidentProcessingState) -> ConfidenceProfile:
        decision = state.consensus_decision
        if not decision:
            return ConfidenceProfile(status="pending")

        confidences = [rec.confidence for rec in decision.agent_recommendations]
        max_conf = max(confidences) if confidences else decision.final_confidence
        min_conf = min(confidences) if confidences else decision.final_confidence
        avg_conf = mean(confidences) if confidences else decision.final_confidence

        return ConfidenceProfile(
            status="evaluated",
            selected_action=decision.selected_action,
            final_confidence=decision.final_confidence,
            confidence_range={
                "min": round(min_conf, 3),
                "max": round(max_conf, 3),
                "avg": round(avg_conf, 3),
            },
            participating_agents=decision.participating_agents,
            requires_escalation=decision.requires_escalation(),
        )

    def _build_counterfactuals(self, state: IncidentProcessingState) -> List[CounterfactualOption]:
        decision = state.consensus_decision
        if not decision:
            return []

        grouped: Dict[str, List[AgentRecommendation]] = defaultdict(list)
        for recommendation in decision.agent_recommendations:
            grouped[recommendation.action_id].append(recommendation)

        selected_action = decision.selected_action
        counterfactuals: List[CounterfactualOption] = []
        ordering = {
            RiskLevel.LOW: 0,
            RiskLevel.MEDIUM: 1,
            RiskLevel.HIGH: 2,
            RiskLevel.CRITICAL: 3
        }

        for action_id, recs in grouped.items():
            if action_id == selected_action:
                continue

            avg_conf = mean([rec.confidence for rec in recs]) if recs else 0.0
            best_risk = min(recs, key=lambda r: ordering.get(r.risk_level, 1)).risk_level if recs else RiskLevel.MEDIUM
            confidence_gap = decision.final_confidence - avg_conf

            counterfactuals.append(
                CounterfactualOption(
                    alternative_action=action_id,
                    supporting_agents=[str(rec.agent_name) for rec in recs],
                    average_confidence=round(avg_conf, 3),
                    confidence_gap=round(confidence_gap, 3),
                    risk_level=best_risk.value if hasattr(best_risk, "value") else str(best_risk),
                    recommended_usage=self._infer_counterfactual_usage(confidence_gap, best_risk),
                    key_considerations=[rec.reasoning for rec in recs[:2]],
                )
            )

        counterfactuals.sort(key=lambda item: item.average_confidence, reverse=True)
        return counterfactuals

    @staticmethod
    def _filter_recommendations(recommendations: List[AgentRecommendation], action_id: str) -> List[AgentRecommendation]:
        return [rec for rec in recommendations if rec.action_id == action_id]

    @staticmethod
    def _infer_counterfactual_usage(confidence_gap: float, risk: RiskLevel) -> str:
        comparable = risk
        if not isinstance(comparable, RiskLevel):
            try:
                comparable = RiskLevel(comparable)  # type: ignore[arg-type]
            except ValueError:
                comparable = RiskLevel.MEDIUM

        if confidence_gap < 0.05 and comparable in (RiskLevel.LOW, RiskLevel.MEDIUM):
            return "Viable alternate path for dry-run simulation"
        if confidence_gap < 0.15:
            return "Track in scenario builder for policy tuning"
        return "Use for retrospective analysis only"


_service: Optional[ExplainabilityService] = None


async def get_explainability_service() -> ExplainabilityService:
    """Factory accessor for explainability service."""
    global _service
    if _service is None:
        _service = ExplainabilityService()
    return _service
