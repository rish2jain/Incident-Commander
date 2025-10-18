"""
Basic tests to verify foundation components are working.
"""

import pytest
from datetime import datetime

from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
from src.models.agent import AgentRecommendation, ActionType, RiskLevel, AgentType
from src.utils.config import config
from src.utils.constants import CONSENSUS_CONFIG, PERFORMANCE_TARGETS
from agents.detection.agent import RobustDetectionAgent, AlertSampler


class TestFoundationModels:
    """Test basic model functionality."""
    
    def test_incident_creation(self):
        """Test incident model creation and validation."""
        business_impact = BusinessImpact(
            service_tier=ServiceTier.TIER_1,
            affected_users=1000,
            revenue_impact_per_minute=500.0
        )
        
        metadata = IncidentMetadata(
            source_system="test",
            tags={"test": "true"}
        )
        
        incident = Incident(
            title="Test Incident",
            description="This is a test incident",
            severity=IncidentSeverity.HIGH,
            business_impact=business_impact,
            metadata=metadata
        )
        
        assert incident.title == "Test Incident"
        assert incident.severity == IncidentSeverity.HIGH
        assert incident.business_impact.service_tier == ServiceTier.TIER_1
        assert incident.id is not None
        assert incident.detected_at is not None
    
    def test_business_impact_calculation(self):
        """Test business impact cost calculations."""
        business_impact = BusinessImpact(
            service_tier=ServiceTier.TIER_1,
            affected_users=2000,
            revenue_impact_per_minute=100.0
        )
        
        cost_per_minute = business_impact.calculate_cost_per_minute()
        assert cost_per_minute > 1000.0  # Base cost + user multiplier + revenue impact
        
        total_cost = business_impact.calculate_total_cost(10.0)  # 10 minutes
        assert total_cost == cost_per_minute * 10.0
    
    def test_agent_recommendation_creation(self):
        """Test agent recommendation model."""
        recommendation = AgentRecommendation(
            agent_name=AgentType.DETECTION,
            incident_id="test-incident-123",
            action_type=ActionType.ESCALATE_INCIDENT,
            action_id="escalate_high_severity",
            confidence=0.85,
            risk_level=RiskLevel.LOW,
            estimated_impact="Improved response time",
            reasoning="High severity incident requires immediate attention",
            urgency=0.7
        )
        
        assert recommendation.agent_name == AgentType.DETECTION
        assert recommendation.confidence == 0.85
        assert recommendation.risk_level == RiskLevel.LOW
        assert not recommendation.is_expired()
    
    def test_incident_checksum_integrity(self):
        """Test incident integrity verification."""
        business_impact = BusinessImpact(service_tier=ServiceTier.TIER_2)
        metadata = IncidentMetadata(source_system="test")
        
        incident = Incident(
            title="Integrity Test",
            description="Testing checksum functionality",
            severity=IncidentSeverity.MEDIUM,
            business_impact=business_impact,
            metadata=metadata
        )
        
        # Generate and verify checksum
        incident.update_checksum()
        assert incident.verify_integrity()
        
        # Modify incident and verify integrity fails
        incident.title = "Modified Title"
        assert not incident.verify_integrity()


class TestConfiguration:
    """Test configuration management."""
    
    def test_config_loading(self):
        """Test configuration loading."""
        assert config.aws.region is not None
        assert config.bedrock.primary_model is not None
        assert config.database.dynamodb_table_prefix is not None
    
    def test_constants_loading(self):
        """Test shared constants are loaded correctly."""
        assert CONSENSUS_CONFIG["autonomous_confidence_threshold"] == 0.7
        assert "detection" in PERFORMANCE_TARGETS
        assert PERFORMANCE_TARGETS["detection"]["target"] == 30


class TestDetectionAgent:
    """Test detection agent functionality."""
    
    @pytest.fixture
    def detection_agent(self):
        """Create detection agent for testing."""
        return RobustDetectionAgent("test_detection")
    
    def test_agent_initialization(self, detection_agent):
        """Test agent initialization."""
        assert detection_agent.name == "test_detection"
        assert detection_agent.agent_type == AgentType.DETECTION
        assert detection_agent.is_healthy
        assert detection_agent.processing_count == 0
    
    @pytest.mark.asyncio
    async def test_alert_sampler(self):
        """Test alert sampling functionality."""
        sampler = AlertSampler(max_rate=10)
        
        # Test normal sampling
        alert = {
            "id": "test-alert-1",
            "severity": "high",
            "source": "api-gateway",
            "message": "High error rate detected"
        }
        
        assert await sampler.should_sample_alert(alert)
    
    @pytest.mark.asyncio
    async def test_memory_pressure_detection(self, detection_agent):
        """Test memory pressure detection."""
        memory_usage = await detection_agent.check_memory_pressure()
        assert 0.0 <= memory_usage <= 1.0
    
    @pytest.mark.asyncio
    async def test_agent_health_check(self, detection_agent):
        """Test agent health check."""
        is_healthy = await detection_agent.health_check()
        assert isinstance(is_healthy, bool)
    
    @pytest.mark.asyncio
    async def test_incident_processing(self, detection_agent):
        """Test incident processing."""
        business_impact = BusinessImpact(service_tier=ServiceTier.TIER_1)
        metadata = IncidentMetadata(source_system="test")
        
        incident = Incident(
            title="Test Processing",
            description="Testing incident processing",
            severity=IncidentSeverity.HIGH,
            business_impact=business_impact,
            metadata=metadata
        )
        
        recommendations = await detection_agent.process_incident(incident)
        assert isinstance(recommendations, list)
        
        # High severity incidents should generate recommendations
        if recommendations:
            assert all(isinstance(rec, AgentRecommendation) for rec in recommendations)


class TestUtilities:
    """Test utility functions."""
    
    def test_logging_configuration(self):
        """Test logging is configured properly."""
        from src.utils.logging import get_logger
        
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "incident_commander.test"
    
    def test_exception_hierarchy(self):
        """Test custom exception hierarchy."""
        from src.utils.exceptions import (
            IncidentCommanderError, AgentError, ConsensusError, 
            EventStoreError, SecurityError
        )
        
        # Test inheritance
        assert issubclass(AgentError, IncidentCommanderError)
        assert issubclass(ConsensusError, IncidentCommanderError)
        assert issubclass(EventStoreError, IncidentCommanderError)
        assert issubclass(SecurityError, IncidentCommanderError)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])