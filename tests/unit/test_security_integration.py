"""
Test security service integration with existing agent communication models.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from src.services.security_service import SecurityService, get_security_service
from src.models.security import SecurityEventType, SecuritySeverity
from src.models.agent import (
    AgentMessage, 
    AgentType, 
    AgentRecommendation, 
    ActionType, 
    RiskLevel,
    Evidence
)


class TestSecurityServiceIntegration:
    """Test security service integration with agent models."""
    
    @pytest.fixture
    def security_service(self):
        """Create security service for testing."""
        return SecurityService()
    
    @pytest.fixture
    def sample_agent_message(self):
        """Create sample agent message."""
        return AgentMessage(
            sender_agent=AgentType.DETECTION,
            recipient_agent=AgentType.DIAGNOSIS,
            message_type="incident_detected",
            payload={"incident_id": "inc_123", "severity": "high"},
            correlation_id="corr_456"
        )
    
    @pytest.fixture
    def sample_agent_recommendation(self):
        """Create sample agent recommendation."""
        return AgentRecommendation(
            agent_name=AgentType.RESOLUTION,
            incident_id="inc_123",
            action_type=ActionType.RESTART_SERVICE,
            action_id="restart_web_service",
            confidence=0.85,
            risk_level=RiskLevel.MEDIUM,
            estimated_impact="Service downtime: 30 seconds",
            reasoning="High memory usage detected, restart will clear memory leak",
            urgency=0.8,  # Add required urgency field
            evidence=[
                Evidence(
                    source="cloudwatch_metrics",
                    data={"memory_usage": "95%", "trend": "increasing"},
                    confidence=0.9,
                    description="Memory usage trending upward"
                )
            ]
        )
    
    @pytest.mark.asyncio
    async def test_agent_authentication_logging(self, security_service):
        """Test logging agent authentication events."""
        # Successful authentication
        event = await security_service.log_agent_authentication(
            agent_id="detection_agent_001",
            agent_type=AgentType.DETECTION,
            outcome="success",
            source_ip="10.0.1.100"
        )
        
        assert event.event_type == SecurityEventType.AGENT_AUTHENTICATION
        assert event.severity == SecuritySeverity.LOW
        assert event.agent_id == "detection_agent_001"
        assert event.outcome == "success"
        assert event.details["agent_type"] == "detection"
        assert event.source_ip == "10.0.1.100"
        assert event.verify_integrity() is True
        
        # Failed authentication
        failed_event = await security_service.log_agent_authentication(
            agent_id="suspicious_agent_001",
            agent_type=AgentType.DIAGNOSIS,
            outcome="failed"
        )
        
        assert failed_event.severity == SecuritySeverity.MEDIUM
        assert failed_event.outcome == "failed"
        
        # Check metrics updated
        metrics = await security_service.get_security_metrics()
        assert metrics.successful_authentications == 1
        assert metrics.failed_authentications == 1
    
    @pytest.mark.asyncio
    async def test_agent_message_logging(self, security_service, sample_agent_message):
        """Test logging agent communication events."""
        event = await security_service.log_agent_message(sample_agent_message)
        
        assert event.event_type == SecurityEventType.AGENT_AUTHORIZATION
        assert event.agent_id == "detection_agent"
        assert event.action == "send_message"
        assert event.details["message_type"] == "incident_detected"
        assert event.details["recipient_agent"] == "diagnosis"
        assert event.details["correlation_id"] == "corr_456"
        assert event.verify_integrity() is True
    
    @pytest.mark.asyncio
    async def test_agent_recommendation_logging(self, security_service, sample_agent_recommendation):
        """Test logging agent recommendation events."""
        event = await security_service.log_agent_recommendation(sample_agent_recommendation)
        
        assert event.event_type == SecurityEventType.DATA_ACCESS
        assert event.agent_id == "resolution_agent"
        assert event.action == "create_recommendation"
        assert event.details["incident_id"] == "inc_123"
        assert event.details["action_type"] == "restart_service"
        assert event.details["confidence"] == 0.85
        assert event.details["risk_level"] == "medium"
        assert event.details["evidence_count"] == 1
        assert event.verify_integrity() is True
    
    @pytest.mark.asyncio
    async def test_agent_anomaly_detection(self, security_service):
        """Test agent anomaly detection and alerting."""
        # High confidence anomaly
        alert = await security_service.detect_agent_anomaly(
            agent_id="diagnosis_agent_002",
            anomaly_indicators=[
                "processing_time_anomaly",
                "unusual_api_calls",
                "confidence_score_drift"
            ],
            confidence_score=0.92
        )
        
        assert alert is not None
        assert alert.alert_type == "agent_behavioral_anomaly"
        assert alert.severity == SecuritySeverity.HIGH
        assert alert.agent_id == "diagnosis_agent_002"
        assert alert.confidence_score == 0.92
        assert len(alert.indicators) == 3
        assert "quarantine_agent" in alert.mitigation_actions
        
        # Low confidence anomaly (should not create alert)
        no_alert = await security_service.detect_agent_anomaly(
            agent_id="normal_agent_001",
            anomaly_indicators=["minor_deviation"],
            confidence_score=0.5
        )
        
        assert no_alert is None
        
        # Check metrics updated
        metrics = await security_service.get_security_metrics()
        assert metrics.suspicious_behaviors_detected == 1
        assert metrics.potential_compromises_detected == 1
    
    @pytest.mark.asyncio
    async def test_agent_certificate_lifecycle(self, security_service):
        """Test agent certificate issuance and validation."""
        agent_id = "prediction_agent_001"
        public_key = "-----BEGIN PUBLIC KEY-----\ntest_key_data\n-----END PUBLIC KEY-----"
        
        # Issue certificate
        certificate = await security_service.issue_agent_certificate(
            agent_id=agent_id,
            public_key=public_key,
            validity_days=90
        )
        
        assert certificate.agent_id == agent_id
        assert certificate.public_key == public_key
        assert certificate.is_valid() is True
        
        # Validate certificate
        is_valid = await security_service.validate_agent_certificate(agent_id)
        assert is_valid is True
        
        # Try to validate non-existent certificate
        is_invalid = await security_service.validate_agent_certificate("non_existent_agent")
        assert is_invalid is False
        
        # Check metrics
        metrics = await security_service.get_security_metrics()
        assert metrics.active_agent_certificates == 1
        assert metrics.expired_certificates == 0
    
    @pytest.mark.asyncio
    async def test_security_metrics_calculation(self, security_service):
        """Test security metrics calculation and updates."""
        # Generate some security events
        await security_service.log_agent_authentication("agent1", AgentType.DETECTION, "success")
        await security_service.log_agent_authentication("agent2", AgentType.DIAGNOSIS, "success")
        await security_service.log_agent_authentication("agent3", AgentType.PREDICTION, "failed")
        
        await security_service.detect_agent_anomaly("agent1", ["anomaly1"], 0.8)
        await security_service.detect_agent_anomaly("agent2", ["anomaly2"], 0.95)
        
        await security_service.issue_agent_certificate("agent1", "key1")
        await security_service.issue_agent_certificate("agent2", "key2")
        
        # Get metrics
        metrics = await security_service.get_security_metrics()
        
        assert metrics.successful_authentications == 2
        assert metrics.failed_authentications == 1
        assert abs(metrics.authentication_rate - 66.67) < 0.01  # 2/3 * 100, allow for floating point precision
        assert metrics.security_events_total > 0
        assert metrics.suspicious_behaviors_detected == 2
        assert metrics.potential_compromises_detected == 1
        assert metrics.active_agent_certificates == 2
        assert metrics.security_alerts_open == 2
        assert metrics.audit_events_last_24h > 0
    
    @pytest.mark.asyncio
    async def test_audit_trail_filtering(self, security_service):
        """Test audit trail retrieval with filtering."""
        # Create events for different agents
        await security_service.log_agent_authentication("agent1", AgentType.DETECTION, "success")
        await security_service.log_agent_authentication("agent2", AgentType.DIAGNOSIS, "success")
        await security_service.log_security_event(
            SecurityEventType.CONFIGURATION_CHANGE,
            SecuritySeverity.MEDIUM,
            action="update_config",
            outcome="success",
            agent_id="agent1"
        )
        
        # Get all events
        all_events = await security_service.get_audit_trail()
        assert len(all_events) >= 3
        
        # Filter by agent
        agent1_events = await security_service.get_audit_trail(agent_id="agent1")
        assert len(agent1_events) == 2
        assert all(event.agent_id == "agent1" for event in agent1_events)
        
        # Filter by event type
        auth_events = await security_service.get_audit_trail(
            event_type=SecurityEventType.AGENT_AUTHENTICATION
        )
        assert len(auth_events) == 2
        assert all(event.event_type == SecurityEventType.AGENT_AUTHENTICATION for event in auth_events)
    
    @pytest.mark.asyncio
    async def test_data_cleanup(self, security_service):
        """Test cleanup of expired certificates and old audit events."""
        # Create expired certificate
        agent_id = "expired_agent"
        certificate = await security_service.issue_agent_certificate(
            agent_id=agent_id,
            public_key="test_key",
            validity_days=1
        )
        
        # Manually expire the certificate
        certificate.expires_at = datetime.utcnow() - timedelta(days=1)
        
        # Create old audit event
        old_event = await security_service.log_security_event(
            SecurityEventType.AGENT_AUTHENTICATION,
            SecuritySeverity.LOW,
            action="test",
            outcome="success"
        )
        
        # Manually age the event
        old_event.timestamp = datetime.utcnow() - timedelta(days=31)
        
        # Run cleanup
        await security_service.cleanup_expired_data()
        
        # Check that expired data was removed
        assert agent_id not in security_service.agent_certificates
        assert old_event not in security_service.audit_events
    
    def test_global_security_service_singleton(self):
        """Test global security service singleton."""
        service1 = get_security_service()
        service2 = get_security_service()
        
        assert service1 is service2
        assert isinstance(service1, SecurityService)


class TestSecurityServiceErrorHandling:
    """Test security service error handling and edge cases."""
    
    @pytest.fixture
    def security_service(self):
        """Create security service for testing."""
        return SecurityService()
    
    @pytest.mark.asyncio
    async def test_invalid_agent_certificate_validation(self, security_service):
        """Test validation of invalid agent certificates."""
        # Test with non-existent agent
        is_valid = await security_service.validate_agent_certificate("non_existent")
        assert is_valid is False
        
        # Test with expired certificate
        agent_id = "test_agent"
        certificate = await security_service.issue_agent_certificate(
            agent_id=agent_id,
            public_key="test_key",
            validity_days=1
        )
        
        # Manually expire the certificate
        certificate.expires_at = datetime.utcnow() - timedelta(days=1)
        
        is_valid = await security_service.validate_agent_certificate(agent_id)
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_security_event_integrity(self, security_service):
        """Test security event integrity verification."""
        event = await security_service.log_security_event(
            SecurityEventType.SECURITY_VIOLATION,
            SecuritySeverity.HIGH,
            action="unauthorized_access",
            outcome="blocked",
            details={"source": "external", "blocked_reason": "invalid_credentials"}
        )
        
        # Verify integrity
        assert event.verify_integrity() is True
        
        # Tamper with event
        original_outcome = event.outcome
        event.outcome = "allowed"
        
        # Integrity should fail
        assert event.verify_integrity() is False
        
        # Restore original data
        event.outcome = original_outcome
        assert event.verify_integrity() is True