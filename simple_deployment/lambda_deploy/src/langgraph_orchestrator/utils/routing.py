"""Routing and state management utilities for LangGraph orchestration."""

from __future__ import annotations

from typing import Any, Dict

from src.langgraph_orchestrator.state_schema import IncidentGraphState


def merge_state_updates(
    base_state: IncidentGraphState, update: IncidentGraphState
) -> IncidentGraphState:
    """
    Merge a state update into the base state.

    This function handles deep merging of nested dictionaries like context
    and appending to lists like timeline.

    Args:
        base_state: The current state
        update: The state update to merge

    Returns:
        A new merged state dictionary
    """
    merged: IncidentGraphState = dict(base_state)

    for key, value in update.items():
        if key == "context" and key in merged:
            # Deep merge context dictionaries
            base_context = dict(merged.get("context", {}))
            update_context = dict(value) if isinstance(value, dict) else {}
            base_context.update(update_context)
            merged["context"] = base_context
        elif key == "timeline" and key in merged:
            # Append timeline events
            base_timeline = list(merged.get("timeline", []))
            update_timeline = list(value) if isinstance(value, list) else []
            base_timeline.extend(update_timeline)
            merged["timeline"] = base_timeline
        else:
            # Direct replacement for other fields
            merged[key] = value

    return merged


def should_escalate(state: IncidentGraphState) -> bool:
    """
    Determine if an incident should be escalated based on state.

    Args:
        state: The current incident graph state

    Returns:
        True if escalation is needed, False otherwise
    """
    incident = state.get("incident")
    if not incident:
        return False

    # Check severity
    severity = str(getattr(incident, "severity", "medium")).lower()
    if severity in {"critical", "high"}:
        return True

    # Check consensus decision
    consensus = state.get("consensus")
    if consensus and hasattr(consensus, "requires_escalation"):
        if callable(consensus.requires_escalation):
            return consensus.requires_escalation()

    return False


def route_based_on_severity(state: IncidentGraphState) -> str:
    """
    Route to different nodes based on incident severity.

    Args:
        state: The current incident graph state

    Returns:
        The name of the next node to execute
    """
    incident = state.get("incident")
    if not incident:
        return "diagnosis"

    severity = str(getattr(incident, "severity", "medium")).lower()

    if severity == "critical":
        return "immediate_escalation"
    elif severity in {"high", "medium"}:
        return "analysis"
    else:
        return "monitoring"


def calculate_confidence_threshold(state: IncidentGraphState) -> float:
    """
    Calculate the confidence threshold for consensus based on state.

    Args:
        state: The current incident graph state

    Returns:
        The confidence threshold (0.0 to 1.0)
    """
    incident = state.get("incident")
    if not incident:
        return 0.7  # Default threshold

    severity = str(getattr(incident, "severity", "medium")).lower()

    # Higher severity requires higher confidence
    severity_thresholds = {
        "critical": 0.85,
        "high": 0.75,
        "medium": 0.65,
        "low": 0.55,
    }

    return severity_thresholds.get(severity, 0.7)
