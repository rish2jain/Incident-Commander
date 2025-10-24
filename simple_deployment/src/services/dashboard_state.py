"""Aggregated dashboard state utilities for API and UI consumers."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict

from src.services.incident_lifecycle_manager import get_incident_lifecycle_manager
from src.services.websocket_manager import get_websocket_manager
from src.services.consensus import get_consensus_engine
from src.services.guardrail_monitor import guardrail_monitor
from src.services.demo_scenario_manager import get_demo_manager
from src.services.finops import get_finops_service


async def get_dashboard_state_summary() -> Dict[str, Any]:
    """Compose a consolidated dashboard snapshot for the UI."""
    lifecycle_manager = get_incident_lifecycle_manager()
    websocket_metrics = get_websocket_manager().get_metrics()

    incidents_summary = lifecycle_manager.get_active_incidents_summary()
    processing_metrics = lifecycle_manager.get_processing_metrics()
    queue_status = lifecycle_manager.get_incident_queue_status()

    consensus_engine = get_consensus_engine()
    consensus_stats = consensus_engine.get_consensus_statistics() if consensus_engine else {}
    latest_decision = (
        consensus_engine.consensus_history[-1]
        if consensus_engine and consensus_engine.consensus_history
        else None
    )

    finops_service, demo_manager = await asyncio.gather(
        get_finops_service(),
        get_demo_manager(),
    )

    finops_dashboard, guardrail_status = await asyncio.gather(
        finops_service.get_dashboard(),
        guardrail_monitor.get_guardrail_status(),
    )

    demo_metrics = demo_manager.get_demo_metrics()

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "connections": websocket_metrics,
        "incidents": {
            "active": incidents_summary,
            "processing": processing_metrics,
            "queue": queue_status,
        },
        "consensus": {
            "statistics": consensus_stats,
            "latest_decision": latest_decision.model_dump(mode="json") if latest_decision else None,
        },
        "guardrails": guardrail_status,
        "finops": {
            "current_costs": finops_dashboard.get("current_costs", {}),
            "spend_by_capability": finops_dashboard.get("spend_by_capability", {}),
            "guardrails": finops_dashboard.get("guardrails", []),
            "cost_savings": finops_dashboard.get("cost_savings"),
            "trend": finops_dashboard.get("trend", {}),
        },
        "demo": demo_metrics,
    }


async def get_current_decision_brief() -> Dict[str, Any]:
    """Return a narrative-ready view of the most recent consensus decision."""
    consensus_engine = get_consensus_engine()
    if not consensus_engine or not consensus_engine.consensus_history:
        return {
            "status": "idle",
            "message": "No consensus decisions have been recorded yet.",
        }

    decision = consensus_engine.consensus_history[-1]
    lifecycle_manager = get_incident_lifecycle_manager()
    incident_status = lifecycle_manager.get_incident_status(decision.incident_id)

    brief: Dict[str, Any] = {
        "status": "ready",
        "decision": decision.model_dump(mode="json"),
        "requires_approval": decision.requires_escalation(),
        "timestamp": decision.decision_time.isoformat(),
        "confidence": decision.final_confidence,
        "participating_agents": decision.participating_agents,
        "fallbacks": decision.fallback_actions,
        "rationale": decision.decision_rationale,
        "minority_opinions": decision.minority_opinions,
    }

    if incident_status:
        brief["incident"] = {
            "current_state": incident_status.get("current_state"),
            "priority": incident_status.get("priority"),
            "processing_duration_seconds": incident_status.get("processing_duration_seconds"),
            "state_transitions": incident_status.get("state_transitions", [])[-5:],
            "assigned_agents": incident_status.get("assigned_agents", []),
            "escalated": incident_status.get("is_escalated", False),
        }

    return brief


async def get_finops_summary() -> Dict[str, Any]:
    """Expose FinOps summary cards for the executive dashboard view."""
    finops_service = await get_finops_service()
    dashboard = await finops_service.get_dashboard()

    return {
        "timestamp": dashboard.get("timestamp"),
        "current_costs": dashboard.get("current_costs", {}),
        "spend_by_capability": dashboard.get("spend_by_capability", {}),
        "optimization_suggestions": dashboard.get("optimization_suggestions", []),
        "guardrails": dashboard.get("guardrails", []),
        "cost_savings": dashboard.get("cost_savings"),
        "trend": dashboard.get("trend", {}),
    }
