"""
Tests for Task 14 - Security Hardening and Compliance implementation.

This module tests the security services implemented for Task 14:
- Tamper-proof audit logging
- Agent cryptographic authentication
- Security monitoring and threat detection
- Compliance management and reporting
- Security testing framework
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from src.models.security import (
    AuditEvent, SecurityEventType, SecuritySeverity,
    AgentCertificate, SecurityAlert, ComplianceReport
)
from src.services.security import (
    TamperProofAuditLogger, AgentAuthenticator,
    SecurityMonitor, ComplianceManager, SecurityTestingFramework
)
from src.utils.config import ConfigManager


@pytest.fixture
def mock_config():
    """Mock configuration for testing."""
    config = Mock()
    config.aws_region = "us-east-1"
    config.get = Mock(return_value="test-value")
    config.aws = Mock()
    config.aws.region = "us-east-1"
    return config


@pytest.fixture
def mock_audit_logger(mock_config):
    """Mock audit logger for testing."""
    with patch('boto3.resource'), patch('boto3.client'):
        logger = TamperProofAuditLogger(mock_config)
        return logger


@pytest.fixture
def mock_agent_authenticator(mock_config):
    """Mock agent authenticator for testing."""
    with patch('boto3.resource'), patch('boto3.client'):
        authenticator = AgentAuthenticator(mock_config)
        return authenticator


@pytest.fixture
def mock_security_monitor(mock_config):
    """Mock security monitor for testing."""
    with patch('boto3.resource'), patch('boto3.client'):
        monitor = SecurityMonitor(mock_config)
        return monitor


@pytest.fixture
def mock_compliance_manager(mock_config):
    """Mock compliance manager for testing."""
    with patch('boto3.resource'), patch('boto3.client'):
        manager = ComplianceManager(mock_config)
        return manager


@pytest.fixture
def mock_security_testing_framework(mock_config):
    """Mock security testing framework for testing."""
    framework = SecurityTestingFramework(mock_config)
    return framework


class TestTamperProofAuditLogger:
    """Test tamper-proof audit logging functionality."""
    
    @pytest.mark.asyncio
    async def test_log_security_event(self, mock_audit_logger):
        """Test logging security events with integrity verification."""
        # Mock the storage method
        mock_audit_logger._store_audit_event = AsyncMock()
        
        # Log a security event
        event = await mock_audit_logger.log_security_event(
            event_type=SecurityEventType.AGENT_AUTHENTICATION,
            severity=SecuritySeverity.MEDIUM,
            action="authenticate",
            outcome="success",
            agent_id="test_agent"
        )
        
        # Verify event properties
        assert event.event_type == SecurityEventType.AGENT_AUTHENTICATION
        assert event.severity == SecuritySeverity.MEDIUM
        assert event.action == "authenticate"
        assert event.outcome == "success"
        assert event.agent_id == "test_agent"
        assert event.integrity_hash is not None
        
        # Verify integrity
        assert event.verify_integrity() is True
        
        # Verify storage was called
        mock_audit_logger._store_audit_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_audit_chain(self, mock_audit_logger):
        """Test audit chain integrity verification."""
        # Mock the get events method
        mock_events = [
            AuditEvent(
                event_id=str(uuid4()),
                event_type=SecurityEventType.AGENT_AUTHENTICATION,
                severity=SecuritySeverity.LOW,
                action="test",
                outcome="success"
            )
        ]
        mock_audit_logger._get_audit_events_by_date_range = AsyncMock(return_value=mock_events)
        
        # Verify chain
        start_date = datetime.utcnow() - timedelta(days=1)
        end_date = datetime.utcnow()
        
        is_valid = await mock_audit_logger.verify_audit_chain(start_date, end_date)
        
        # Should be valid for properly formed events
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_pii_redaction(self, mock_audit_logger):
        """Test PII redaction functionality."""
        test_text = "Contact john.doe@example.com or call 555-123-4567"
        
        result = await mock_audit_logger.redact_pii(test_text)
        
        assert result.original_text == test_text
        assert "[REDACTED_EMAIL]" in result.redacted_text
        assert "[REDACTED_PHONE]" in result.redacted_text
        assert len(result.redacted_items) == 2
        assert result.confidence_score > 0
    
    @pytest.mark.asyncio
    async def test_compliance_report_generation(self, mock_audit_logger):
        """Test compliance report generation."""
        # Mock dependencies
        mock_audit_logger._get_audit_events_by_date_range = AsyncMock(return_value=[])
        mock_audit_logger._verify_data_retention = AsyncMock(return_value=True)
        mock_audit_logger._verify_encryption_compliance = AsyncMock(return_value=True)
        mock_audit_logger._verify_access_control_compliance = AsyncMock(return_value=True)
        mock_audit_logger._store_compliance_report = AsyncMock()
        
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        report = await mock_audit_logger.generate_compliance_report(
            start_date=start_date,
            end_date=end_date,
            compliance_framework="SOC2"
        )
        
        assert report.compliance_framework == "SOC2"
        assert report.period_start == start_date
        assert report.period_end == end_date
        assert report.data_retention_compliance is True
        assert report.encryption_compliance is True
        assert report.access_control_compliance is True


class TestAgentAuthenticator:
    """Test agent cryptographic authentication functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_agent_certificate(self, mock_agent_authenticator):
        """Test agent certificate generation."""
        # Mock storage methods
        mock_agent_authenticator._store_certificate = AsyncMock()
        mock_agent_authenticator._store_private_key = AsyncMock()
        
        certificate = await mock_agent_authenticator.generate_agent_certificate("test_agent")
        
        assert certificate.agent_id == "test_agent"
        assert certificate.certificate_id is not None
        assert certificate.public_key is not None
        assert certificate.is_valid() is True
        assert certificate.status == "active"
    
    @pytest.mark.asyncio
    async def test_certificate_validation(self, mock_agent_authenticator):
        """Test certificate validation logic."""
        # Create a test certificate
        certificate = AgentCertificate(
            agent_id="test_agent",
            certificate_id=str(uuid4()),
            public_key="test_key",
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        assert certificate.is_valid() is True
        assert certificate.is_expired() is False
        assert certificate.days_until_expiry() > 0
    
    @pytest.mark.asyncio
    async def test_certificate_revocation(self, mock_agent_authenticator):
        """Test certificate revocation functionality."""
        # Mock methods
        mock_agent_authenticator.get_agent_certificate = AsyncMock(
            return_value=AgentCertificate(
                agent_id="test_agent",
                certificate_id=str(uuid4()),
                public_key="test_key",
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
        )
        mock_agent_authenticator._store_certificate = AsyncMock()
        
        success = await mock_agent_authenticator.revoke_certificate(
            "test_agent", 
            "test_revocation"
        )
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_impersonation_detection(self, mock_agent_authenticator):
        """Test agent impersonation detection."""
        # Mock signature verification to fail (indicating potential impersonation)
        mock_agent_authenticator.verify_agent_signature = AsyncMock(return_value=False)
        
        is_impersonation = await mock_agent_authenticator.detect_agent_impersonation(
            agent_id="test_agent",
            message="test_message",
            signature="invalid_signature"
        )
        
        assert is_impersonation is True


class TestSecurityMonitor:
    """Test security monitoring and threat detection functionality."""
    
    @pytest.mark.asyncio
    async def test_analyze_security_event(self, mock_security_monitor):
        """Test security event analysis."""
        # Mock methods
        mock_security_monitor._analyze_agent_behavior = AsyncMock(return_value=[])
        mock_security_monitor._detect_suspicious_patterns = AsyncMock(return_value=[])
        mock_security_monitor._correlate_threat_intelligence = AsyncMock(return_value=[])
        mock_security_monitor._analyze_authentication_events = AsyncMock(return_value=[])
        mock_security_monitor._update_behavioral_tracking = AsyncMock()
        mock_security_monitor._store_security_alert = AsyncMock()
        mock_security_monitor._trigger_automated_response = AsyncMock()
        
        # Create test audit event
        audit_event = AuditEvent(
            event_id=str(uuid4()),
            event_type=SecurityEventType.AGENT_AUTHENTICATION,
            severity=SecuritySeverity.MEDIUM,
            action="authenticate",
            outcome="success",
            agent_id="test_agent"
        )
        
        alerts = await mock_security_monitor.analyze_security_event(audit_event)
        
        assert isinstance(alerts, list)
    
    @pytest.mark.asyncio
    async def test_agent_compromise_detection(self, mock_security_monitor):
        """Test agent compromise detection."""
        # Mock detection methods
        mock_security_monitor._detect_unusual_activity_pattern = AsyncMock(return_value=True)
        mock_security_monitor._detect_privilege_escalation_pattern = AsyncMock(return_value=True)
        mock_security_monitor._detect_authentication_anomalies = AsyncMock(return_value=False)
        mock_security_monitor._detect_data_access_anomalies = AsyncMock(return_value=False)
        
        # Add some behavioral data
        mock_security_monitor._agent_behaviors["test_agent"].extend([
            {"timestamp": datetime.utcnow(), "action": "test"} for _ in range(15)
        ])
        
        alert = await mock_security_monitor.detect_agent_compromise("test_agent")
        
        assert alert is not None
        assert alert.alert_type == "agent_compromise"
        assert alert.severity == SecuritySeverity.CRITICAL
    
    @pytest.mark.asyncio
    async def test_security_metrics(self, mock_security_monitor):
        """Test security metrics collection."""
        metrics = await mock_security_monitor.get_security_metrics()
        
        assert hasattr(metrics, 'security_events_total')
        assert hasattr(metrics, 'security_alerts_open')
        assert hasattr(metrics, 'suspicious_behaviors_detected')


class TestComplianceManager:
    """Test compliance management functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_compliance_report(self, mock_compliance_manager):
        """Test compliance report generation."""
        # Mock dependencies
        mock_compliance_manager._get_audit_events_for_period = AsyncMock(return_value=[])
        mock_compliance_manager._count_security_violations = AsyncMock(return_value=0)
        mock_compliance_manager._assess_compliance_controls = AsyncMock(return_value={})
        mock_compliance_manager._verify_data_retention_compliance = AsyncMock(return_value=True)
        mock_compliance_manager._verify_encryption_compliance = AsyncMock(return_value=True)
        mock_compliance_manager._verify_access_control_compliance = AsyncMock(return_value=True)
        mock_compliance_manager._generate_compliance_findings = AsyncMock(return_value=[])
        mock_compliance_manager._generate_compliance_recommendations = AsyncMock(return_value=[])
        mock_compliance_manager._store_compliance_report = AsyncMock()
        mock_compliance_manager._upload_compliance_report_to_s3 = AsyncMock()
        
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        report = await mock_compliance_manager.generate_compliance_report(
            framework="SOC2",
            start_date=start_date,
            end_date=end_date
        )
        
        assert report.compliance_framework == "SOC2"
        assert report.period_start == start_date
        assert report.period_end == end_date
    
    @pytest.mark.asyncio
    async def test_data_retention_enforcement(self, mock_compliance_manager):
        """Test data retention policy enforcement."""
        # Mock cleanup methods
        mock_compliance_manager._cleanup_audit_logs = AsyncMock(return_value=10)
        mock_compliance_manager._cleanup_incident_data = AsyncMock(return_value=5)
        mock_compliance_manager._cleanup_security_alerts = AsyncMock(return_value=3)
        mock_compliance_manager._cleanup_compliance_reports = AsyncMock(return_value=2)
        mock_compliance_manager._cleanup_expired_certificates = AsyncMock(return_value=1)
        mock_compliance_manager._cleanup_threat_intelligence = AsyncMock(return_value=7)
        
        results = await mock_compliance_manager.enforce_data_retention_policy()
        
        assert isinstance(results, dict)
        assert "audit_logs" in results
        assert results["audit_logs"] == 10
    
    @pytest.mark.asyncio
    async def test_compliance_controls_validation(self, mock_compliance_manager):
        """Test compliance controls validation."""
        # Mock validation methods
        mock_compliance_manager._get_audit_events_for_period = AsyncMock(return_value=[])
        mock_compliance_manager._validate_access_control = AsyncMock(return_value=True)
        mock_compliance_manager._validate_encryption_control = AsyncMock(return_value=True)
        mock_compliance_manager._validate_audit_logging_control = AsyncMock(return_value=True)
        mock_compliance_manager._validate_incident_response_control = AsyncMock(return_value=True)
        mock_compliance_manager._validate_change_management_control = AsyncMock(return_value=True)
        
        results = await mock_compliance_manager.validate_compliance_controls("SOC2")
        
        assert isinstance(results, dict)
        assert all(results.values())  # All controls should pass


class TestSecurityTestingFramework:
    """Test security testing framework functionality."""
    
    @pytest.mark.asyncio
    async def test_comprehensive_security_test_suite(self, mock_security_testing_framework):
        """Test comprehensive security test suite execution."""
        # Mock test category methods
        mock_security_testing_framework._run_authentication_tests = AsyncMock(
            return_value={"category": "authentication", "tests": []}
        )
        mock_security_testing_framework._run_authorization_tests = AsyncMock(
            return_value={"category": "authorization", "tests": []}
        )
        mock_security_testing_framework._run_agent_security_tests = AsyncMock(
            return_value={"category": "agent_security", "tests": []}
        )
        mock_security_testing_framework._run_data_protection_tests = AsyncMock(
            return_value={"category": "data_protection", "tests": []}
        )
        mock_security_testing_framework._run_network_security_tests = AsyncMock(
            return_value={"category": "network_security", "tests": []}
        )
        mock_security_testing_framework._run_compliance_tests = AsyncMock(
            return_value={"category": "compliance", "tests": []}
        )
        mock_security_testing_framework._run_penetration_tests = AsyncMock(
            return_value={"category": "penetration", "tests": []}
        )
        mock_security_testing_framework._generate_security_recommendations = AsyncMock(
            return_value=[]
        )
        
        results = await mock_security_testing_framework.run_comprehensive_security_test_suite()
        
        assert "test_suite_id" in results
        assert "tests" in results
        assert "summary" in results
        assert "vulnerabilities" in results
        assert "recommendations" in results
    
    @pytest.mark.asyncio
    async def test_penetration_test_scenario(self, mock_security_testing_framework):
        """Test specific penetration test scenario execution."""
        # Mock penetration test method
        mock_security_testing_framework._test_agent_impersonation = AsyncMock(
            return_value={"vulnerabilities": [], "recommendations": []}
        )
        
        results = await mock_security_testing_framework.run_penetration_test_scenario(
            "agent_impersonation"
        )
        
        assert isinstance(results, dict)
        assert "vulnerabilities" in results
        assert "recommendations" in results
    
    @pytest.mark.asyncio
    async def test_compliance_validation(self, mock_security_testing_framework):
        """Test security compliance validation."""
        # Mock compliance test methods
        mock_security_testing_framework._test_soc2_access_controls = AsyncMock(
            return_value=Mock(passed=True, severity=SecuritySeverity.HIGH)
        )
        mock_security_testing_framework._test_soc2_system_operations = AsyncMock(
            return_value=Mock(passed=True, severity=SecuritySeverity.MEDIUM)
        )
        mock_security_testing_framework._test_soc2_change_management = AsyncMock(
            return_value=Mock(passed=True, severity=SecuritySeverity.MEDIUM)
        )
        mock_security_testing_framework._test_soc2_logical_access = AsyncMock(
            return_value=Mock(passed=True, severity=SecuritySeverity.HIGH)
        )
        mock_security_testing_framework._test_soc2_system_monitoring = AsyncMock(
            return_value=Mock(passed=True, severity=SecuritySeverity.MEDIUM)
        )
        
        results = await mock_security_testing_framework.validate_security_compliance("SOC2")
        
        assert results["framework"] == "SOC2"
        assert results["compliance_score"] >= 80
        assert results["compliant"] is True


class TestSecurityIntegration:
    """Test security service integration."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_security_workflow(self, mock_config):
        """Test end-to-end security workflow integration."""
        with patch('boto3.resource'), patch('boto3.client'):
            # Initialize all security services
            audit_logger = TamperProofAuditLogger(mock_config)
            authenticator = AgentAuthenticator(mock_config)
            monitor = SecurityMonitor(mock_config, audit_logger, authenticator)
            
            # Mock methods
            audit_logger._store_audit_event = AsyncMock()
            authenticator._store_certificate = AsyncMock()
            authenticator._store_private_key = AsyncMock()
            monitor._store_security_alert = AsyncMock()
            monitor._trigger_automated_response = AsyncMock()
            monitor._analyze_agent_behavior = AsyncMock(return_value=[])
            monitor._detect_suspicious_patterns = AsyncMock(return_value=[])
            monitor._correlate_threat_intelligence = AsyncMock(return_value=[])
            monitor._analyze_authentication_events = AsyncMock(return_value=[])
            monitor._update_behavioral_tracking = AsyncMock()
            
            # Test workflow: Generate certificate -> Log event -> Analyze security
            certificate = await authenticator.generate_agent_certificate("test_agent")
            
            audit_event = await audit_logger.log_security_event(
                event_type=SecurityEventType.AGENT_AUTHENTICATION,
                severity=SecuritySeverity.MEDIUM,
                action="certificate_generated",
                outcome="success",
                agent_id="test_agent"
            )
            
            alerts = await monitor.analyze_security_event(audit_event)
            
            # Verify integration
            assert certificate.agent_id == "test_agent"
            assert audit_event.agent_id == "test_agent"
            assert isinstance(alerts, list)


if __name__ == "__main__":
    pytest.main([__file__])