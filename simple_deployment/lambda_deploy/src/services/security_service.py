"""
Security Service Integration

Provides security event logging, agent authentication, and audit trail
functionality that integrates with the existing agent communication system.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import uuid4

from src.models.security import (
    SecurityEventType,
    SecuritySeverity,
    AuditEvent,
    SecurityAlert,
    AgentCertificate,
    SecurityMetrics,
    ThreatIntelligence
)
from src.models.agent import AgentMessage, AgentType, AgentRecommendation
from src.utils.logging import get_logger


logger = get_logger("security_service")


class SecurityService:
    """
    Security service for agent authentication, audit logging, and threat detection.
    
    Integrates with existing agent communication models to provide comprehensive
    security monitoring and compliance capabilities.
    """
    
    def __init__(self):
        self.audit_events: List[AuditEvent] = []
        self.security_alerts: List[SecurityAlert] = []
        self.agent_certificates: Dict[str, AgentCertificate] = {}
        self.threat_intelligence: Dict[str, ThreatIntelligence] = {}
        self.security_metrics = SecurityMetrics()
        
    async def log_agent_authentication(
        self, 
        agent_id: str, 
        agent_type: AgentType,
        outcome: str,
        authentication_method: str = "certificate",
        source_ip: Optional[str] = None
    ) -> AuditEvent:
        """Log agent authentication event."""
        event = AuditEvent(
            event_id=f"auth_{agent_id}_{int(datetime.utcnow().timestamp())}",
            event_type=SecurityEventType.AGENT_AUTHENTICATION,
            severity=SecuritySeverity.LOW if outcome == "success" else SecuritySeverity.MEDIUM,
            agent_id=agent_id,
            source_ip=source_ip,
            action="authenticate",
            outcome=outcome,
            details={
                "agent_type": agent_type.value,
                "authentication_method": authentication_method,
                "session_duration": 3600
            }
        )
        
        self.audit_events.append(event)
        
        # Update security metrics
        if outcome == "success":
            self.security_metrics.successful_authentications += 1
        else:
            self.security_metrics.failed_authentications += 1
        
        logger.info(f"Agent authentication logged: {agent_id} - {outcome}")
        return event
    
    async def log_agent_message(
        self, 
        message: AgentMessage,
        outcome: str = "success"
    ) -> AuditEvent:
        """Log agent communication event."""
        event = AuditEvent(
            event_id=f"msg_{message.id}",
            event_type=SecurityEventType.AGENT_AUTHORIZATION,
            severity=SecuritySeverity.LOW,
            agent_id=f"{message.sender_agent}_agent",
            action="send_message",
            outcome=outcome,
            details={
                "message_type": message.message_type,
                "recipient_agent": message.recipient_agent if message.recipient_agent else "broadcast",
                "correlation_id": message.correlation_id,
                "payload_size": len(str(message.payload))
            }
        )
        
        self.audit_events.append(event)
        return event
    
    async def log_agent_recommendation(
        self, 
        recommendation: AgentRecommendation,
        outcome: str = "created"
    ) -> AuditEvent:
        """Log agent recommendation event."""
        event = AuditEvent(
            event_id=f"rec_{recommendation.id}",
            event_type=SecurityEventType.DATA_ACCESS,
            severity=SecuritySeverity.MEDIUM if recommendation.risk_level == "high" else SecuritySeverity.LOW,
            agent_id=f"{recommendation.agent_name}_agent",
            action="create_recommendation",
            outcome=outcome,
            details={
                "incident_id": recommendation.incident_id,
                "action_type": recommendation.action_type,
                "confidence": recommendation.confidence,
                "risk_level": recommendation.risk_level,
                "evidence_count": len(recommendation.evidence)
            }
        )
        
        self.audit_events.append(event)
        return event
    
    async def detect_agent_anomaly(
        self, 
        agent_id: str,
        anomaly_indicators: List[str],
        confidence_score: float
    ) -> Optional[SecurityAlert]:
        """Detect and create security alert for agent anomalies."""
        if confidence_score < 0.7:
            return None
        
        alert = SecurityAlert(
            alert_id=f"anomaly_{agent_id}_{int(datetime.utcnow().timestamp())}",
            alert_type="agent_behavioral_anomaly",
            severity=SecuritySeverity.HIGH if confidence_score > 0.9 else SecuritySeverity.MEDIUM,
            agent_id=agent_id,
            description=f"Agent {agent_id} exhibiting anomalous behavior patterns",
            indicators=anomaly_indicators,
            confidence_score=confidence_score,
            mitigation_actions=[
                "quarantine_agent",
                "rollback_to_previous_version",
                "notify_security_team"
            ]
        )
        
        self.security_alerts.append(alert)
        
        # Update security metrics
        self.security_metrics.suspicious_behaviors_detected += 1
        if confidence_score > 0.9:
            self.security_metrics.potential_compromises_detected += 1
        
        logger.warning(f"Agent anomaly detected: {agent_id} - confidence: {confidence_score}")
        return alert
    
    async def issue_agent_certificate(
        self, 
        agent_id: str,
        public_key: str,
        validity_days: int = 90
    ) -> AgentCertificate:
        """Issue new certificate for agent authentication."""
        certificate = AgentCertificate(
            agent_id=agent_id,
            certificate_id=f"cert_{agent_id}_{int(datetime.utcnow().timestamp())}_{str(uuid4())[:8]}",
            public_key=public_key,
            expires_at=datetime.utcnow() + timedelta(days=validity_days)
        )
        
        self.agent_certificates[agent_id] = certificate
        
        # Log certificate issuance
        await self.log_security_event(
            SecurityEventType.CONFIGURATION_CHANGE,
            SecuritySeverity.LOW,
            agent_id=agent_id,
            action="issue_certificate",
            outcome="success",
            details={
                "certificate_id": certificate.certificate_id,
                "validity_days": validity_days,
                "expires_at": certificate.expires_at.isoformat()
            }
        )
        
        # Update security metrics
        self.security_metrics.active_agent_certificates += 1
        
        logger.info(f"Certificate issued for agent: {agent_id}")
        return certificate
    
    async def validate_agent_certificate(
        self, 
        agent_id: str
    ) -> bool:
        """Validate agent certificate for authentication."""
        certificate = self.agent_certificates.get(agent_id)
        
        if not certificate:
            await self.log_security_event(
                SecurityEventType.AGENT_AUTHENTICATION,
                SecuritySeverity.MEDIUM,
                agent_id=agent_id,
                action="validate_certificate",
                outcome="failed",
                details={"reason": "certificate_not_found"}
            )
            return False
        
        is_valid = certificate.is_valid()
        
        await self.log_security_event(
            SecurityEventType.AGENT_AUTHENTICATION,
            SecuritySeverity.LOW if is_valid else SecuritySeverity.MEDIUM,
            agent_id=agent_id,
            action="validate_certificate",
            outcome="success" if is_valid else "failed",
            details={
                "certificate_id": certificate.certificate_id,
                "is_expired": certificate.is_expired(),
                "days_until_expiry": certificate.days_until_expiry()
            }
        )
        
        return is_valid
    
    async def log_security_event(
        self,
        event_type: SecurityEventType,
        severity: SecuritySeverity,
        action: str,
        outcome: str,
        agent_id: Optional[str] = None,
        user_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Log generic security event."""
        event = AuditEvent(
            event_id=f"sec_{int(datetime.utcnow().timestamp())}_{str(uuid4())[:8]}",
            event_type=event_type,
            severity=severity,
            agent_id=agent_id,
            user_id=user_id,
            source_ip=source_ip,
            resource=resource,
            action=action,
            outcome=outcome,
            details=details or {}
        )
        
        self.audit_events.append(event)
        
        # Update security metrics
        self.security_metrics.security_events_total += 1
        if severity.value not in self.security_metrics.security_events_by_severity:
            self.security_metrics.security_events_by_severity[severity.value] = 0
        self.security_metrics.security_events_by_severity[severity.value] += 1
        
        return event
    
    async def get_security_metrics(self) -> SecurityMetrics:
        """Get current security metrics."""
        # Update timestamp
        self.security_metrics.timestamp = datetime.utcnow()
        
        # Calculate authentication rate
        total_auth = (self.security_metrics.successful_authentications + 
                     self.security_metrics.failed_authentications)
        if total_auth > 0:
            self.security_metrics.authentication_rate = (
                self.security_metrics.successful_authentications / total_auth * 100
            )
        
        # Count active certificates
        active_certs = sum(1 for cert in self.agent_certificates.values() if cert.is_valid())
        expired_certs = sum(1 for cert in self.agent_certificates.values() if cert.is_expired())
        
        self.security_metrics.active_agent_certificates = active_certs
        self.security_metrics.expired_certificates = expired_certs
        
        # Count open/resolved alerts
        open_alerts = sum(1 for alert in self.security_alerts if alert.status == "open")
        resolved_alerts = sum(1 for alert in self.security_alerts if alert.status == "resolved")
        
        self.security_metrics.security_alerts_open = open_alerts
        self.security_metrics.security_alerts_resolved = resolved_alerts
        
        # Count recent audit events
        recent_time = datetime.utcnow() - timedelta(hours=24)
        recent_events = sum(1 for event in self.audit_events if event.timestamp > recent_time)
        self.security_metrics.audit_events_last_24h = recent_events
        
        return self.security_metrics
    
    async def get_audit_trail(
        self, 
        agent_id: Optional[str] = None,
        event_type: Optional[SecurityEventType] = None,
        hours: int = 24
    ) -> List[AuditEvent]:
        """Get audit trail with optional filtering."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        filtered_events = []
        for event in self.audit_events:
            if event.timestamp < cutoff_time:
                continue
            
            if agent_id and event.agent_id != agent_id:
                continue
            
            if event_type and event.event_type != event_type:
                continue
            
            filtered_events.append(event)
        
        # Sort by timestamp (newest first)
        filtered_events.sort(key=lambda e: e.timestamp, reverse=True)
        return filtered_events
    
    async def cleanup_expired_data(self):
        """Clean up expired certificates and old audit events."""
        # Remove expired certificates
        expired_agents = []
        for agent_id, cert in self.agent_certificates.items():
            if cert.is_expired():
                expired_agents.append(agent_id)
        
        for agent_id in expired_agents:
            del self.agent_certificates[agent_id]
            logger.info(f"Removed expired certificate for agent: {agent_id}")
        
        # Archive old audit events (keep last 30 days)
        cutoff_time = datetime.utcnow() - timedelta(days=30)
        self.audit_events = [
            event for event in self.audit_events 
            if event.timestamp > cutoff_time
        ]
        
        # Archive old security alerts (keep last 90 days)
        cutoff_time = datetime.utcnow() - timedelta(days=90)
        self.security_alerts = [
            alert for alert in self.security_alerts 
            if alert.timestamp > cutoff_time
        ]


# Global security service instance
_security_service = None


def get_security_service() -> SecurityService:
    """Get the global security service instance."""
    global _security_service
    if _security_service is None:
        _security_service = SecurityService()
    return _security_service