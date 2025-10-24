"""
Guardrail Tracking System

Monitors and tracks guardrail decisions, policy enforcement, and compliance
reporting for the Autonomous Incident Commander system. Provides analytics
on guardrail effectiveness and policy adherence.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import json

from src.utils.logging import get_logger
from src.utils.config import config
from src.utils.constants import SECURITY_CONFIG


logger = get_logger("guardrail_tracker")


class GuardrailType(str, Enum):
    """Types of guardrails in the system."""
    CONTENT_FILTER = "content_filter"
    SAFETY_CHECK = "safety_check"
    COMPLIANCE_POLICY = "compliance_policy"
    RISK_ASSESSMENT = "risk_assessment"
    ACTION_APPROVAL = "action_approval"
    DATA_PROTECTION = "data_protection"
    RATE_LIMITING = "rate_limiting"
    ACCESS_CONTROL = "access_control"


class GuardrailDecision(str, Enum):
    """Possible guardrail decisions."""
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"
    ESCALATE = "escalate"
    MODIFY = "modify"


class GuardrailSeverity(str, Enum):
    """Severity levels for guardrail violations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GuardrailEvent:
    """Individual guardrail enforcement event."""
    id: str
    timestamp: datetime
    guardrail_type: GuardrailType
    guardrail_name: str
    decision: GuardrailDecision
    severity: GuardrailSeverity
    
    # Context information
    agent_name: Optional[str] = None
    incident_id: Optional[str] = None
    action_type: Optional[str] = None
    
    # Decision details
    confidence_score: float = 0.0
    reasoning: str = ""
    policy_violated: Optional[str] = None
    
    # Content and metadata
    original_content: Optional[str] = None
    modified_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Processing details
    processing_time_ms: float = 0.0
    model_used: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "guardrail_type": self.guardrail_type.value,
            "guardrail_name": self.guardrail_name,
            "decision": self.decision.value,
            "severity": self.severity.value,
            "agent_name": self.agent_name,
            "incident_id": self.incident_id,
            "action_type": self.action_type,
            "confidence_score": self.confidence_score,
            "reasoning": self.reasoning,
            "policy_violated": self.policy_violated,
            "original_content": self.original_content,
            "modified_content": self.modified_content,
            "metadata": self.metadata,
            "processing_time_ms": self.processing_time_ms,
            "model_used": self.model_used
        }


@dataclass
class GuardrailMetrics:
    """Metrics for a specific guardrail."""
    guardrail_name: str
    guardrail_type: GuardrailType
    
    # Event counts
    total_events: int = 0
    allow_count: int = 0
    block_count: int = 0
    warn_count: int = 0
    escalate_count: int = 0
    modify_count: int = 0
    
    # Performance metrics
    average_processing_time_ms: float = 0.0
    min_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0
    
    # Effectiveness metrics
    false_positive_count: int = 0
    false_negative_count: int = 0
    accuracy_rate: float = 0.0
    
    # Time tracking
    first_event: Optional[datetime] = None
    last_event: Optional[datetime] = None
    
    def calculate_block_rate(self) -> float:
        """Calculate the percentage of events that were blocked."""
        if self.total_events == 0:
            return 0.0
        return (self.block_count / self.total_events) * 100
    
    def calculate_escalation_rate(self) -> float:
        """Calculate the percentage of events that were escalated."""
        if self.total_events == 0:
            return 0.0
        return (self.escalate_count / self.total_events) * 100
    
    def update_processing_time(self, processing_time_ms: float) -> None:
        """Update processing time metrics."""
        if self.total_events == 1:  # First event
            self.min_processing_time_ms = processing_time_ms
            self.max_processing_time_ms = processing_time_ms
            self.average_processing_time_ms = processing_time_ms
        else:
            self.min_processing_time_ms = min(self.min_processing_time_ms, processing_time_ms)
            self.max_processing_time_ms = max(self.max_processing_time_ms, processing_time_ms)
            
            # Update running average
            total_time = self.average_processing_time_ms * (self.total_events - 1)
            total_time += processing_time_ms
            self.average_processing_time_ms = total_time / self.total_events


@dataclass
class ComplianceReport:
    """Compliance report for guardrail enforcement."""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    
    # Summary statistics
    total_events: int
    total_violations: int
    compliance_rate: float
    
    # Breakdown by type
    events_by_type: Dict[str, int]
    violations_by_severity: Dict[str, int]
    
    # Policy adherence
    policy_violations: List[Dict[str, Any]]
    top_violated_policies: List[Dict[str, Any]]
    
    # Recommendations
    recommendations: List[str]
    
    # Detailed metrics
    guardrail_metrics: Dict[str, GuardrailMetrics]


class GuardrailTracker:
    """
    Comprehensive guardrail tracking and compliance monitoring system.
    
    Tracks all guardrail decisions, analyzes policy enforcement effectiveness,
    and generates compliance reports for audit and optimization purposes.
    """
    
    def __init__(self):
        self.logger = get_logger("guardrail_tracker")
        self.events: List[GuardrailEvent] = []
        self.metrics: Dict[str, GuardrailMetrics] = {}
        self.tracking_active = False
        
        # Configuration
        self.max_events_in_memory = 10000
        self.retention_period = timedelta(days=SECURITY_CONFIG["audit_log_retention_days"])
        
        # Policy definitions (can be loaded from configuration)
        self.policies = self._load_policy_definitions()
        
        # Analytics cache
        self._analytics_cache: Dict[str, Any] = {}
        self._cache_expiry: Optional[datetime] = None
        self._cache_duration = timedelta(minutes=5)
    
    def _load_policy_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Load guardrail policy definitions."""
        return {
            "content_safety": {
                "description": "Prevent harmful or inappropriate content generation",
                "severity_threshold": GuardrailSeverity.HIGH,
                "auto_block": True
            },
            "pii_protection": {
                "description": "Protect personally identifiable information",
                "severity_threshold": GuardrailSeverity.MEDIUM,
                "auto_block": True
            },
            "action_risk_assessment": {
                "description": "Assess risk level of automated actions",
                "severity_threshold": GuardrailSeverity.HIGH,
                "auto_block": False
            },
            "compliance_check": {
                "description": "Ensure compliance with regulatory requirements",
                "severity_threshold": GuardrailSeverity.MEDIUM,
                "auto_block": True
            },
            "rate_limit_enforcement": {
                "description": "Enforce API and service rate limits",
                "severity_threshold": GuardrailSeverity.LOW,
                "auto_block": True
            }
        }
    
    async def start_tracking(self) -> None:
        """Start guardrail tracking."""
        if self.tracking_active:
            self.logger.warning("Guardrail tracking already active")
            return
        
        self.tracking_active = True
        self.logger.info("Guardrail tracking started")
    
    async def stop_tracking(self) -> None:
        """Stop guardrail tracking."""
        self.tracking_active = False
        self.logger.info("Guardrail tracking stopped")
    
    async def record_guardrail_event(self, event: GuardrailEvent) -> None:
        """Record a guardrail enforcement event."""
        if not self.tracking_active:
            return
        
        # Add to events list
        self.events.append(event)
        
        # Update metrics
        await self._update_guardrail_metrics(event)
        
        # Manage memory usage
        if len(self.events) > self.max_events_in_memory:
            # Remove oldest events (in production, these would be persisted to storage)
            self.events = self.events[-self.max_events_in_memory:]
        
        # Clear analytics cache
        self._invalidate_cache()
        
        # Log significant events
        if event.decision in [GuardrailDecision.BLOCK, GuardrailDecision.ESCALATE]:
            self.logger.warning(
                f"Guardrail {event.guardrail_name} {event.decision.value}: {event.reasoning}"
            )
        
        self.logger.debug(f"Recorded guardrail event: {event.id}")
    
    async def _update_guardrail_metrics(self, event: GuardrailEvent) -> None:
        """Update metrics for a guardrail based on new event."""
        guardrail_name = event.guardrail_name
        
        if guardrail_name not in self.metrics:
            self.metrics[guardrail_name] = GuardrailMetrics(
                guardrail_name=guardrail_name,
                guardrail_type=event.guardrail_type
            )
        
        metrics = self.metrics[guardrail_name]
        
        # Update event counts
        metrics.total_events += 1
        
        if event.decision == GuardrailDecision.ALLOW:
            metrics.allow_count += 1
        elif event.decision == GuardrailDecision.BLOCK:
            metrics.block_count += 1
        elif event.decision == GuardrailDecision.WARN:
            metrics.warn_count += 1
        elif event.decision == GuardrailDecision.ESCALATE:
            metrics.escalate_count += 1
        elif event.decision == GuardrailDecision.MODIFY:
            metrics.modify_count += 1
        
        # Update timing
        metrics.update_processing_time(event.processing_time_ms)
        
        if metrics.first_event is None:
            metrics.first_event = event.timestamp
        metrics.last_event = event.timestamp
    
    async def get_guardrail_metrics(self, guardrail_name: Optional[str] = None) -> Dict[str, GuardrailMetrics]:
        """Get metrics for specific guardrail or all guardrails."""
        if guardrail_name:
            if guardrail_name in self.metrics:
                return {guardrail_name: self.metrics[guardrail_name]}
            else:
                return {}
        
        return dict(self.metrics)
    
    async def get_recent_events(
        self,
        hours: int = 24,
        guardrail_type: Optional[GuardrailType] = None,
        decision: Optional[GuardrailDecision] = None
    ) -> List[GuardrailEvent]:
        """Get recent guardrail events with optional filtering."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        filtered_events = [
            event for event in self.events
            if event.timestamp >= cutoff_time
        ]
        
        if guardrail_type:
            filtered_events = [
                event for event in filtered_events
                if event.guardrail_type == guardrail_type
            ]
        
        if decision:
            filtered_events = [
                event for event in filtered_events
                if event.decision == decision
            ]
        
        return sorted(filtered_events, key=lambda x: x.timestamp, reverse=True)
    
    async def get_compliance_analytics(self) -> Dict[str, Any]:
        """Get comprehensive compliance analytics."""
        # Check cache first
        if self._analytics_cache and self._cache_expiry and datetime.utcnow() < self._cache_expiry:
            return self._analytics_cache
        
        current_time = datetime.utcnow()
        last_24h = current_time - timedelta(hours=24)
        last_7d = current_time - timedelta(days=7)
        
        # Get events for different time periods
        events_24h = [e for e in self.events if e.timestamp >= last_24h]
        events_7d = [e for e in self.events if e.timestamp >= last_7d]
        
        # Calculate analytics
        analytics = {
            "summary": {
                "total_events_24h": len(events_24h),
                "total_events_7d": len(events_7d),
                "total_events_all_time": len(self.events),
                "active_guardrails": len(self.metrics),
                "compliance_rate_24h": self._calculate_compliance_rate(events_24h),
                "compliance_rate_7d": self._calculate_compliance_rate(events_7d)
            },
            "decisions_breakdown_24h": self._get_decisions_breakdown(events_24h),
            "decisions_breakdown_7d": self._get_decisions_breakdown(events_7d),
            "severity_breakdown_24h": self._get_severity_breakdown(events_24h),
            "severity_breakdown_7d": self._get_severity_breakdown(events_7d),
            "top_triggered_guardrails": self._get_top_triggered_guardrails(events_7d),
            "policy_violations": self._get_policy_violations(events_7d),
            "performance_metrics": self._get_performance_metrics(),
            "trends": self._calculate_trends()
        }
        
        # Cache results
        self._analytics_cache = analytics
        self._cache_expiry = current_time + self._cache_duration
        
        return analytics
    
    def _calculate_compliance_rate(self, events: List[GuardrailEvent]) -> float:
        """Calculate compliance rate (percentage of allowed events)."""
        if not events:
            return 100.0
        
        allowed_events = sum(1 for e in events if e.decision == GuardrailDecision.ALLOW)
        return (allowed_events / len(events)) * 100
    
    def _get_decisions_breakdown(self, events: List[GuardrailEvent]) -> Dict[str, int]:
        """Get breakdown of guardrail decisions."""
        breakdown = {decision.value: 0 for decision in GuardrailDecision}
        
        for event in events:
            breakdown[event.decision.value] += 1
        
        return breakdown
    
    def _get_severity_breakdown(self, events: List[GuardrailEvent]) -> Dict[str, int]:
        """Get breakdown by severity level."""
        breakdown = {severity.value: 0 for severity in GuardrailSeverity}
        
        for event in events:
            breakdown[event.severity.value] += 1
        
        return breakdown
    
    def _get_top_triggered_guardrails(self, events: List[GuardrailEvent], limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently triggered guardrails."""
        guardrail_counts: Dict[str, int] = {}
        
        for event in events:
            guardrail_counts[event.guardrail_name] = guardrail_counts.get(event.guardrail_name, 0) + 1
        
        sorted_guardrails = sorted(guardrail_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                "guardrail_name": name,
                "trigger_count": count,
                "guardrail_type": self.metrics.get(name, {}).guardrail_type.value if name in self.metrics else "unknown"
            }
            for name, count in sorted_guardrails[:limit]
        ]
    
    def _get_policy_violations(self, events: List[GuardrailEvent]) -> List[Dict[str, Any]]:
        """Get policy violations summary."""
        violations = []
        
        for event in events:
            if event.decision in [GuardrailDecision.BLOCK, GuardrailDecision.ESCALATE] and event.policy_violated:
                violations.append({
                    "timestamp": event.timestamp.isoformat(),
                    "policy": event.policy_violated,
                    "guardrail": event.guardrail_name,
                    "severity": event.severity.value,
                    "agent": event.agent_name,
                    "incident_id": event.incident_id
                })
        
        return violations
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for guardrails."""
        if not self.metrics:
            return {}
        
        total_events = sum(m.total_events for m in self.metrics.values())
        avg_processing_time = sum(m.average_processing_time_ms for m in self.metrics.values()) / len(self.metrics)
        
        return {
            "total_guardrails": len(self.metrics),
            "total_events_processed": total_events,
            "average_processing_time_ms": avg_processing_time,
            "fastest_guardrail": min(self.metrics.values(), key=lambda m: m.average_processing_time_ms).guardrail_name,
            "slowest_guardrail": max(self.metrics.values(), key=lambda m: m.average_processing_time_ms).guardrail_name
        }
    
    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate trends in guardrail activity."""
        current_time = datetime.utcnow()
        
        # Compare last 24h vs previous 24h
        last_24h = current_time - timedelta(hours=24)
        prev_24h = current_time - timedelta(hours=48)
        
        recent_events = [e for e in self.events if e.timestamp >= last_24h]
        previous_events = [e for e in self.events if prev_24h <= e.timestamp < last_24h]
        
        recent_blocks = sum(1 for e in recent_events if e.decision == GuardrailDecision.BLOCK)
        previous_blocks = sum(1 for e in previous_events if e.decision == GuardrailDecision.BLOCK)
        
        block_trend = "stable"
        if recent_blocks > previous_blocks * 1.2:
            block_trend = "increasing"
        elif recent_blocks < previous_blocks * 0.8:
            block_trend = "decreasing"
        
        return {
            "events_trend": {
                "recent_24h": len(recent_events),
                "previous_24h": len(previous_events),
                "change_percentage": ((len(recent_events) - len(previous_events)) / max(1, len(previous_events))) * 100
            },
            "blocks_trend": {
                "recent_24h": recent_blocks,
                "previous_24h": previous_blocks,
                "trend": block_trend
            }
        }
    
    async def generate_compliance_report(
        self,
        period_days: int = 7,
        include_recommendations: bool = True
    ) -> ComplianceReport:
        """Generate comprehensive compliance report."""
        current_time = datetime.utcnow()
        period_start = current_time - timedelta(days=period_days)
        
        # Filter events for the period
        period_events = [
            event for event in self.events
            if period_start <= event.timestamp <= current_time
        ]
        
        # Calculate summary statistics
        total_events = len(period_events)
        violations = [e for e in period_events if e.decision in [GuardrailDecision.BLOCK, GuardrailDecision.ESCALATE]]
        total_violations = len(violations)
        compliance_rate = ((total_events - total_violations) / max(1, total_events)) * 100
        
        # Events by type
        events_by_type = {}
        for event in period_events:
            event_type = event.guardrail_type.value
            events_by_type[event_type] = events_by_type.get(event_type, 0) + 1
        
        # Violations by severity
        violations_by_severity = {}
        for violation in violations:
            severity = violation.severity.value
            violations_by_severity[severity] = violations_by_severity.get(severity, 0) + 1
        
        # Policy violations
        policy_violations = []
        policy_counts: Dict[str, int] = {}
        
        for violation in violations:
            if violation.policy_violated:
                policy_counts[violation.policy_violated] = policy_counts.get(violation.policy_violated, 0) + 1
                policy_violations.append({
                    "timestamp": violation.timestamp.isoformat(),
                    "policy": violation.policy_violated,
                    "guardrail": violation.guardrail_name,
                    "severity": violation.severity.value,
                    "reasoning": violation.reasoning
                })
        
        # Top violated policies
        top_violated_policies = [
            {"policy": policy, "violation_count": count}
            for policy, count in sorted(policy_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Generate recommendations
        recommendations = []
        if include_recommendations:
            recommendations = self._generate_compliance_recommendations(period_events, violations)
        
        return ComplianceReport(
            report_id=f"compliance-{current_time.strftime('%Y%m%d-%H%M%S')}",
            generated_at=current_time,
            period_start=period_start,
            period_end=current_time,
            total_events=total_events,
            total_violations=total_violations,
            compliance_rate=compliance_rate,
            events_by_type=events_by_type,
            violations_by_severity=violations_by_severity,
            policy_violations=policy_violations,
            top_violated_policies=top_violated_policies,
            recommendations=recommendations,
            guardrail_metrics=dict(self.metrics)
        )
    
    def _generate_compliance_recommendations(
        self,
        events: List[GuardrailEvent],
        violations: List[GuardrailEvent]
    ) -> List[str]:
        """Generate recommendations for improving compliance."""
        recommendations = []
        
        if not events:
            recommendations.append("No guardrail events recorded - ensure tracking is properly configured")
            return recommendations
        
        violation_rate = len(violations) / len(events)
        
        if violation_rate > 0.1:  # More than 10% violations
            recommendations.append("High violation rate detected - review and strengthen guardrail policies")
        
        # Check for frequently violated policies
        policy_counts: Dict[str, int] = {}
        for violation in violations:
            if violation.policy_violated:
                policy_counts[violation.policy_violated] = policy_counts.get(violation.policy_violated, 0) + 1
        
        if policy_counts:
            most_violated = max(policy_counts.items(), key=lambda x: x[1])
            if most_violated[1] > 5:  # More than 5 violations of same policy
                recommendations.append(f"Policy '{most_violated[0]}' frequently violated - consider policy review or additional training")
        
        # Check for performance issues
        slow_guardrails = [
            name for name, metrics in self.metrics.items()
            if metrics.average_processing_time_ms > 1000  # More than 1 second
        ]
        
        if slow_guardrails:
            recommendations.append(f"Slow guardrail processing detected: {', '.join(slow_guardrails)} - consider optimization")
        
        # Check for escalation patterns
        escalations = [e for e in violations if e.decision == GuardrailDecision.ESCALATE]
        if len(escalations) > len(violations) * 0.3:  # More than 30% escalations
            recommendations.append("High escalation rate - consider adjusting guardrail sensitivity or approval thresholds")
        
        if not recommendations:
            recommendations.append("Compliance metrics are within acceptable ranges - continue monitoring")
        
        return recommendations
    
    def _invalidate_cache(self) -> None:
        """Invalidate analytics cache."""
        self._analytics_cache = {}
        self._cache_expiry = None
    
    async def export_events(
        self,
        format_type: str = "json",
        hours: int = 24
    ) -> str:
        """Export guardrail events in specified format."""
        events = await self.get_recent_events(hours=hours)
        
        if format_type.lower() == "json":
            return json.dumps([event.to_dict() for event in events], indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")


# Global instance for use across the application
_guardrail_tracker_instance: Optional[GuardrailTracker] = None


def get_guardrail_tracker() -> GuardrailTracker:
    """Get the global guardrail tracker instance."""
    global _guardrail_tracker_instance
    
    if _guardrail_tracker_instance is None:
        _guardrail_tracker_instance = GuardrailTracker()
    
    return _guardrail_tracker_instance