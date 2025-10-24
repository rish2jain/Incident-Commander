"""Heuristic agent implementations shared between LangGraph and legacy flows."""

from __future__ import annotations

import asyncio
import math
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Dict, List, Optional

from src.interfaces.agent import (
    CommunicationAgent,
    DetectionAgent,
    DiagnosisAgent,
    PredictionAgent,
    ResolutionAgent,
)
from src.models.agent import (
    ActionType,
    AgentMessage,
    AgentRecommendation,
    AgentType,
    RiskLevel,
)
from src.models.incident import Incident
from src.services.message_bus import MessagePriority, ResilientMessageBus
from src.utils.logging import get_logger


logger = get_logger("heuristic_agents")


@dataclass
class AgentRunArtifacts:
    """Captured metadata from a heuristic agent run."""

    metrics: Dict[str, Any]
    timeline_message: str
    timeline_metadata: Dict[str, Any]
    context_delta: Dict[str, Any]


class _HeuristicAgentMixin:
    """Common helper mixin for heuristic agents."""

    def __init__(self) -> None:
        self._context: Dict[str, Any] = {}
        self._artifacts: Optional[AgentRunArtifacts] = None

    def set_context(self, context: Optional[Dict[str, Any]]) -> None:
        self._context = dict(context or {})

    @property
    def context(self) -> Dict[str, Any]:
        return self._context

    @property
    def artifacts(self) -> AgentRunArtifacts:
        if self._artifacts is None:
            raise RuntimeError("Agent has not been executed yet")
        return self._artifacts

    def _store_artifacts(
        self,
        *,
        metrics: Dict[str, Any],
        timeline_message: str,
        timeline_metadata: Dict[str, Any],
        context_delta: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._artifacts = AgentRunArtifacts(
            metrics=metrics,
            timeline_message=timeline_message,
            timeline_metadata=timeline_metadata,
            context_delta=context_delta or {},
        )


class DetectionHeuristicAgent(_HeuristicAgentMixin, DetectionAgent):
    """Deterministic detection agent used for parity across orchestrators."""

    def __init__(self, *, message_bus: Optional[ResilientMessageBus] = None) -> None:
        DetectionAgent.__init__(self, name="detection_langgraph")
        _HeuristicAgentMixin.__init__(self)
        self._message_bus = message_bus

    async def process_incident(self, incident: Incident) -> List[AgentRecommendation]:
        self._artifacts = None
        start = perf_counter()

        severity = str(incident.severity)

        # Safe type coercion for telemetry_sources
        raw_telemetry = self.context.get("telemetry_sources", [])
        if isinstance(raw_telemetry, (list, tuple)):
            telemetry_sources: List[str] = [str(item) for item in raw_telemetry]
        else:
            telemetry_sources: List[str] = []

        # Safe type coercion for alert_count
        try:
            alert_count = int(self.context.get("alert_count", 1))
        except (ValueError, TypeError):
            alert_count = 1

        recommended_action = (
            ActionType.ESCALATE_INCIDENT
            if severity in {"critical", "high"}
            else ActionType.NOTIFY_TEAM
        )

        risk_map = {
            "critical": RiskLevel.CRITICAL,
            "high": RiskLevel.HIGH,
            "medium": RiskLevel.MEDIUM,
            "low": RiskLevel.LOW,
        }
        risk_level = risk_map.get(severity, RiskLevel.MEDIUM)

        base_confidence = {
            "critical": 0.95,
            "high": 0.9,
            "medium": 0.82,
            "low": 0.72,
        }.get(severity, 0.75)

        telemetry_factor = min(0.04, 0.01 * len(telemetry_sources))
        alert_factor = min(0.05, 0.02 * math.log(max(alert_count, 1), 10))
        confidence = min(0.99, base_confidence + telemetry_factor + alert_factor)

        recommendation = AgentRecommendation(
            agent_name=AgentType.DETECTION,
            incident_id=incident.id,
            action_type=recommended_action,
            action_id=f"detect-{incident.id}",
            confidence=confidence,
            risk_level=risk_level,
            estimated_impact="Detection heuristics confirm incident signal strength",
            reasoning=(
                "Synthesized severity, telemetry coverage, and alert density to initiate incident response"
            ),
            parameters={
                "telemetry_sources": telemetry_sources,
                "alert_count": alert_count,
            },
            urgency=round(confidence, 2),
        )

        latency_ms = (perf_counter() - start) * 1000

        metrics = {
            "latency_ms": round(latency_ms, 2),
            "confidence": round(confidence, 3),
            "risk_level": risk_level.value,
        }
        timeline_metadata = {
            "incident_id": incident.id,
            "telemetry_sources": telemetry_sources,
            "alert_count": alert_count,
            "latency_ms": metrics["latency_ms"],
        }
        timeline_message = (
            f"Detection confidence {confidence:.2f} with action {recommended_action.value}"
        )
        context_delta = {
            "detection_completed_at": incident.detected_at.isoformat(),
            "detection_confidence": confidence,
            "detection_action_id": recommendation.action_id,
        }

        await self._emit_bus_signal(incident_id=incident.id, confidence=confidence)

        self._update_status_success(last_confidence=confidence)
        self._store_artifacts(
            metrics=metrics,
            timeline_message=timeline_message,
            timeline_metadata=timeline_metadata,
            context_delta=context_delta,
        )
        return [recommendation]

    async def analyze_alerts(self, alerts: List[Dict[str, Any]]) -> List[Incident]:  # pragma: no cover - legacy hook
        return []

    async def correlate_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:  # pragma: no cover
        return []

    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        logger.debug("Detection agent received message", extra={"type": message.message_type})
        return None

    async def health_check(self) -> bool:
        return True

    async def _emit_bus_signal(self, *, incident_id: str, confidence: float) -> None:
        if not self._message_bus:
            return

        message = AgentMessage(
            sender_agent=AgentType.DETECTION,
            recipient_agent=AgentType.COMMUNICATION,
            message_type="incident.detected",
            payload={"incident_id": incident_id, "confidence": confidence},
            correlation_id=incident_id,
        )

        try:
            await self._message_bus.send_message(
                message,
                priority=MessagePriority.HIGH,
                ttl_seconds=300,
            )
        except Exception as exc:  # noqa: BLE001 - best effort notification
            logger.warning("Detection bus emission failed", extra={"incident_id": incident_id, "error": str(exc)})


class DiagnosisHeuristicAgent(_HeuristicAgentMixin, DiagnosisAgent):
    """Simple diagnosis agent leveraging incident metadata."""

    KEYWORD_ACTION_MAP = {
        "latency": (ActionType.INCREASE_CAPACITY, "Latency spike suggests scaling nodes"),
        "timeout": (ActionType.RESTART_SERVICE, "Timeout burst indicates service stall"),
        "error": (ActionType.ROLLBACK_DEPLOYMENT, "Recent deploy error signature detected"),
        "cpu": (ActionType.SCALE_UP, "CPU saturation detected"),
        "memory": (ActionType.SCALE_UP, "Memory thrash observed"),
    }

    def __init__(self) -> None:
        DiagnosisAgent.__init__(self, name="diagnosis_langgraph")
        _HeuristicAgentMixin.__init__(self)

    async def process_incident(self, incident: Incident) -> List[AgentRecommendation]:
        self._artifacts = None
        description = incident.description.lower()

        selected_action = ActionType.NO_ACTION
        rationale = "No critical diagnostic findings; monitoring baseline maintained."
        triggered_keywords: List[str] = []

        for keyword, (action, reason) in self.KEYWORD_ACTION_MAP.items():
            if keyword in description:
                selected_action = action
                rationale = reason
                triggered_keywords.append(keyword)
                break

        diagnostics_confidence = self._confidence_for_severity(str(incident.severity))
        recommendation = AgentRecommendation(
            agent_name=AgentType.DIAGNOSIS,
            incident_id=incident.id,
            action_type=selected_action,
            action_id=f"diagnosis-{incident.id}",
            confidence=diagnostics_confidence,
            risk_level=RiskLevel.MEDIUM,
            estimated_impact="Diagnosis agent prioritized remediation pathway",
            reasoning=rationale,
            parameters={
                "keywords_triggered": triggered_keywords,
                "severity": str(incident.severity),
            },
            urgency=0.6 if selected_action != ActionType.NO_ACTION else 0.35,
        )

        metrics = {
            "keywords_matched": triggered_keywords,
            "confidence": round(diagnostics_confidence, 3),
            "log_sources": self.context.get("log_sources", []),
        }
        timeline_metadata = {
            "incident_id": incident.id,
            "keywords": triggered_keywords,
        }
        timeline_message = (
            f"Diagnosis suggests {selected_action.value} with confidence {diagnostics_confidence:.2f}"
        )

        context_delta = {
            "diagnosis_confidence": diagnostics_confidence,
            "diagnosis_action": selected_action.value,
        }

        self._update_status_success(keywords=triggered_keywords)
        self._store_artifacts(
            metrics=metrics,
            timeline_message=timeline_message,
            timeline_metadata=timeline_metadata,
            context_delta=context_delta,
        )
        return [recommendation]

    async def analyze_logs(self, log_sources: List[str], time_range: tuple) -> Dict[str, Any]:  # pragma: no cover
        return {"sources": log_sources, "time_range": time_range}

    async def trace_root_cause(self, incident: Incident) -> Dict[str, Any]:  # pragma: no cover
        return {"incident_id": incident.id, "status": "heuristic"}

    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        logger.debug("Diagnosis agent received message", extra={"type": message.message_type})
        return None

    async def health_check(self) -> bool:
        return True

    @staticmethod
    def _confidence_for_severity(severity: str) -> float:
        mapping = {
            "critical": 0.88,
            "high": 0.82,
            "medium": 0.74,
            "low": 0.65,
        }
        return mapping.get(severity, 0.7)


class PredictionHeuristicAgent(_HeuristicAgentMixin, PredictionAgent):
    """Forecasts cost and duration using business impact heuristics."""

    def __init__(self) -> None:
        PredictionAgent.__init__(self, name="prediction_langgraph")
        _HeuristicAgentMixin.__init__(self)

    async def process_incident(self, incident: Incident) -> List[AgentRecommendation]:
        self._artifacts = None

        severity = str(incident.severity)
        expected_minutes, risk_level = self._estimate_duration_and_risk(severity)

        # Defend against None business_impact
        if incident.business_impact is None:
            cost_per_minute = 0
            # Optionally log warning
        else:
            cost_per_minute = incident.business_impact.calculate_cost_per_minute()

        projected_cost = cost_per_minute * expected_minutes

        action_type = (
            ActionType.INCREASE_CAPACITY
            if risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
            else ActionType.NO_ACTION
        )

        recommendation = AgentRecommendation(
            agent_name=AgentType.PREDICTION,
            incident_id=incident.id,
            action_type=action_type,
            action_id=f"prediction-{incident.id}",
            confidence=self._confidence_for_severity(severity),
            risk_level=risk_level,
            estimated_impact=f"Projected cost ${projected_cost:,.2f} over {expected_minutes:.1f} minutes",
            reasoning="Predictive model combined business impact and historical MTTR baselines",
            parameters={
                "expected_minutes": expected_minutes,
                "cost_per_minute": cost_per_minute,
                "projected_cost": projected_cost,
            },
            urgency=0.7 if risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL} else 0.4,
        )

        metrics = {
            "expected_minutes": round(expected_minutes, 2),
            "projected_cost": round(projected_cost, 2),
            "cost_per_minute": round(cost_per_minute, 2),
        }
        timeline_metadata = {
            "incident_id": incident.id,
            "severity": severity,
            "projected_cost": metrics["projected_cost"],
        }
        timeline_message = (
            f"Projected duration {expected_minutes:.1f}m with cost ${projected_cost:,.2f}; "
            f"recommended action {action_type.value}"
        )
        context_delta = {
            "predicted_minutes": expected_minutes,
            "predicted_cost": projected_cost,
        }

        self._update_status_success(predicted_minutes=expected_minutes)
        self._store_artifacts(
            metrics=metrics,
            timeline_message=timeline_message,
            timeline_metadata=timeline_metadata,
            context_delta=context_delta,
        )
        return [recommendation]

    async def forecast_trends(self, metrics: List[Dict[str, Any]], forecast_minutes: int = 30) -> Dict[str, Any]:  # pragma: no cover
        return {"forecast_minutes": forecast_minutes, "metrics": metrics}

    async def assess_risk(self, current_state: Dict[str, Any]) -> float:  # pragma: no cover - simple heuristic
        severity = current_state.get("severity", "medium")
        _, risk_level = self._estimate_duration_and_risk(str(severity))
        risk_map = {
            RiskLevel.CRITICAL: 0.95,
            RiskLevel.HIGH: 0.8,
            RiskLevel.MEDIUM: 0.55,
            RiskLevel.LOW: 0.35,
        }
        return risk_map.get(risk_level, 0.5)

    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        logger.debug("Prediction agent received message", extra={"type": message.message_type})
        return None

    async def health_check(self) -> bool:
        return True

    @staticmethod
    def _estimate_duration_and_risk(severity: str) -> tuple[float, RiskLevel]:
        mapping = {
            "critical": (45.0, RiskLevel.CRITICAL),
            "high": (30.0, RiskLevel.HIGH),
            "medium": (18.0, RiskLevel.MEDIUM),
            "low": (8.0, RiskLevel.LOW),
        }
        return mapping.get(severity, (15.0, RiskLevel.MEDIUM))

    @staticmethod
    def _confidence_for_severity(severity: str) -> float:
        confidence_map = {
            "critical": 0.9,
            "high": 0.85,
            "medium": 0.78,
            "low": 0.7,
        }
        return confidence_map.get(severity, 0.75)


class ResolutionHeuristicAgent(_HeuristicAgentMixin, ResolutionAgent):
    """Translation layer between consensus output and resolution planning."""

    def __init__(self) -> None:
        ResolutionAgent.__init__(self, name="resolution_langgraph")
        _HeuristicAgentMixin.__init__(self)
        self._consensus = None

    def set_consensus(self, consensus) -> None:
        self._consensus = consensus

    async def process_incident(self, incident: Incident) -> List[AgentRecommendation]:
        self._artifacts = None
        consensus = self._consensus

        if consensus is not None:
            action_value = getattr(consensus, "action_type", ActionType.NO_ACTION.value)
            confidence = getattr(consensus, "final_confidence", 0.5)
            rationale = getattr(consensus, "decision_rationale", None) or "Consensus-selected action plan"

            # Safely call requires_escalation if it exists
            if callable(getattr(consensus, "requires_escalation", None)):
                requires_human = consensus.requires_escalation()
            else:
                requires_human = True
        else:
            action_value = ActionType.NO_ACTION.value
            confidence = 0.5
            rationale = "Consensus unavailable; awaiting operator guidance"
            requires_human = True

        try:
            action_type = ActionType(action_value)
        except ValueError:
            action_type = ActionType.NO_ACTION

        recommendation = AgentRecommendation(
            agent_name=AgentType.RESOLUTION,
            incident_id=incident.id,
            action_type=action_type,
            action_id=f"resolution-{incident.id}",
            confidence=confidence,
            risk_level=RiskLevel.MEDIUM,
            estimated_impact="Resolution node translated consensus into runbook steps",
            reasoning=rationale,
            parameters={
                "consensus_action": getattr(consensus, "selected_action", None),
                "requires_human_approval": requires_human,
            },
            urgency=0.8 if not requires_human else 0.5,
        )

        metrics = {
            "requires_human_approval": requires_human,
            "confidence": round(confidence, 3),
        }
        timeline_metadata = {
            "incident_id": incident.id,
            "requires_human_approval": requires_human,
        }
        timeline_message = (
            f"Resolution prepared action {action_type.value} (confidence {confidence:.2f})"
        )
        context_delta = {
            "resolution_action": action_type.value,
            "resolution_ready": True,
        }

        self._update_status_success(resolution_action=action_type.value)
        self._store_artifacts(
            metrics=metrics,
            timeline_message=timeline_message,
            timeline_metadata=timeline_metadata,
            context_delta=context_delta,
        )
        return [recommendation]

    async def execute_action(self, recommendation: AgentRecommendation) -> Dict[str, Any]:  # pragma: no cover
        await asyncio.sleep(0)
        return {
            "action_id": recommendation.action_id,
            "status": "simulated",
            "notes": "Execution simulated in heuristic agent",
        }

    async def validate_action(self, recommendation: AgentRecommendation) -> bool:  # pragma: no cover
        return recommendation.confidence >= 0.4

    async def rollback_action(self, action_id: str) -> Dict[str, Any]:  # pragma: no cover
        await asyncio.sleep(0)
        return {"action_id": action_id, "status": "rolled_back", "notes": "Heuristic rollback complete"}

    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        logger.debug("Resolution agent received message", extra={"type": message.message_type})
        return None

    async def health_check(self) -> bool:
        return True


class CommunicationHeuristicAgent(_HeuristicAgentMixin, CommunicationAgent):
    """Generates stakeholder updates using incident state."""

    def __init__(self) -> None:
        CommunicationAgent.__init__(self, name="communication_langgraph")
        _HeuristicAgentMixin.__init__(self)
        self._consensus = None
        self._resolution_recommendation: Optional[AgentRecommendation] = None

    def set_consensus(self, consensus) -> None:
        self._consensus = consensus

    def set_resolution(self, resolution_recommendation: Optional[AgentRecommendation]) -> None:
        self._resolution_recommendation = resolution_recommendation

    async def process_incident(self, incident: Incident) -> List[AgentRecommendation]:
        self._artifacts = None
        consensus = self._consensus
        resolution = self._resolution_recommendation

        summary = self._build_summary(
            incident_id=incident.id,
            consensus=consensus,
            resolution=resolution,
        )

        recommendation = AgentRecommendation(
            agent_name=AgentType.COMMUNICATION,
            incident_id=incident.id,
            action_type=ActionType.NOTIFY_TEAM,
            action_id=f"communication-{incident.id}",
            confidence=0.92,
            risk_level=RiskLevel.LOW,
            estimated_impact="Stakeholders receive clear, actionable update",
            reasoning="Generated summary consolidates detection, diagnosis, prediction, and resolution signals",
            parameters={
                "audiences": ["sre_on_call", "product_owner", "executive_bridge"],
                "channels": ["slack", "email"],
                "summary": summary,
            },
            urgency=0.85,
        )

        metrics = {
            "summary_length": len(summary),
        }
        timeline_metadata = {
            "incident_id": incident.id,
            "audiences": recommendation.parameters["audiences"],
        }
        timeline_message = "Stakeholder update generated"
        context_delta = {
            "communication_summary": summary,
            "communication_channels": recommendation.parameters["channels"],
        }

        self._update_status_success(summary_length=len(summary))
        self._store_artifacts(
            metrics=metrics,
            timeline_message=timeline_message,
            timeline_metadata=timeline_metadata,
            context_delta=context_delta,
        )
        return [recommendation]

    async def handle_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        logger.debug("Communication agent received message", extra={"type": message.message_type})
        return None

    async def health_check(self) -> bool:
        return True

    def _build_summary(self, *, incident_id: str, consensus, resolution) -> str:
        # Defensive consensus attribute access
        if consensus:
            consensus_action = getattr(consensus, "selected_action", "unknown action")
            consensus_type_raw = getattr(consensus, "action_type", None)
            if hasattr(consensus_type_raw, "value"):
                consensus_type = consensus_type_raw.value
            elif consensus_type_raw is not None:
                consensus_type = str(consensus_type_raw)
            else:
                consensus_type = "unknown"
            consensus_confidence = getattr(consensus, "final_confidence", 0.0)
            consensus_part = f"Action {consensus_action} ({consensus_type}) at confidence {consensus_confidence:.2f}"
        else:
            consensus_part = "Awaiting consensus outcome"
        if resolution:
            resolution_action = (
                resolution.action_type.value
                if hasattr(resolution.action_type, "value")
                else str(resolution.action_type)
            )
            resolution_part = f"Resolution step {resolution_action} prepared"
        else:
            resolution_part = "Resolution pending"
        return (
            f"Incident {incident_id}: {consensus_part}. {resolution_part}. "
            "Communications ready for SRE, product, and executive channels."
        )

    async def send_notification(self, channel: str, message: str, severity: str) -> bool:  # pragma: no cover
        logger.debug(
            "Sending notification",
            extra={"channel": channel, "severity": severity, "preview": message[:80]},
        )
        await asyncio.sleep(0)
        return True

    async def escalate_incident(self, incident: Incident, escalation_level: str) -> bool:  # pragma: no cover
        logger.debug(
            "Escalating incident",
            extra={"incident_id": incident.id, "level": escalation_level},
        )
        await asyncio.sleep(0)
        return True
