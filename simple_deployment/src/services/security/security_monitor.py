"""
Security monitoring and threat detection service.

This module implements behavioral analysis for agent compromise detection,
security event correlation, automated incident response, and security metrics.
"""

import asyncio
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from uuid import uuid4

import boto3
import structlog
from prometheus_client import Counter, Histogram, Gauge

from src.models.security import (
    SecurityAlert, SecurityEventType, SecuritySeverity,
    SecurityMetrics, ThreatIntelligence, AuditEvent
)
from src.utils.config import ConfigManager
from src.utils.exceptions import SecurityError


logger = structlog.get_logger(__name__)


# Prometheus metrics
security_events_total = Counter('security_events_total', 'Total security events', ['event_type', 'severity'])
security_alerts_total = Counter('security_alerts_total', 'Total security alerts', ['alert_type', 'severity'])
threat_detection_duration = Histogram('threat_detection_duration_seconds', 'Time spent on threat detection')
suspicious_behaviors_detected = Counter('suspicious_behaviors_detected_total', 'Suspicious behaviors detected')
agent_compromise_attempts = Counter('agent_compromise_attempts_total', 'Agent compromise attempts')
automated_responses_triggered = Counter('automated_responses_triggered_total', 'Automated security responses')


class SecurityMonitor:
    """
    Security monitoring and threat detection service.
    
    Features:
    - Behavioral analysis for agent compromise detection
    - Security event correlation and threat intelligence integration
    - Automated security incident response and containment
    - Security metrics and compliance dashboards
    - Real-time threat detection and alerting
    """
    
    def __init__(self, config: ConfigManager, audit_logger=None, agent_authenticator=None):
        self.config = config
        self.audit_logger = audit_logger
        self.agent_authenticator = agent_authenticator
        
        # AWS services
        self.dynamodb = boto3.resource('dynamodb', region_name=config.aws.region)
        self.sns = boto3.client('sns', region_name=config.aws.region)
        
        # Storage configuration
        self.alerts_table_name = config.get('security_alerts_table', 'incident-commander-security-alerts')
        self.threat_intel_table_name = config.get('threat_intel_table', 'incident-commander-threat-intel')
        self.security_topic_arn = config.get('security_topic_arn')
        
        # Behavioral analysis configuration
        self.behavior_window_minutes = config.get('behavior_window_minutes', 60)
        self.max_failed_auth_attempts = config.get('max_failed_auth_attempts', 5)
        self.max_privilege_escalations = config.get('max_privilege_escalations', 3)
        self.suspicious_action_threshold = config.get('suspicious_action_threshold', 10)
        
        # In-memory tracking for behavioral analysis
        self._agent_behaviors: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._failed_auth_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self._privilege_escalations: Dict[str, List[datetime]] = defaultdict(list)
        self._suspicious_patterns: Dict[str, int] = defaultdict(int)
        
        # Threat intelligence cache
        self._threat_intel_cache: Dict[str, ThreatIntelligence] = {}
        self._threat_intel_updated: Optional[datetime] = None
        
        # Active alerts tracking
        self._active_alerts: Dict[str, SecurityAlert] = {}
        
        # Security metrics
        self._metrics = SecurityMetrics()
        self._metrics_last_updated = datetime.utcnow()
    
    async def analyze_security_event(self, audit_event: AuditEvent) -> List[SecurityAlert]:
        """
        Analyze a security event for threats and suspicious behavior.
        
        Args:
            audit_event: Audit event to analyze
            
        Returns:
            List[SecurityAlert]: Generated security alerts
        """
        alerts = []
        
        try:
            with threat_detection_duration.time():
                # Update metrics
                security_events_total.labels(
                    event_type=audit_event.event_type,
                    severity=audit_event.severity
                ).inc()
                
                # Behavioral analysis
                behavioral_alerts = await self._analyze_agent_behavior(audit_event)
                alerts.extend(behavioral_alerts)
                
                # Pattern-based detection
                pattern_alerts = await self._detect_suspicious_patterns(audit_event)
                alerts.extend(pattern_alerts)
                
                # Threat intelligence correlation
                intel_alerts = await self._correlate_threat_intelligence(audit_event)
                alerts.extend(intel_alerts)
                
                # Authentication analysis
                auth_alerts = await self._analyze_authentication_events(audit_event)
                alerts.extend(auth_alerts)
                
                # Store and process alerts
                for alert in alerts:
                    await self._store_security_alert(alert)
                    await self._trigger_automated_response(alert)
                    
                    security_alerts_total.labels(
                        alert_type=alert.alert_type,
                        severity=alert.severity
                    ).inc()
                
                # Update behavioral tracking
                await self._update_behavioral_tracking(audit_event)
                
                if alerts:
                    await logger.ainfo(
                        "Security analysis completed",
                        event_id=audit_event.event_id,
                        alerts_generated=len(alerts)
                    )
                
                return alerts
                
        except Exception as e:
            await logger.aerror(
                "Security event analysis failed",
                event_id=audit_event.event_id,
                error=str(e)
            )
            raise SecurityError(f"Security analysis failed: {e}")
    
    async def detect_agent_compromise(self, agent_id: str) -> Optional[SecurityAlert]:
        """
        Detect potential agent compromise based on behavioral patterns.
        
        Args:
            agent_id: Agent identifier to analyze
            
        Returns:
            SecurityAlert: Compromise alert if detected
        """
        try:
            # Get recent agent behaviors
            recent_behaviors = list(self._agent_behaviors[agent_id])
            if len(recent_behaviors) < 10:  # Need sufficient data
                return None
            
            # Analyze behavior patterns
            compromise_indicators = []
            
            # Check for unusual activity patterns
            if await self._detect_unusual_activity_pattern(agent_id, recent_behaviors):
                compromise_indicators.append("unusual_activity_pattern")
            
            # Check for privilege escalation attempts
            if await self._detect_privilege_escalation_pattern(agent_id):
                compromise_indicators.append("privilege_escalation_attempts")
            
            # Check for authentication anomalies
            if await self._detect_authentication_anomalies(agent_id):
                compromise_indicators.append("authentication_anomalies")
            
            # Check for data access anomalies
            if await self._detect_data_access_anomalies(agent_id, recent_behaviors):
                compromise_indicators.append("data_access_anomalies")
            
            # Generate alert if multiple indicators present
            if len(compromise_indicators) >= 2:
                alert = SecurityAlert(
                    alert_id=str(uuid4()),
                    alert_type="agent_compromise",
                    severity=SecuritySeverity.CRITICAL,
                    agent_id=agent_id,
                    description=f"Potential agent compromise detected for {agent_id}",
                    indicators=compromise_indicators,
                    confidence_score=min(1.0, len(compromise_indicators) * 0.3),
                    mitigation_actions=[
                        "revoke_agent_certificate",
                        "quarantine_agent",
                        "investigate_recent_actions",
                        "notify_security_team"
                    ]
                )
                
                agent_compromise_attempts.inc()
                
                await logger.acritical(
                    "Agent compromise detected",
                    agent_id=agent_id,
                    indicators=compromise_indicators,
                    confidence=alert.confidence_score
                )
                
                return alert
            
            return None
            
        except Exception as e:
            await logger.aerror(
                "Agent compromise detection failed",
                agent_id=agent_id,
                error=str(e)
            )
            return None
    
    async def correlate_security_events(
        self,
        time_window_minutes: int = 30
    ) -> List[SecurityAlert]:
        """
        Correlate security events to detect coordinated attacks.
        
        Args:
            time_window_minutes: Time window for correlation
            
        Returns:
            List[SecurityAlert]: Correlated attack alerts
        """
        try:
            # Get recent security events
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
            recent_events = await self._get_recent_security_events(cutoff_time)
            
            if len(recent_events) < 5:  # Need sufficient events for correlation
                return []
            
            alerts = []
            
            # Detect coordinated authentication attacks
            auth_attack_alert = await self._detect_coordinated_auth_attack(recent_events)
            if auth_attack_alert:
                alerts.append(auth_attack_alert)
            
            # Detect privilege escalation campaigns
            privilege_campaign_alert = await self._detect_privilege_escalation_campaign(recent_events)
            if privilege_campaign_alert:
                alerts.append(privilege_campaign_alert)
            
            # Detect data exfiltration patterns
            exfiltration_alert = await self._detect_data_exfiltration_pattern(recent_events)
            if exfiltration_alert:
                alerts.append(exfiltration_alert)
            
            # Detect distributed attacks
            distributed_attack_alert = await self._detect_distributed_attack(recent_events)
            if distributed_attack_alert:
                alerts.append(distributed_attack_alert)
            
            if alerts:
                await logger.ainfo(
                    "Security event correlation completed",
                    time_window_minutes=time_window_minutes,
                    events_analyzed=len(recent_events),
                    alerts_generated=len(alerts)
                )
            
            return alerts
            
        except Exception as e:
            await logger.aerror(
                "Security event correlation failed",
                error=str(e)
            )
            return []
    
    async def update_threat_intelligence(
        self,
        indicators: List[ThreatIntelligence]
    ) -> int:
        """
        Update threat intelligence database.
        
        Args:
            indicators: List of threat intelligence indicators
            
        Returns:
            int: Number of indicators updated
        """
        try:
            updated_count = 0
            
            for indicator in indicators:
                # Store in database
                await self._store_threat_intelligence(indicator)
                
                # Update cache
                self._threat_intel_cache[indicator.indicator_value] = indicator
                updated_count += 1
            
            self._threat_intel_updated = datetime.utcnow()
            
            await logger.ainfo(
                "Threat intelligence updated",
                indicators_updated=updated_count
            )
            
            return updated_count
            
        except Exception as e:
            await logger.aerror(
                "Threat intelligence update failed",
                error=str(e)
            )
            return 0
    
    async def get_security_metrics(self) -> SecurityMetrics:
        """
        Get current security metrics.
        
        Returns:
            SecurityMetrics: Current security metrics
        """
        try:
            # Update metrics if stale
            if datetime.utcnow() - self._metrics_last_updated > timedelta(minutes=5):
                await self._update_security_metrics()
            
            return self._metrics
            
        except Exception as e:
            await logger.aerror("Failed to get security metrics", error=str(e))
            return SecurityMetrics()  # Return empty metrics on error
    
    async def quarantine_agent(self, agent_id: str, reason: str) -> bool:
        """
        Quarantine a compromised agent.
        
        Args:
            agent_id: Agent to quarantine
            reason: Quarantine reason
            
        Returns:
            bool: True if quarantine successful
        """
        try:
            # Revoke agent certificate
            if self.agent_authenticator:
                await self.agent_authenticator.revoke_certificate(agent_id, reason)
            
            # Log quarantine action
            if self.audit_logger:
                await self.audit_logger.log_security_event(
                    event_type=SecurityEventType.SECURITY_VIOLATION,
                    severity=SecuritySeverity.CRITICAL,
                    action="quarantine_agent",
                    outcome="success",
                    agent_id=agent_id,
                    details={"reason": reason}
                )
            
            # Notify security team
            await self._notify_security_team(
                f"Agent {agent_id} has been quarantined",
                f"Reason: {reason}",
                SecuritySeverity.CRITICAL
            )
            
            automated_responses_triggered.inc()
            
            await logger.acritical(
                "Agent quarantined",
                agent_id=agent_id,
                reason=reason
            )
            
            return True
            
        except Exception as e:
            await logger.aerror(
                "Agent quarantine failed",
                agent_id=agent_id,
                error=str(e)
            )
            return False
    
    # Private helper methods
    
    async def _analyze_agent_behavior(self, event: AuditEvent) -> List[SecurityAlert]:
        """Analyze agent behavior for anomalies."""
        alerts = []
        
        if not event.agent_id:
            return alerts
        
        # Check for rapid successive actions (potential automation/compromise)
        recent_actions = [
            b for b in self._agent_behaviors[event.agent_id]
            if datetime.utcnow() - b['timestamp'] < timedelta(minutes=5)
        ]
        
        if len(recent_actions) > 20:  # More than 20 actions in 5 minutes
            alert = SecurityAlert(
                alert_id=str(uuid4()),
                alert_type="rapid_actions",
                severity=SecuritySeverity.MEDIUM,
                agent_id=event.agent_id,
                description=f"Agent {event.agent_id} performing unusually rapid actions",
                indicators=["high_action_frequency"],
                confidence_score=0.7,
                mitigation_actions=["monitor_agent", "rate_limit_actions"]
            )
            alerts.append(alert)
            suspicious_behaviors_detected.inc()
        
        return alerts
    
    async def _detect_suspicious_patterns(self, event: AuditEvent) -> List[SecurityAlert]:
        """Detect suspicious patterns in security events."""
        alerts = []
        
        # Check for privilege escalation attempts
        if event.event_type == SecurityEventType.PRIVILEGE_ESCALATION:
            if event.agent_id:
                escalations = self._privilege_escalations[event.agent_id]
                escalations.append(datetime.utcnow())
                
                # Remove old escalations
                cutoff = datetime.utcnow() - timedelta(hours=1)
                escalations[:] = [t for t in escalations if t > cutoff]
                
                if len(escalations) > self.max_privilege_escalations:
                    alert = SecurityAlert(
                        alert_id=str(uuid4()),
                        alert_type="privilege_escalation_pattern",
                        severity=SecuritySeverity.HIGH,
                        agent_id=event.agent_id,
                        description=f"Multiple privilege escalation attempts by {event.agent_id}",
                        indicators=["repeated_privilege_escalation"],
                        confidence_score=0.8,
                        mitigation_actions=["investigate_agent", "restrict_permissions"]
                    )
                    alerts.append(alert)
        
        return alerts
    
    async def _correlate_threat_intelligence(self, event: AuditEvent) -> List[SecurityAlert]:
        """Correlate event with threat intelligence."""
        alerts = []
        
        # Check source IP against threat intelligence
        if event.source_ip and event.source_ip in self._threat_intel_cache:
            threat_info = self._threat_intel_cache[event.source_ip]
            
            alert = SecurityAlert(
                alert_id=str(uuid4()),
                alert_type="threat_intelligence_match",
                severity=SecuritySeverity.HIGH,
                agent_id=event.agent_id,
                description=f"Activity from known malicious IP: {event.source_ip}",
                indicators=[f"malicious_ip_{threat_info.threat_type}"],
                confidence_score=threat_info.confidence,
                mitigation_actions=["block_ip", "investigate_activity"]
            )
            alerts.append(alert)
        
        return alerts
    
    async def _analyze_authentication_events(self, event: AuditEvent) -> List[SecurityAlert]:
        """Analyze authentication events for anomalies."""
        alerts = []
        
        if event.event_type == SecurityEventType.AGENT_AUTHENTICATION and event.outcome == "failure":
            if event.agent_id:
                failures = self._failed_auth_attempts[event.agent_id]
                failures.append(datetime.utcnow())
                
                # Remove old failures
                cutoff = datetime.utcnow() - timedelta(hours=1)
                failures[:] = [t for t in failures if t > cutoff]
                
                if len(failures) > self.max_failed_auth_attempts:
                    alert = SecurityAlert(
                        alert_id=str(uuid4()),
                        alert_type="authentication_brute_force",
                        severity=SecuritySeverity.HIGH,
                        agent_id=event.agent_id,
                        description=f"Multiple authentication failures for {event.agent_id}",
                        indicators=["repeated_auth_failures"],
                        confidence_score=0.9,
                        mitigation_actions=["lock_agent", "investigate_source"]
                    )
                    alerts.append(alert)
        
        return alerts
    
    async def _update_behavioral_tracking(self, event: AuditEvent) -> None:
        """Update behavioral tracking data."""
        if event.agent_id:
            behavior_entry = {
                'timestamp': event.timestamp,
                'event_type': event.event_type,
                'action': event.action,
                'outcome': event.outcome,
                'source_ip': event.source_ip
            }
            self._agent_behaviors[event.agent_id].append(behavior_entry)
    
    async def _trigger_automated_response(self, alert: SecurityAlert) -> None:
        """Trigger automated response to security alert."""
        try:
            if alert.severity == SecuritySeverity.CRITICAL:
                # Critical alerts trigger immediate response
                if "quarantine_agent" in alert.mitigation_actions and alert.agent_id:
                    await self.quarantine_agent(alert.agent_id, alert.description)
                
                # Notify security team immediately
                await self._notify_security_team(
                    f"CRITICAL SECURITY ALERT: {alert.alert_type}",
                    alert.description,
                    alert.severity
                )
            
            elif alert.severity == SecuritySeverity.HIGH:
                # High severity alerts get escalated
                await self._notify_security_team(
                    f"HIGH SECURITY ALERT: {alert.alert_type}",
                    alert.description,
                    alert.severity
                )
            
            automated_responses_triggered.inc()
            
        except Exception as e:
            await logger.aerror(
                "Automated response failed",
                alert_id=alert.alert_id,
                error=str(e)
            )
    
    async def _notify_security_team(
        self,
        subject: str,
        message: str,
        severity: SecuritySeverity
    ) -> None:
        """Notify security team of alerts."""
        if not self.security_topic_arn:
            return
        
        try:
            notification = {
                'subject': subject,
                'message': message,
                'severity': severity,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await asyncio.to_thread(
                self.sns.publish,
                TopicArn=self.security_topic_arn,
                Subject=subject,
                Message=json.dumps(notification, indent=2)
            )
            
        except Exception as e:
            await logger.aerror(
                "Security team notification failed",
                error=str(e)
            )
    
    async def _store_security_alert(self, alert: SecurityAlert) -> None:
        """Store security alert in DynamoDB."""
        table = self.dynamodb.Table(self.alerts_table_name)
        
        item = {
            'alert_id': alert.alert_id,
            'timestamp': alert.timestamp.isoformat(),
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'agent_id': alert.agent_id,
            'description': alert.description,
            'indicators': alert.indicators,
            'confidence_score': alert.confidence_score,
            'mitigation_actions': alert.mitigation_actions,
            'status': alert.status,
            'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
            'resolution_notes': alert.resolution_notes
        }
        
        # Remove None values
        item = {k: v for k, v in item.items() if v is not None}
        
        await asyncio.to_thread(table.put_item, Item=item)
        
        # Track active alerts
        self._active_alerts[alert.alert_id] = alert
    
    async def _store_threat_intelligence(self, indicator: ThreatIntelligence) -> None:
        """Store threat intelligence in DynamoDB."""
        table = self.dynamodb.Table(self.threat_intel_table_name)
        
        item = {
            'indicator_id': indicator.indicator_id,
            'indicator_type': indicator.indicator_type,
            'indicator_value': indicator.indicator_value,
            'threat_type': indicator.threat_type,
            'confidence': indicator.confidence,
            'source': indicator.source,
            'first_seen': indicator.first_seen.isoformat(),
            'last_seen': indicator.last_seen.isoformat(),
            'tags': indicator.tags,
            'description': indicator.description
        }
        
        # Remove None values
        item = {k: v for k, v in item.items() if v is not None}
        
        await asyncio.to_thread(table.put_item, Item=item)
    
    async def _update_security_metrics(self) -> None:
        """Update security metrics."""
        try:
            # Count active alerts by severity
            alerts_by_severity = defaultdict(int)
            for alert in self._active_alerts.values():
                if alert.status == "open":
                    alerts_by_severity[alert.severity] += 1
            
            # Update metrics
            self._metrics = SecurityMetrics(
                security_events_by_severity=dict(alerts_by_severity),
                security_alerts_open=len([a for a in self._active_alerts.values() if a.status == "open"]),
                security_alerts_resolved=len([a for a in self._active_alerts.values() if a.status == "resolved"]),
                suspicious_behaviors_detected=int(suspicious_behaviors_detected._value.get()),
                potential_compromises_detected=int(agent_compromise_attempts._value.get()),
                automated_responses_triggered=int(automated_responses_triggered._value.get())
            )
            
            self._metrics_last_updated = datetime.utcnow()
            
        except Exception as e:
            await logger.aerror("Failed to update security metrics", error=str(e))
    
    # Additional detection methods would be implemented here
    async def _detect_unusual_activity_pattern(self, agent_id: str, behaviors: List[Dict]) -> bool:
        """Detect unusual activity patterns."""
        # Simplified implementation - in production, this would use ML models
        return False
    
    async def _detect_privilege_escalation_pattern(self, agent_id: str) -> bool:
        """Detect privilege escalation patterns."""
        escalations = self._privilege_escalations[agent_id]
        return len(escalations) > self.max_privilege_escalations
    
    async def _detect_authentication_anomalies(self, agent_id: str) -> bool:
        """Detect authentication anomalies."""
        failures = self._failed_auth_attempts[agent_id]
        return len(failures) > self.max_failed_auth_attempts
    
    async def _detect_data_access_anomalies(self, agent_id: str, behaviors: List[Dict]) -> bool:
        """Detect data access anomalies."""
        # Simplified implementation
        data_access_events = [b for b in behaviors if 'data_access' in b.get('action', '')]
        return len(data_access_events) > 50  # Threshold for unusual data access
    
    async def _get_recent_security_events(self, cutoff_time: datetime) -> List[AuditEvent]:
        """Get recent security events for correlation."""
        # This would query the audit log table in production
        return []
    
    async def _detect_coordinated_auth_attack(self, events: List[AuditEvent]) -> Optional[SecurityAlert]:
        """Detect coordinated authentication attacks."""
        # Implementation would analyze patterns across multiple agents
        return None
    
    async def _detect_privilege_escalation_campaign(self, events: List[AuditEvent]) -> Optional[SecurityAlert]:
        """Detect privilege escalation campaigns."""
        return None
    
    async def _detect_data_exfiltration_pattern(self, events: List[AuditEvent]) -> Optional[SecurityAlert]:
        """Detect data exfiltration patterns."""
        return None
    
    async def _detect_distributed_attack(self, events: List[AuditEvent]) -> Optional[SecurityAlert]:
        """Detect distributed attacks."""
        return None