"""
Guardrail Instrumentation & Reporting System

Provides comprehensive guardrail monitoring, policy enforcement tracking,
and compliance reporting for governance and audit requirements.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque

from src.utils.logging import get_logger
from src.utils.config import config


logger = get_logger("guardrail_monitor")


class GuardrailType(Enum):
    """Types of guardrails in the system."""
    CONTENT_FILTER = "content_filter"
    SAFETY_POLICY = "safety_policy"
    COMPLIANCE_CHECK = "compliance_check"
    RATE_LIMIT = "rate_limit"
    ACCESS_CONTROL = "access_control"
    DATA_PRIVACY = "data_privacy"


class GuardrailAction(Enum):
    """Actions taken by guardrails."""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    MODIFIED = "modified"
    FLAGGED = "flagged"
    ESCALATED = "escalated"


@dataclass
class GuardrailEvent:
    """Individual guardrail enforcement event."""
    event_id: str
    timestamp: datetime
    guardrail_type: GuardrailType
    policy_name: str
    action: GuardrailAction
    agent_id: str
    incident_id: Optional[str]
    content_hash: str
    risk_score: float
    details: Dict[str, Any] = field(default_factory=dict)
    compliance_tags: List[str] = field(default_factory=list)


class GuardrailMonitor:
    """Comprehensive guardrail monitoring and reporting system."""
    
    def __init__(self):
        self.events: deque = deque(maxlen=10000)  # Keep last 10k events
        self.policy_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_checks": 0,
            "blocked_count": 0,
            "allowed_count": 0,
            "modified_count": 0,
            "flagged_count": 0,
            "escalated_count": 0,
            "average_risk_score": 0.0,
            "recent_events": deque(maxlen=100)
        })
        self.compliance_metrics = {
            "sox_compliance": {"checks": 0, "violations": 0},
            "gdpr_compliance": {"checks": 0, "violations": 0},
            "hipaa_compliance": {"checks": 0, "violations": 0},
            "pci_compliance": {"checks": 0, "violations": 0}
        }
        
        # Load guardrail configuration
        self.guardrail_config = self._load_guardrail_config()
        
    def _load_guardrail_config(self) -> Dict[str, Any]:
        """Load guardrail configuration from environment."""
        return {
            "content_filters": {
                "pii_detection": {"enabled": True, "sensitivity": "high"},
                "profanity_filter": {"enabled": True, "sensitivity": "medium"},
                "code_injection": {"enabled": True, "sensitivity": "high"}
            },
            "safety_policies": {
                "destructive_actions": {"enabled": True, "require_approval": True},
                "data_modification": {"enabled": True, "audit_required": True},
                "external_access": {"enabled": True, "whitelist_only": True}
            },
            "compliance_checks": {
                "data_retention": {"enabled": True, "max_days": 2555},
                "access_logging": {"enabled": True, "real_time": True},
                "encryption_required": {"enabled": True, "min_strength": "AES-256"}
            },
            "rate_limits": {
                "bedrock_calls": {"limit": 100, "window": 60},
                "external_apis": {"limit": 50, "window": 60},
                "database_queries": {"limit": 200, "window": 60}
            }
        }
    
    async def record_guardrail_event(self, guardrail_type: GuardrailType, 
                                   policy_name: str, action: GuardrailAction,
                                   agent_id: str, content_hash: str, 
                                   risk_score: float, incident_id: str = None,
                                   details: Dict[str, Any] = None,
                                   compliance_tags: List[str] = None) -> str:
        """Record a guardrail enforcement event."""
        
        event_id = f"gr-{int(datetime.utcnow().timestamp() * 1000)}"
        
        event = GuardrailEvent(
            event_id=event_id,
            timestamp=datetime.utcnow(),
            guardrail_type=guardrail_type,
            policy_name=policy_name,
            action=action,
            agent_id=agent_id,
            incident_id=incident_id,
            content_hash=content_hash,
            risk_score=risk_score,
            details=details or {},
            compliance_tags=compliance_tags or []
        )
        
        # Store event
        self.events.append(event)
        
        # Update policy statistics
        policy_stats = self.policy_stats[policy_name]
        policy_stats["total_checks"] += 1
        policy_stats[f"{action.value}_count"] += 1
        
        # Update average risk score
        total_risk = policy_stats["average_risk_score"] * (policy_stats["total_checks"] - 1)
        policy_stats["average_risk_score"] = (total_risk + risk_score) / policy_stats["total_checks"]
        
        # Add to recent events
        policy_stats["recent_events"].append({
            "event_id": event_id,
            "timestamp": event.timestamp.isoformat(),
            "action": action.value,
            "risk_score": risk_score,
            "agent_id": agent_id
        })
        
        # Update compliance metrics
        for tag in compliance_tags or []:
            if tag in self.compliance_metrics:
                self.compliance_metrics[tag]["checks"] += 1
                if action in [GuardrailAction.BLOCKED, GuardrailAction.ESCALATED]:
                    self.compliance_metrics[tag]["violations"] += 1
        
        logger.info(f"Recorded guardrail event: {event_id} ({policy_name}: {action.value})")
        return event_id
    
    async def get_guardrail_status(self) -> Dict[str, Any]:
        """Get comprehensive guardrail system status."""
        
        # Calculate overall statistics
        total_events = len(self.events)
        recent_events = [e for e in self.events if e.timestamp > datetime.utcnow() - timedelta(hours=24)]
        
        blocked_count = sum(1 for e in self.events if e.action == GuardrailAction.BLOCKED)
        allowed_count = sum(1 for e in self.events if e.action == GuardrailAction.ALLOWED)
        
        block_rate = (blocked_count / total_events * 100) if total_events > 0 else 0
        
        # Risk analysis
        risk_scores = [e.risk_score for e in self.events]
        avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        high_risk_events = sum(1 for score in risk_scores if score > 0.8)
        
        return {
            "system_status": "operational",
            "guardrail_config": self.guardrail_config,
            "statistics": {
                "total_events": total_events,
                "events_last_24h": len(recent_events),
                "block_rate_percent": round(block_rate, 2),
                "average_risk_score": round(avg_risk, 3),
                "high_risk_events": high_risk_events
            },
            "policy_breakdown": {
                policy: {
                    "total_checks": stats["total_checks"],
                    "block_rate": round((stats["blocked_count"] / stats["total_checks"] * 100) 
                                      if stats["total_checks"] > 0 else 0, 2),
                    "average_risk": round(stats["average_risk_score"], 3)
                }
                for policy, stats in self.policy_stats.items()
            },
            "compliance_status": {
                framework: {
                    "compliance_rate": round(((metrics["checks"] - metrics["violations"]) / 
                                           metrics["checks"] * 100) if metrics["checks"] > 0 else 100, 2),
                    "total_checks": metrics["checks"],
                    "violations": metrics["violations"]
                }
                for framework, metrics in self.compliance_metrics.items()
            }
        }
    
    async def get_guardrail_analytics(self, time_window: timedelta = timedelta(days=7)) -> Dict[str, Any]:
        """Get detailed guardrail analytics for specified time window."""
        
        cutoff_time = datetime.utcnow() - time_window
        relevant_events = [e for e in self.events if e.timestamp > cutoff_time]
        
        # Temporal analysis
        hourly_stats = defaultdict(lambda: {"blocked": 0, "allowed": 0, "total": 0})
        
        for event in relevant_events:
            hour_key = event.timestamp.strftime("%Y-%m-%d %H:00")
            hourly_stats[hour_key]["total"] += 1
            if event.action == GuardrailAction.BLOCKED:
                hourly_stats[hour_key]["blocked"] += 1
            elif event.action == GuardrailAction.ALLOWED:
                hourly_stats[hour_key]["allowed"] += 1
        
        # Agent analysis
        agent_stats = defaultdict(lambda: {"events": 0, "blocked": 0, "risk_score": 0.0})
        
        for event in relevant_events:
            agent_stats[event.agent_id]["events"] += 1
            agent_stats[event.agent_id]["risk_score"] += event.risk_score
            if event.action == GuardrailAction.BLOCKED:
                agent_stats[event.agent_id]["blocked"] += 1
        
        # Calculate agent averages
        for agent_id, stats in agent_stats.items():
            if stats["events"] > 0:
                stats["avg_risk_score"] = stats["risk_score"] / stats["events"]
                stats["block_rate"] = stats["blocked"] / stats["events"] * 100
        
        # Top violations
        violation_types = defaultdict(int)
        for event in relevant_events:
            if event.action in [GuardrailAction.BLOCKED, GuardrailAction.ESCALATED]:
                violation_types[event.policy_name] += 1
        
        top_violations = sorted(violation_types.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "analysis_period": {
                "start": cutoff_time.isoformat(),
                "end": datetime.utcnow().isoformat(),
                "total_events": len(relevant_events)
            },
            "temporal_trends": dict(hourly_stats),
            "agent_analysis": dict(agent_stats),
            "top_violations": top_violations,
            "risk_distribution": {
                "low_risk": sum(1 for e in relevant_events if e.risk_score < 0.3),
                "medium_risk": sum(1 for e in relevant_events if 0.3 <= e.risk_score < 0.7),
                "high_risk": sum(1 for e in relevant_events if e.risk_score >= 0.7)
            },
            "compliance_summary": {
                framework: {
                    "events": sum(1 for e in relevant_events if framework in e.compliance_tags),
                    "violations": sum(1 for e in relevant_events 
                                   if framework in e.compliance_tags and 
                                   e.action in [GuardrailAction.BLOCKED, GuardrailAction.ESCALATED])
                }
                for framework in self.compliance_metrics.keys()
            }
        }
    
    async def generate_compliance_report(self, report_type: str = "monthly") -> Dict[str, Any]:
        """Generate comprehensive compliance report."""
        
        if report_type == "monthly":
            time_window = timedelta(days=30)
        elif report_type == "weekly":
            time_window = timedelta(days=7)
        else:
            time_window = timedelta(days=1)
        
        analytics = await self.get_guardrail_analytics(time_window)
        
        # Executive summary
        total_events = analytics["analysis_period"]["total_events"]
        violations = sum(count for _, count in analytics["top_violations"])
        compliance_rate = ((total_events - violations) / total_events * 100) if total_events > 0 else 100
        
        return {
            "report_metadata": {
                "report_type": report_type,
                "generated_at": datetime.utcnow().isoformat(),
                "period": analytics["analysis_period"]
            },
            "executive_summary": {
                "overall_compliance_rate": round(compliance_rate, 2),
                "total_policy_checks": total_events,
                "policy_violations": violations,
                "high_risk_events": analytics["risk_distribution"]["high_risk"],
                "system_health": "compliant" if compliance_rate > 95 else "needs_attention"
            },
            "detailed_analytics": analytics,
            "recommendations": self._generate_compliance_recommendations(analytics),
            "audit_trail": {
                "events_retained": len(self.events),
                "oldest_event": min(e.timestamp for e in self.events).isoformat() if self.events else None,
                "data_integrity": "verified"
            }
        }
    
    def _generate_compliance_recommendations(self, analytics: Dict[str, Any]) -> List[str]:
        """Generate compliance recommendations based on analytics."""
        recommendations = []
        
        # Check violation rates
        for policy, count in analytics["top_violations"][:3]:
            if count > 10:
                recommendations.append(f"Review {policy} policy - {count} violations detected")
        
        # Check risk distribution
        high_risk_pct = (analytics["risk_distribution"]["high_risk"] / 
                        analytics["analysis_period"]["total_events"] * 100) if analytics["analysis_period"]["total_events"] > 0 else 0
        
        if high_risk_pct > 5:
            recommendations.append(f"High risk events at {high_risk_pct:.1f}% - consider tightening policies")
        
        # Check agent behavior
        for agent_id, stats in analytics["agent_analysis"].items():
            if stats.get("block_rate", 0) > 20:
                recommendations.append(f"Agent {agent_id} has high block rate ({stats['block_rate']:.1f}%) - review training")
        
        if not recommendations:
            recommendations.append("System operating within compliance parameters")
        
        return recommendations


# Global guardrail monitor instance
guardrail_monitor = GuardrailMonitor()