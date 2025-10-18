"""
Test security models for validation, serialization, and integration.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from src.models.security import (
    SecurityEventType,
    SecuritySeverity,
    AuditEvent,
    SecurityAlert,
    AgentCertificate,
    ComplianceReport,
    PIIRedactionResult,
    SecurityMetrics,
    ThreatIntelligence
)


class TestAuditEvent:
    """Test AuditEvent model functionality."""
    
    def test_audit_event_creation(self):
        """Test basic audit event creation."""
        event = AuditEvent(
            event_id="test_event_001",
            event_type=SecurityEventType.AGENT_AUTHENTICATION,
            severity=SecuritySeverity.LOW,
            agent_id="detection_agent_001",
            action="authenticate",
            outcome="success"
        )
        
        assert event.event_id == "test_event_001"
        assert event.event_type == SecurityEventType.AGENT_AUTHENTICATION
        assert event.severity == SecuritySeverity.LOW
        assert event.agent_id == "detection_agent_001"
        assert event.action == "authenticate"
        assert event.outcome == "success"
        assert event.integrity_hash is not None
    
    def test_integrity_hash_calculation(self):
        """Test cryptographic integrity hash calculation."""
        event = AuditEvent(
            event_id="test_event_002",
            event_type=SecurityEventType.DATA_ACCESS,
            severity=SecuritySeverity.MEDIUM,
            action="read_incident_data",
            outcome="success",
            details={"incident_id": "inc_123", "data_type": "logs"}
        )
        
        # Hash should be calculated automatically
        assert event.integrity_hash is not None
        assert len(event.integrity_hash) == 64  # SHA-256 hex length
        
        # Verify integrity
        assert event.verify_integrity() is True
    
    def test_integrity_verification_failure(self):
        """Test integrity verification with tampered data."""
        event = AuditEvent(
            event_id="test_event_003",
            event_type=SecurityEventType.SECURITY_VIOLATION,
            severity=SecuritySeverity.HIGH,
            action="unauthorized_access",
            outcome="blocked"
        )
        
        original_hash = event.integrity_hash
        
        # Tamper with the event
        event.outcome = "success"  # Change outcome without recalculating hash
        
        # Verification should fail
        assert event.verify_integrity() is False
        
        # Restore original data
        event.outcome = "blocked"
        event.integrity_hash = original_hash
        assert event.verify_integrity() is True
    
    def test_deterministic_hashing(self):
        """Test that identical events produce identical hashes."""
        # Use fixed timestamp for deterministic hashing
        fixed_timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        event_data = {
            "event_id": "test_event_004",
            "timestamp": fixed_timestamp,
            "event_type": SecurityEventType.CONFIGURATION_CHANGE,
            "severity": SecuritySeverity.MEDIUM,
            "action": "update_config",
            "outcome": "success",
            "details": {"config_key": "rate_limit", "old_value": "100", "new_value": "200"}
        }
        
        event1 = AuditEvent(**event_data)
        event2 = AuditEvent(**event_data)
        
        # Should produce identical hashes
        assert event1.integrity_hash == event2.integrity_hash
    
    def test_serialization_deserialization(self):
        """Test JSON serialization and deserialization."""
        event = AuditEvent(
            event_id="test_event_005",
            event_type=SecurityEventType.AGENT_COMPROMISE,
            severity=SecuritySeverity.CRITICAL,
            agent_id="suspicious_agent_001",
            action="anomalous_behavior",
            outcome="quarantined",
            details={"anomaly_score": 0.95, "behavior_type": "privilege_escalation"}
        )
        
        # Serialize to dict
        event_dict = event.model_dump()
        assert "integrity_hash" in event_dict
        assert event_dict["event_type"] == "agent_compromise"
        
        # Deserialize from dict
        restored_event = AuditEvent(**event_dict)
        assert restored_event.event_id == event.event_id
        assert restored_event.verify_integrity() is True


class TestSecurityAlert:
    """Test SecurityAlert model functionality."""
    
    def test_security_alert_creation(self):
        """Test basic security alert creation."""
        alert = SecurityAlert(
            alert_id="alert_001",
            alert_type="behavioral_anomaly",
            severity=SecuritySeverity.HIGH,
            agent_id="detection_agent_001",
            description="Agent exhibiting unusual API call patterns",
            indicators=["high_api_frequency", "unusual_endpoints"],
            confidence_score=0.85,
            mitigation_actions=["quarantine_agent", "notify_security_team"]
        )
        
        assert alert.alert_id == "alert_001"
        assert alert.severity == SecuritySeverity.HIGH
        assert alert.confidence_score == 0.85
        assert len(alert.indicators) == 2
        assert len(alert.mitigation_actions) == 2
        assert alert.status == "open"
    
    def test_confidence_score_validation(self):
        """Test confidence score validation bounds."""
        # Valid confidence score
        alert = SecurityAlert(
            alert_id="alert_002",
            alert_type="test_alert",
            severity=SecuritySeverity.LOW,
            description="Test alert",
            confidence_score=0.75
        )
        assert alert.confidence_score == 0.75
        
        # Invalid confidence scores should raise validation error
        with pytest.raises(ValueError):
            SecurityAlert(
                alert_id="alert_003",
                alert_type="test_alert",
                severity=SecuritySeverity.LOW,
                description="Test alert",
                confidence_score=1.5  # > 1.0
            )
        
        with pytest.raises(ValueError):
            SecurityAlert(
                alert_id="alert_004",
                alert_type="test_alert",
                severity=SecuritySeverity.LOW,
                description="Test alert",
                confidence_score=-0.1  # < 0.0
            )


class TestAgentCertificate:
    """Test AgentCertificate model functionality."""
    
    def test_certificate_creation(self):
        """Test basic certificate creation."""
        cert = AgentCertificate(
            agent_id="detection_agent_001",
            certificate_id="cert_001",
            public_key="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...\n-----END PUBLIC KEY-----",
            expires_at=datetime.utcnow() + timedelta(days=90)
        )
        
        assert cert.agent_id == "detection_agent_001"
        assert cert.certificate_id == "cert_001"
        assert cert.status == "active"
        assert cert.is_valid() is True
        assert cert.is_expired() is False
    
    def test_certificate_expiration_validation(self):
        """Test certificate expiration validation."""
        now = datetime.utcnow()
        
        # Valid expiration (future date)
        cert = AgentCertificate(
            agent_id="test_agent",
            certificate_id="cert_002",
            public_key="test_key",
            issued_at=now,
            expires_at=now + timedelta(days=30)
        )
        assert cert.is_valid() is True
        
        # Invalid expiration (past date)
        with pytest.raises(ValueError, match="Certificate expiration must be after issuance"):
            AgentCertificate(
                agent_id="test_agent",
                certificate_id="cert_003",
                public_key="test_key",
                issued_at=now,
                expires_at=now - timedelta(days=1)
            )
        
        # Invalid expiration (too far in future)
        with pytest.raises(ValueError, match="Certificate lifetime cannot exceed 1 year"):
            AgentCertificate(
                agent_id="test_agent",
                certificate_id="cert_004",
                public_key="test_key",
                issued_at=now,
                expires_at=now + timedelta(days=400)
            )
    
    def test_certificate_validity_checks(self):
        """Test certificate validity checking methods."""
        now = datetime.utcnow()
        
        # Valid certificate
        cert = AgentCertificate(
            agent_id="test_agent",
            certificate_id="cert_005",
            public_key="test_key",
            issued_at=now - timedelta(days=10),
            expires_at=now + timedelta(days=80)
        )
        
        assert cert.is_valid() is True
        assert cert.is_expired() is False
        # Allow for small timing differences (79-80 days)
        days_left = cert.days_until_expiry()
        assert 79 <= days_left <= 80
        
        # Expired certificate
        expired_cert = AgentCertificate(
            agent_id="test_agent",
            certificate_id="cert_006",
            public_key="test_key",
            issued_at=now - timedelta(days=100),
            expires_at=now - timedelta(days=10)
        )
        
        assert expired_cert.is_valid() is False
        assert expired_cert.is_expired() is True
        assert expired_cert.days_until_expiry() == 0
        
        # Revoked certificate
        revoked_cert = AgentCertificate(
            agent_id="test_agent",
            certificate_id="cert_007",
            public_key="test_key",
            expires_at=now + timedelta(days=30),
            revoked_at=now - timedelta(days=1),
            revocation_reason="security_breach"
        )
        
        assert revoked_cert.is_valid() is False
        assert revoked_cert.is_expired() is False


class TestComplianceReport:
    """Test ComplianceReport model functionality."""
    
    def test_compliance_report_creation(self):
        """Test basic compliance report creation."""
        report = ComplianceReport(
            report_id="compliance_001",
            report_type="SOC2_Type_II",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 12, 31),
            compliance_framework="SOC2",
            total_audit_events=15000,
            security_violations=5,
            findings=[
                {"finding_id": "F001", "severity": "low", "description": "Minor configuration issue"},
                {"finding_id": "F002", "severity": "medium", "description": "Access control improvement needed"}
            ],
            recommendations=[
                "Implement additional access controls",
                "Enhance monitoring for privileged operations"
            ]
        )
        
        assert report.report_id == "compliance_001"
        assert report.compliance_framework == "SOC2"
        assert report.total_audit_events == 15000
        assert report.security_violations == 5
        assert len(report.findings) == 2
        assert len(report.recommendations) == 2
        assert report.status == "draft"


class TestPIIRedactionResult:
    """Test PIIRedactionResult model functionality."""
    
    def test_pii_redaction_result_creation(self):
        """Test basic PII redaction result creation."""
        result = PIIRedactionResult(
            original_text="User john.doe@example.com accessed system from IP 192.168.1.100",
            redacted_text="User [REDACTED_EMAIL] accessed system from IP [REDACTED_IP]",
            redacted_items=[
                {"type": "email", "pattern": "john.doe@example.com"},
                {"type": "ip_address", "pattern": "192.168.1.100"}
            ],
            confidence_score=0.95
        )
        
        assert "john.doe@example.com" not in result.redacted_text
        assert "192.168.1.100" not in result.redacted_text
        assert len(result.redacted_items) == 2
        assert result.confidence_score == 0.95
    
    def test_redacted_items_validation(self):
        """Test validation of redacted items structure."""
        # Valid redacted items
        result = PIIRedactionResult(
            original_text="test",
            redacted_text="test",
            redacted_items=[
                {"type": "email", "pattern": "test@example.com"}
            ],
            confidence_score=0.8
        )
        assert len(result.redacted_items) == 1
        
        # Invalid redacted items (missing required fields)
        with pytest.raises(ValueError, match="Each redacted item must have 'type' and 'pattern' fields"):
            PIIRedactionResult(
                original_text="test",
                redacted_text="test",
                redacted_items=[
                    {"type": "email"}  # Missing 'pattern' field
                ],
                confidence_score=0.8
            )


class TestSecurityMetrics:
    """Test SecurityMetrics model functionality."""
    
    def test_security_metrics_creation(self):
        """Test basic security metrics creation."""
        metrics = SecurityMetrics(
            successful_authentications=1500,
            failed_authentications=25,
            authentication_rate=98.3,
            security_events_total=200,
            security_events_by_severity={
                "low": 150,
                "medium": 35,
                "high": 12,
                "critical": 3
            },
            security_alerts_open=8,
            security_alerts_resolved=45,
            active_agent_certificates=12,
            expired_certificates=2,
            audit_events_last_24h=500,
            pii_redaction_rate=99.8,
            suspicious_behaviors_detected=3,
            potential_compromises_detected=1,
            automated_responses_triggered=15
        )
        
        assert metrics.successful_authentications == 1500
        assert metrics.failed_authentications == 25
        assert metrics.security_events_total == 200
        assert metrics.security_events_by_severity["critical"] == 3
        assert metrics.pii_redaction_rate == 99.8


class TestThreatIntelligence:
    """Test ThreatIntelligence model functionality."""
    
    def test_threat_intelligence_creation(self):
        """Test basic threat intelligence creation."""
        threat = ThreatIntelligence(
            indicator_id="threat_001",
            indicator_type="ip_address",
            indicator_value="192.168.1.100",
            threat_type="malicious_ip",
            confidence=0.85,
            source="threat_feed_alpha",
            tags=["botnet", "ddos", "malware_c2"],
            description="Known malicious IP associated with botnet activity"
        )
        
        assert threat.indicator_id == "threat_001"
        assert threat.indicator_type == "ip_address"
        assert threat.confidence == 0.85
        assert len(threat.tags) == 3
        assert threat.is_stale() is False
    
    def test_threat_intelligence_staleness(self):
        """Test threat intelligence staleness detection."""
        now = datetime.utcnow()
        
        # Fresh threat intelligence
        fresh_threat = ThreatIntelligence(
            indicator_id="threat_002",
            indicator_type="domain",
            indicator_value="malicious.example.com",
            threat_type="malware_domain",
            confidence=0.9,
            source="internal_analysis",
            last_seen=now - timedelta(days=5)
        )
        assert fresh_threat.is_stale() is False
        assert fresh_threat.is_stale(max_age_days=3) is True
        
        # Stale threat intelligence
        stale_threat = ThreatIntelligence(
            indicator_id="threat_003",
            indicator_type="hash",
            indicator_value="abc123def456",
            threat_type="malware_hash",
            confidence=0.95,
            source="external_feed",
            last_seen=now - timedelta(days=45)
        )
        assert stale_threat.is_stale() is True
        assert stale_threat.is_stale(max_age_days=60) is False


class TestSecurityModelIntegration:
    """Test integration between security models and existing agent models."""
    
    def test_audit_event_agent_integration(self):
        """Test audit event creation for agent activities."""
        from src.models.agent import AgentType
        
        # Create audit event for agent authentication
        event = AuditEvent(
            event_id="agent_auth_001",
            event_type=SecurityEventType.AGENT_AUTHENTICATION,
            severity=SecuritySeverity.LOW,
            agent_id="detection_agent_001",
            action="authenticate",
            outcome="success",
            details={
                "agent_type": AgentType.DETECTION.value,
                "authentication_method": "certificate",
                "session_duration": 3600
            }
        )
        
        assert event.details["agent_type"] == "detection"
        assert event.verify_integrity() is True
    
    def test_security_alert_agent_integration(self):
        """Test security alert creation for agent anomalies."""
        from src.models.agent import AgentType
        
        alert = SecurityAlert(
            alert_id="agent_anomaly_001",
            alert_type="agent_behavioral_anomaly",
            severity=SecuritySeverity.HIGH,
            agent_id="diagnosis_agent_002",
            description="Agent showing unusual processing patterns",
            indicators=[
                "processing_time_anomaly",
                "unusual_api_calls",
                "confidence_score_drift"
            ],
            confidence_score=0.78,
            mitigation_actions=[
                "quarantine_agent",
                "rollback_to_previous_version",
                "notify_security_team"
            ]
        )
        
        assert alert.agent_id == "diagnosis_agent_002"
        assert "confidence_score_drift" in alert.indicators
        assert "quarantine_agent" in alert.mitigation_actions
    
    def test_certificate_agent_lifecycle(self):
        """Test certificate lifecycle for agent identity management."""
        from src.models.agent import AgentType
        
        # Create certificate for new agent
        cert = AgentCertificate(
            agent_id="prediction_agent_001",
            certificate_id="cert_pred_001",
            public_key="-----BEGIN PUBLIC KEY-----\ntest_key_data\n-----END PUBLIC KEY-----",
            expires_at=datetime.utcnow() + timedelta(days=90)
        )
        
        # Verify certificate is valid for agent operations
        assert cert.is_valid() is True
        assert cert.agent_id == "prediction_agent_001"
        
        # Simulate certificate renewal before expiry
        days_left = cert.days_until_expiry()
        assert days_left > 0
        
        # Certificate should be renewed when < 30 days remaining
        renewal_needed = days_left < 30
        assert renewal_needed is False  # Should be False for 90-day cert