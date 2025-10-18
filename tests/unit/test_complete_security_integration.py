"""
Complete security integration test covering all security models and services.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from src.services.security_service import SecurityService
from src.services.security_error_integration import SecurityAwareErrorHandler
from src.models.security import SecurityEventType, SecuritySeverity
from src.models.agent import AgentType, AgentMessage, AgentRecommendation, ActionType, RiskLevel
from src.services.error_handling_recovery import ErrorHandlingRecoverySystem


class TestCompleteSecurityIntegration:
    """Test complete security integration across all components."""
    
    @pytest.fixture
    def security_service(self):
        """Create security service for testing."""
        return SecurityService()
    
    @pytest.fixture
    def security_error_handler(self):
        """Create security-aware error handler for testing."""
        return SecurityAwareErrorHandler()
    
    @pytest.mark.asyncio
    async def test_end_to_end_security_workflow(self, security_service):
        """Test complete end-to-end security workflow."""
        # 1. Agent authentication
        auth_event = await security_service.log_agent_authentication(
            agent_id="detection_agent_001",
            agent_type=AgentType.DETECTION,
            outcome="success"
        )
        assert auth_event.verify_integrity() is True
        
        # 2. Issue certificate
        certificate = await security_service.issue_agent_certificate(
            agent_id="detection_agent_001",
            public_key="test_public_key"
        )
        assert certificate.is_valid() is True
        
        # 3. Validate certificate
        is_valid = await security_service.validate_agent_certificate("detection_agent_001")
        assert is_valid is True
        
        # 4. Log agent message
        message = AgentMessage(
            sender_agent=AgentType.DETECTION,
            recipient_agent=AgentType.DIAGNOSIS,
            message_type="incident_detected",
            payload={"incident_id": "inc_123"},
            correlation_id="corr_456"
        )
        message_event = await security_service.log_agent_message(message)
        assert message_event.verify_integrity() is True
        
        # 5. Detect anomaly
        alert = await security_service.detect_agent_anomaly(
            agent_id="detection_agent_001",
            anomaly_indicators=["unusual_behavior"],
            confidence_score=0.85
        )
        assert alert is not None
        
        # 6. Get comprehensive metrics
        metrics = await security_service.get_security_metrics()
        assert metrics.successful_authentications == 1
        assert metrics.active_agent_certificates == 1
        assert metrics.suspicious_behaviors_detected == 1
        assert metrics.security_events_total > 0
        
        # 7. Get audit trail
        audit_trail = await security_service.get_audit_trail()
        assert len(audit_trail) >= 4  # Auth, cert issue, cert validation, message
        
        # Verify all events have integrity
        for event in audit_trail:
            assert event.verify_integrity() is True
    
    @pytest.mark.asyncio
    async def test_security_error_integration(self, security_error_handler):
        """Test security integration with error handling system."""
        # Simulate agent timeout error
        timeout_error = asyncio.TimeoutError("Agent timeout")
        
        # Handle error with security logging
        result = await security_error_handler.handle_error_with_security_logging(
            error=timeout_error,
            component="detection_agent",
            agent_id="detection_agent_001",
            correlation_id="test_corr_123"
        )
        
        # Verify error was handled
        assert "error_id" in result
        assert result["severity"] in ["low", "medium", "high", "critical"]
        
        # Verify security events were logged
        security_metrics = await security_error_handler.security_service.get_security_metrics()
        assert security_metrics.security_events_total > 0
        
        # Get integrated metrics
        integrated_metrics = await security_error_handler.get_security_error_metrics()
        assert "security_metrics" in integrated_metrics
        assert "error_metrics" in integrated_metrics
        assert "integrated_metrics" in integrated_metrics
    
    @pytest.mark.asyncio
    async def test_recovery_action_security_validation(self, security_error_handler):
        """Test security validation for recovery actions."""
        agent_id = "test_agent_001"
        
        # Issue certificate for agent
        await security_error_handler.security_service.issue_agent_certificate(
            agent_id=agent_id,
            public_key="test_key"
        )
        
        # Validate high-risk recovery action
        is_valid = await security_error_handler.validate_recovery_action_security(
            recovery_action="agent_restart",
            component="detection_agent",
            agent_id=agent_id
        )
        assert is_valid is True
        
        # Test with invalid agent (no certificate)
        is_invalid = await security_error_handler.validate_recovery_action_security(
            recovery_action="agent_restart",
            component="detection_agent",
            agent_id="invalid_agent"
        )
        assert is_invalid is False
        
        # Log recovery action
        await security_error_handler.log_recovery_action_security(
            recovery_action="agent_restart",
            component="detection_agent",
            outcome="success",
            agent_id=agent_id
        )
        
        # Verify security events were logged
        audit_trail = await security_error_handler.security_service.get_audit_trail()
        recovery_events = [
            event for event in audit_trail 
            if "recovery_" in event.action
        ]
        assert len(recovery_events) > 0
    
    @pytest.mark.asyncio
    async def test_security_metrics_correlation(self, security_error_handler):
        """Test correlation between security events and system errors."""
        # Generate some errors and security events
        for i in range(3):
            await security_error_handler.handle_error_with_security_logging(
                error=ValueError(f"Test error {i}"),
                component=f"test_component_{i}",
                agent_id=f"agent_{i}"
            )
        
        # Generate some security events
        for i in range(2):
            await security_error_handler.security_service.detect_agent_anomaly(
                agent_id=f"agent_{i}",
                anomaly_indicators=["test_anomaly"],
                confidence_score=0.8
            )
        
        # Get integrated metrics
        metrics = await security_error_handler.get_security_error_metrics()
        
        # Verify metrics structure
        assert "security_metrics" in metrics
        assert "error_metrics" in metrics
        assert "integrated_metrics" in metrics
        
        # Verify correlation calculation
        correlation = metrics["integrated_metrics"]["security_error_correlation"]
        assert 0.0 <= correlation <= 1.0
        
        # Verify risk assessment
        risk = metrics["integrated_metrics"]["risk_assessment"]
        assert risk in ["low", "medium", "high"]
    
    @pytest.mark.asyncio
    async def test_security_event_integrity_across_services(self, security_service):
        """Test security event integrity across different services."""
        events = []
        
        # Create various types of security events
        events.append(await security_service.log_security_event(
            SecurityEventType.AGENT_AUTHENTICATION,
            SecuritySeverity.LOW,
            "authenticate",
            "success",
            agent_id="test_agent"
        ))
        
        events.append(await security_service.log_security_event(
            SecurityEventType.CONFIGURATION_CHANGE,
            SecuritySeverity.MEDIUM,
            "update_config",
            "success",
            details={"config_key": "security_level", "new_value": "high"}
        ))
        
        events.append(await security_service.log_security_event(
            SecurityEventType.SECURITY_VIOLATION,
            SecuritySeverity.HIGH,
            "unauthorized_access",
            "blocked",
            details={"source_ip": "192.168.1.100", "attempted_resource": "admin_panel"}
        ))
        
        # Verify all events have valid integrity
        for event in events:
            assert event.verify_integrity() is True
            
            # Tamper with event and verify integrity fails
            original_outcome = event.outcome
            event.outcome = "tampered"
            assert event.verify_integrity() is False
            
            # Restore and verify integrity passes
            event.outcome = original_outcome
            assert event.verify_integrity() is True
    
    @pytest.mark.asyncio
    async def test_certificate_lifecycle_security(self, security_service):
        """Test complete certificate lifecycle with security validation."""
        agent_id = "lifecycle_test_agent"
        
        # 1. Issue certificate
        certificate = await security_service.issue_agent_certificate(
            agent_id=agent_id,
            public_key="test_public_key",
            validity_days=30
        )
        
        assert certificate.is_valid() is True
        assert certificate.days_until_expiry() <= 30
        
        # 2. Validate certificate multiple times
        for _ in range(3):
            is_valid = await security_service.validate_agent_certificate(agent_id)
            assert is_valid is True
        
        # 3. Manually expire certificate
        certificate.expires_at = datetime.utcnow() - timedelta(days=1)
        
        # 4. Validation should fail
        is_valid = await security_service.validate_agent_certificate(agent_id)
        assert is_valid is False
        
        # 5. Issue new certificate
        new_certificate = await security_service.issue_agent_certificate(
            agent_id=agent_id,
            public_key="new_public_key",
            validity_days=90
        )
        
        assert new_certificate.is_valid() is True
        assert new_certificate.certificate_id != certificate.certificate_id
        
        # 6. Verify audit trail contains all certificate operations
        audit_trail = await security_service.get_audit_trail(agent_id=agent_id)
        cert_events = [
            event for event in audit_trail 
            if "certificate" in event.action
        ]
        assert len(cert_events) >= 2  # At least 2 certificate operations
    
    @pytest.mark.asyncio
    async def test_threat_intelligence_integration(self, security_service):
        """Test threat intelligence integration with security events."""
        # Add threat intelligence
        threat = {
            "indicator_id": "threat_001",
            "indicator_type": "ip_address",
            "indicator_value": "192.168.1.100",
            "threat_type": "malicious_ip",
            "confidence": 0.9,
            "source": "test_feed"
        }
        
        security_service.threat_intelligence["threat_001"] = threat
        
        # Log security event with matching IP
        event = await security_service.log_security_event(
            SecurityEventType.UNAUTHORIZED_ACCESS,
            SecuritySeverity.HIGH,
            "blocked_access",
            "blocked",
            source_ip="192.168.1.100",
            details={"threat_matched": True, "threat_id": "threat_001"}
        )
        
        assert event.source_ip == "192.168.1.100"
        assert event.details["threat_matched"] is True
        assert event.verify_integrity() is True
    
    @pytest.mark.asyncio
    async def test_compliance_reporting_integration(self, security_service):
        """Test compliance reporting with security events."""
        # Generate various security events for compliance
        events_data = [
            (SecurityEventType.AGENT_AUTHENTICATION, SecuritySeverity.LOW, "authenticate", "success"),
            (SecurityEventType.DATA_ACCESS, SecuritySeverity.MEDIUM, "access_data", "success"),
            (SecurityEventType.CONFIGURATION_CHANGE, SecuritySeverity.MEDIUM, "update_config", "success"),
            (SecurityEventType.SECURITY_VIOLATION, SecuritySeverity.HIGH, "violation_detected", "blocked"),
        ]
        
        for event_type, severity, action, outcome in events_data:
            await security_service.log_security_event(
                event_type, severity, action, outcome
            )
        
        # Get security metrics for compliance
        metrics = await security_service.get_security_metrics()
        
        # Verify compliance-relevant metrics
        assert metrics.security_events_total >= 4
        assert metrics.audit_events_last_24h >= 4
        assert "high" in metrics.security_events_by_severity
        assert metrics.security_events_by_severity["high"] >= 1
        
        # Verify data retention compliance
        assert metrics.data_retention_compliance_rate == 1.0
        
        # Get audit trail for compliance report
        audit_trail = await security_service.get_audit_trail(hours=24)
        assert len(audit_trail) >= 4
        
        # Verify all events are properly logged and have integrity
        for event in audit_trail:
            assert event.verify_integrity() is True
            assert event.timestamp is not None
            assert event.event_type is not None
            assert event.action is not None
            assert event.outcome is not None


class TestSecurityModelValidation:
    """Test security model validation and edge cases."""
    
    def test_audit_event_edge_cases(self):
        """Test audit event edge cases and validation."""
        from src.models.security import AuditEvent
        
        # Test with minimal required fields
        event = AuditEvent(
            event_id="minimal_test",
            event_type=SecurityEventType.AGENT_AUTHENTICATION,
            severity=SecuritySeverity.LOW,
            action="test_action",
            outcome="success"
        )
        
        assert event.verify_integrity() is True
        assert event.agent_id is None
        assert event.user_id is None
        assert len(event.details) == 0
    
    def test_certificate_validation_edge_cases(self):
        """Test certificate validation edge cases."""
        from src.models.security import AgentCertificate
        
        now = datetime.utcnow()
        
        # Test certificate about to expire
        near_expiry_cert = AgentCertificate(
            agent_id="test_agent",
            certificate_id="near_expiry",
            public_key="test_key",
            expires_at=now + timedelta(hours=1)
        )
        
        assert near_expiry_cert.is_valid() is True
        assert near_expiry_cert.days_until_expiry() == 0  # Less than 1 day
        
        # Test revoked certificate
        revoked_cert = AgentCertificate(
            agent_id="test_agent",
            certificate_id="revoked",
            public_key="test_key",
            expires_at=now + timedelta(days=30),
            revoked_at=now - timedelta(hours=1),
            revocation_reason="security_breach"
        )
        
        assert revoked_cert.is_valid() is False
        assert revoked_cert.is_expired() is False  # Not expired, but revoked
    
    def test_security_metrics_edge_cases(self):
        """Test security metrics edge cases."""
        from src.models.security import SecurityMetrics
        
        # Test with all zero values
        metrics = SecurityMetrics()
        
        assert metrics.successful_authentications == 0
        assert metrics.failed_authentications == 0
        assert metrics.authentication_rate == 0.0
        assert metrics.security_events_total == 0
        assert len(metrics.security_events_by_severity) == 0
        
        # Test with maximum values
        max_metrics = SecurityMetrics(
            successful_authentications=999999,
            failed_authentications=0,
            authentication_rate=100.0,
            security_events_total=999999,
            active_agent_certificates=1000,
            pii_redaction_rate=100.0,
            data_retention_compliance_rate=1.0
        )
        
        assert max_metrics.authentication_rate == 100.0
        assert max_metrics.pii_redaction_rate == 100.0
        assert max_metrics.data_retention_compliance_rate == 1.0