"""Insights & analytics for resilience scorecards and benchmarking."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.orchestrator.swarm_coordinator import AgentSwarmCoordinator, IncidentProcessingState


class AnalyticsService:
    """Generates scorecards, SLO impact analysis, and benchmarking."""

    def __init__(self) -> None:
        self._history: deque = deque(maxlen=20)

    def build_insights(self, coordinator: AgentSwarmCoordinator) -> Dict[str, Any]:
        states = list(coordinator.processing_states.values())
        if not states:
            return {
                "resilience_scorecard": {},
                "slo_impact": {},
                "benchmarks": {},
                "timeline": []
            }

        scorecard = self._build_resilience_scorecard(states)
        slo_impact = self._build_slo_impact(states)
        benchmarks = self._build_benchmarks(states)

        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "resilience_scorecard": scorecard,
            "slo_impact": slo_impact,
            "benchmarks": benchmarks,
        }
        self._history.append(snapshot)
        snapshot["timeline"] = list(self._history)
        return snapshot

    def _build_resilience_scorecard(self, states: List[IncidentProcessingState]) -> Dict[str, Any]:
        total_duration = sum(state.total_duration_seconds for state in states)
        completed = [s for s in states if s.consensus_decision]
        avg_confidence = (
            sum(s.consensus_decision.final_confidence for s in completed) / len(completed)
            if completed else 0.0
        )
        automation = [s for s in completed if not s.consensus_decision.requires_human_approval]
        near_misses = [s for s in completed if s.consensus_decision.final_confidence < 0.75]

        change_failures = [
            s for s in completed
            if s.consensus_decision.conflicts_detected or s.consensus_decision.requires_human_approval
        ]

        return {
            "incident_count": len(states),
            "average_processing_seconds": round(total_duration / len(states), 2),
            "automation_rate": round(len(automation) / max(1, len(completed)), 3),
            "mean_confidence": round(avg_confidence, 3),
            "near_miss_count": len(near_misses),
            "change_failure_rate": round(len(change_failures) / max(1, len(completed)), 3),
        }

    def _build_slo_impact(self, states: List[IncidentProcessingState]) -> Dict[str, Any]:
        slo_threshold_seconds = 900  # 15 minutes target resolution window
        slo_met = 0
        avoided_minutes = 0.0

        for state in states:
            duration = state.total_duration_seconds
            if duration <= slo_threshold_seconds:
                slo_met += 1
            baseline_duration = 1800  # 30 minutes baseline
            avoided = max(0.0, (baseline_duration - duration) / 60.0)
            avoided_minutes += avoided

        total_incidents = len(states)
        return {
            "slo_met": slo_met,
            "slo_breached": total_incidents - slo_met,
            "slo_compliance_rate": round(slo_met / max(1, total_incidents), 3),
            "minutes_of_downtime_avoided": round(avoided_minutes, 2),
            "projected_annual_avoidance_hours": round((avoided_minutes / 60.0) * 52, 2),
        }

    def _build_benchmarks(self, states: List[IncidentProcessingState]) -> Dict[str, Any]:
        team_metrics: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "incidents": 0,
            "avg_confidence": 0.0,
            "automation_rate": 0.0,
            "total_duration": 0.0,
            "automation_count": 0,
        })

        for state in states:
            tags = state.incident.metadata.tags or {}
            team = tags.get("team") or tags.get("service") or "unassigned"
            metrics = team_metrics[team]
            metrics["incidents"] += 1
            metrics["total_duration"] += state.total_duration_seconds
            if state.consensus_decision:
                metrics["avg_confidence"] += state.consensus_decision.final_confidence
                if not state.consensus_decision.requires_human_approval:
                    metrics["automation_count"] += 1

        leaderboard: List[Dict[str, Any]] = []
        for team, values in team_metrics.items():
            count = values["incidents"]
            avg_conf = values["avg_confidence"] / count if count else 0.0
            automation_rate = values["automation_count"] / count if count else 0.0
            leaderboard.append({
                "team": team,
                "incident_count": count,
                "avg_confidence": round(avg_conf, 3),
                "automation_rate": round(automation_rate, 3),
                "avg_resolution_seconds": round(values["total_duration"] / max(1, count), 2),
            })

        leaderboard.sort(key=lambda entry: entry["avg_confidence"], reverse=True)

        return {
            "team_leaderboard": leaderboard[:10],
            "total_teams_tracked": len(leaderboard),
        }


_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
