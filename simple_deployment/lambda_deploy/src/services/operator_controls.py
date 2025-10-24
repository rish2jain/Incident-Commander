"""Operator control panel, autonomy toggles, and scenario builder."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional, Set


DEFAULT_THRESHOLDS = {
    "read_only": 1.0,
    "advisory": 0.8,
    "execute": 0.6,
}


@dataclass
class ScenarioTemplate:
    name: str
    severity: str
    description: str
    capabilities: List[str]
    expected_outcomes: List[str]
    guardrails: List[str]

    def render(self, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        overrides = overrides or {}
        payload = {
            "scenario_name": overrides.get("name", self.name),
            "severity": overrides.get("severity", self.severity),
            "description": overrides.get("description", self.description),
            "capabilities": overrides.get("capabilities", self.capabilities),
            "expected_outcomes": overrides.get("expected_outcomes", self.expected_outcomes),
            "guardrails": overrides.get("guardrails", self.guardrails),
        }
        payload.update({k: v for k, v in overrides.items() if k not in payload})
        return payload


class OperatorControlService:
    """Manage autonomy settings, dry-run mode, and scenario generation."""

    def __init__(self) -> None:
        self._autonomy_mode: str = "advisory"
        self._custom_thresholds: Dict[str, float] = {}
        self._global_dry_run: bool = False
        self._dry_run_incidents: Set[str] = set()
        self._scenario_templates: Dict[str, ScenarioTemplate] = {
            "database_spike": ScenarioTemplate(
                name="database_spike",
                severity="critical",
                description="Database latency spike impacts checkout",
                capabilities=["detection", "diagnosis", "resolution", "communication"],
                expected_outcomes=[
                    "Detect connection pool exhaustion",
                    "Offer restart playbook",
                    "Notify customer success",
                ],
                guardrails=[
                    "Require approval if confidence < 0.8",
                    "Pause automated scaling if budget approached",
                ],
            ),
            "api_throttle": ScenarioTemplate(
                name="api_throttle",
                severity="high",
                description="Traffic surge requires API throttling",
                capabilities=["prediction", "resolution", "communication"],
                expected_outcomes=[
                    "Forecast sustained spike",
                    "Apply throttling with rollback",
                    "Coordinate communications",
                ],
                guardrails=[
                    "Escalate if projected churn > 0.2",
                    "Prefer dry-run for new policies",
                ],
            ),
        }
        self._scenario_history: List[Dict[str, Any]] = []

    def get_settings(self) -> Dict[str, Any]:
        return {
            "autonomy_mode": self._autonomy_mode,
            "confidence_threshold": self._effective_threshold(self._autonomy_mode),
            "global_dry_run": self._global_dry_run,
            "dry_run_incidents": list(self._dry_run_incidents),
            "available_modes": list(DEFAULT_THRESHOLDS.keys()),
            "scenario_templates": list(self._scenario_templates.keys()),
        }

    def set_autonomy_mode(self, mode: str, *, confidence_threshold: Optional[float] = None) -> Dict[str, Any]:
        if mode not in DEFAULT_THRESHOLDS:
            raise ValueError(f"Unsupported autonomy mode: {mode}")
        self._autonomy_mode = mode
        if confidence_threshold is not None:
            self._custom_thresholds[mode] = confidence_threshold
        return self.get_settings()

    def toggle_global_dry_run(self, enabled: bool) -> None:
        self._global_dry_run = enabled

    def set_incident_dry_run(self, incident_id: str, enabled: bool) -> None:
        if enabled:
            self._dry_run_incidents.add(incident_id)
        else:
            self._dry_run_incidents.discard(incident_id)

    def is_dry_run(self, incident_id: Optional[str]) -> bool:
        return self._global_dry_run or (incident_id is not None and incident_id in self._dry_run_incidents)

    def evaluate_decision(self, incident_id: str, consensus_decision) -> Dict[str, Any]:
        threshold = self._effective_threshold(self._autonomy_mode)
        requires_manual = self._autonomy_mode == "read_only"
        if consensus_decision.final_confidence < threshold:
            requires_manual = True
        return {
            "requires_manual": requires_manual,
            "threshold": threshold,
            "autonomy_mode": self._autonomy_mode,
            "dry_run": self.is_dry_run(incident_id),
        }

    def can_execute_actions(self, incident_id: str, consensus_decision) -> bool:
        evaluation = self.evaluate_decision(incident_id, consensus_decision)
        if evaluation["requires_manual"] or evaluation["dry_run"]:
            return False
        return True

    def build_scenario(self, template_name: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if template_name not in self._scenario_templates:
            raise ValueError(f"Unknown scenario template: {template_name}")
        rendered = self._scenario_templates[template_name].render(overrides)
        rendered["generated_at"] = datetime.utcnow().isoformat()
        self._scenario_history.append(rendered)
        if len(self._scenario_history) > 25:
            self._scenario_history.pop(0)
        return rendered

    def get_scenario_history(self) -> List[Dict[str, Any]]:
        return list(self._scenario_history)

    def _effective_threshold(self, mode: str) -> float:
        return self._custom_thresholds.get(mode, DEFAULT_THRESHOLDS[mode])


_operator_controls: Optional[OperatorControlService] = None


def get_operator_control_service() -> OperatorControlService:
    global _operator_controls
    if _operator_controls is None:
        _operator_controls = OperatorControlService()
    return _operator_controls
