"""
Comprehensive end-to-end tests for completed Milestone 1.
"""

import pytest
import asyncio
from datetime import datetime

from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
from src.models.agent import AgentRecommendation, ActionType, RiskLevel, AgentType
from src.orchestrator.swarm_coordinator import AgentSwarmCoordinator, ProcessingPhase
from src.services.consensus import BasicWeightedConsensusEngine
from agents.detection.agent import RobustDetectionAgent
from agents.diagnosis.agent import HardenedDiagnosisAgent


class TestMilestone1Complete:
    """Test complete Milestone 1 functionality."""
    
    @pytest.fixture
    def sample_incident(self):
        """Create sample incident for testing."""
        business_impact = BusinessImpact(
            service_tier=ServiceTier.TIER_1,
            affected_users=5000,
            revenue_impact_per_minute=1000.0
        )
        
        metadata = IncidentMetadata(
            source_system="test_system",
            tags={"environment": "production", "service": "payment_api"}
        )
        
        return Incident(
            title="Payment API Database Connection Failures",
            description="Critical database connection failures causing payment processing outages",
            severity=IncidentSeverity.CRITICAL,
            business_impact=business_impact,
            metadata=metadata
        )
    
    @pytest.fixture
    def coordinator_with_agents(self):
        """Create coordinator with registered agents."""
        coordinator = AgentSwarmCoordinator()
        
        # Register agents
        detection_agent = RobustDetectionAgent("test_detection")
        diagnosis_agent = HardenedDiagnosisAgent("test_diagnosis")
        
        coordinator.register_agent(detection_agent)
        coordinator.register_agent(diagnosis_agent)
        
        return coordinator
    
    @pytest.mark.asyncio
    async def test_consensus_engine_basic_functionality(self, sample_incident):
        """Test basic consensus engine functionality."""
        consensus_engine = BasicWeightedConsensusEngine()
        
        # Create test recommendations
        detection_rec = AgentRecommendation(
            agent_name=AgentType.DETECTION,
            incident_id=sample_incident.id,
            action_type=ActionType.ESCALATE_INCIDENT,
            action_id="escalate_critical",
            confidence=0.9,
            risk_level=RiskLevel.LOW,
            estimated_impact="Immediate escalation for critical incident",
            reasoning="Critical severity requires immediate attention",
            urgency=0.9
        )
        
        diagnosis_rec = AgentRecommendation(
            agent_name=AgentType.DIAGNOSIS,
            incident_id=sample_incident.id,
            action_type=ActionType.RESTART_SERVICE,
            action_id="restart_database_connections",
            confidence=0.8,
            risk_level=RiskLevel.MEDIUM,
            estimated_impact="Restore database connectivity",
            reasoning="Database connection pool exhaustion detected",
            urgency=0.8
        )
        
        recommendations = [detection_rec, diagnosis_rec]
        
        # Test consensus
        decision = await consensus_engine.reach_consensus(sample_incident, recommendations)
        
        assert decision is not None
        assert decision.incident_id == sample_incident.id
        assert decision.final_confidence > 0.0
        assert decision.selected_action in ["escalate_critical", "restart_database_connections"]
        assert len(decision.participating_agents) == 2
        assert decision.consensus_method == "weighted_voting"
    
    @pytest.mark.asyncio
    async def test_consensus_engine_conflict_resolution(self, sample_incident):
        """Test consensus engine conflict resolution."""
        consensus_engine = BasicWeightedConsensusEngine()
        
        # Create conflicting recommendations
        rec1 = AgentRecommendation(
            agent_name=AgentType.DETECTION,
            incident_id=sample_incident.id,
            action_type=ActionType.SCALE_UP,
            action_id="scale_up_service",
            confidence=0.7,
            risk_level=RiskLevel.LOW,
            estimated_impact="Increase capacity",
            reasoning="High load detected",
            urgency=0.6
        )
        
        rec2 = AgentRecommendation(
            agent_name=AgentType.DIAGNOSIS,
            incident_id=sample_incident.id,
            action_type=ActionType.RESTART_SERVICE,
            action_id="restart_service",
            confidence=0.8,
            risk_level=RiskLevel.MEDIUM,
            estimated_impact="Fix service issues",
            reasoning="Service corruption detected",
            urgency=0.8
        )
        
        recommendations = [rec1, rec2]
        
        # Test conflict resolution
        decision = await consensus_engine.reach_consensus(sample_incident, recommendations)
        
        assert decision.conflicts_detected
        # Diagnosis agent has higher weight (0.4 vs 0.2), so should win
        assert decision.selected_action == "restart_service"
        assert decision.final_confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_consensus_engine_byzantine_fault_detection(self, sample_incident):
        """Test Byzantine fault detection."""
        consensus_engine = BasicWeightedConsensusEngine()
        
        # Create suspicious recommendation (bypass Pydantic validation for testing)
        suspicious_rec = AgentRecommendation(
            agent_name=AgentType.DETECTION,
            incident_id=sample_incident.id,
            action_type=ActionType.ESCALATE_INCIDENT,
            action_id="no_action",
            confidence=0.99,  # Very high confidence without evidence
            risk_level=RiskLevel.LOW,
            estimated_impact="Do nothing",
            reasoning="Everything is fine",
            urgency=0.1
        )
        # Manually set invalid confidence after creation
        suspicious_rec.confidence = 1.5
        
        normal_rec = AgentRecommendation(
            agent_name=AgentType.DIAGNOSIS,
            incident_id=sample_incident.id,
            action_type=ActionType.ESCALATE_INCIDENT,
            action_id="escalate",
            confidence=0.8,
            risk_level=RiskLevel.MEDIUM,
            estimated_impact="Escalate incident",
            reasoning="Critical issue detected",
            urgency=0.8
        )
        
        recommendations = [suspicious_rec, normal_rec]
        
        # Test Byzantine fault detection
        suspicious_agents = await consensus_engine.detect_byzantine_faults(recommendations)
        
        assert "detection" in suspicious_agents
        
        # Test consensus with Byzantine fault filtering
        decision = await consensus_engine.reach_consensus(sample_incident, recommendations)
        
        # Should only use the normal recommendation
        assert decision.selected_action == "escalate"
        assert len(decision.participating_agents) == 1
        assert "diagnosis" in decision.participating_agents
    
    @pytest.mark.asyncio
    async def test_agent_swarm_coordinator_basic_flow(self, coordinator_with_agents, sample_incident):
        """Test basic agent swarm coordinator flow."""
        coordinator = coordinator_with_agents
        
        # Test incident processing
        decision = await coordinator.process_incident(sample_incident)
        
        assert decision is not None
        assert decision.incident_id == sample_incident.id
        
        # Check processing state
        status = coordinator.get_incident_status(sample_incident.id)
        assert status is not None
        assert status["incident_id"] == sample_incident.id
        assert status["phase"] in ["completed", "failed"]
        
        # Check that agents were executed
        assert len(status["agent_executions"]) >= 1
        
        # Check metrics
        metrics = coordinator.get_processing_metrics()
        assert metrics["total_incidents"] >= 1
        assert metrics["registered_agents"] == 2
    
    @pytest.mark.asyncio
    async def test_agent_swarm_coordinator_agent_failure_handling(self, sample_incident):
        """Test agent failure handling in coordinator."""
        coordinator = AgentSwarmCoordinator()
        
        # Create a failing agent (mock)
        class FailingAgent:
            def __init__(self):
                self.name = "failing_agent"
                self.agent_type = AgentType.DETECTION
                self.is_healthy = True
                self.last_heartbeat = datetime.utcnow()
                self.processing_count = 0
                self.error_count = 0
            
            async def process_incident(self, incident):
                raise Exception("Simulated agent failure")
            
            async def handle_message(self, message):
                return None
            
            async def health_check(self):
                return False
        
        # Register failing agent
        failing_agent = FailingAgent()
        coordinator.register_agent(failing_agent)
        
        # Process incident
        decision = await coordinator.process_incident(sample_incident)
        
        # Should handle failure gracefully
        assert decision is not None
        
        # Check that failure was recorded
        status = coordinator.get_incident_status(sample_incident.id)
        assert status is not None
        
        failed_agents = [
            name for name, exec in status["agent_executions"].items()
            if exec["status"] == "failed"
        ]
        assert "failing_agent" in failed_agents
    
    @pytest.mark.asyncio
    async def test_agent_swarm_coordinator_health_monitoring(self, coordinator_with_agents):
        """Test agent health monitoring."""
        coordinator = coordinator_with_agents
        
        # Test health check
        is_healthy = await coordinator.health_check()
        assert isinstance(is_healthy, bool)
        
        # Test agent status
        agent_status = coordinator.get_agent_health_status()
        assert len(agent_status) == 2
        
        for agent_name, status in agent_status.items():
            assert "agent_type" in status
            assert "is_healthy" in status
            assert "circuit_breaker_state" in status
            assert status["circuit_breaker_state"] in ["closed", "open", "half_open"]
    
    @pytest.mark.asyncio
    async def test_end_to_end_incident_processing_performance(self, coordinator_with_agents, sample_incident):
        """Test end-to-end performance requirements."""
        coordinator = coordinator_with_agents
        
        import time
        start_time = time.time()
        
        # Process incident
        decision = await coordinator.process_incident(sample_incident)
        
        end_time = time.time()
        processing_duration = end_time - start_time
        
        # Should complete within 3 minutes (180 seconds) for Milestone 1
        assert processing_duration < 180, f"Processing took {processing_duration:.2f}s, expected < 180s"
        
        # Check decision quality
        assert decision is not None
        assert decision.final_confidence >= 0.0
        
        # Check processing state
        status = coordinator.get_incident_status(sample_incident.id)
        assert status["duration_seconds"] < 180
    
    @pytest.mark.asyncio
    async def test_business_impact_calculations_integration(self, sample_incident):
        """Test business impact calculations in real processing."""
        # Test cost calculations
        cost_per_minute = sample_incident.business_impact.calculate_cost_per_minute()
        assert cost_per_minute > 1000.0  # Tier 1 with high user count
        
        # Test total cost calculation
        total_cost_5min = sample_incident.business_impact.calculate_total_cost(5.0)
        assert total_cost_5min == cost_per_minute * 5.0
        
        # Test that business impact influences consensus
        consensus_engine = BasicWeightedConsensusEngine()
        
        # Create escalation recommendation
        escalation_rec = AgentRecommendation(
            agent_name=AgentType.DETECTION,
            incident_id=sample_incident.id,
            action_type=ActionType.ESCALATE_INCIDENT,
            action_id="escalate_high_cost",
            confidence=0.7,
            risk_level=RiskLevel.HIGH,
            estimated_impact=f"Prevent ${cost_per_minute:.2f}/minute loss",
            reasoning="High business impact requires immediate escalation",
            urgency=0.9
        )
        
        decision = await consensus_engine.reach_consensus(sample_incident, [escalation_rec])
        
        # High cost incidents should trigger escalation
        assert decision.requires_human_approval or decision.final_confidence >= 0.7
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration_with_agents(self, coordinator_with_agents, sample_incident):
        """Test circuit breaker integration with agent processing."""
        coordinator = coordinator_with_agents
        
        from src.services.circuit_breaker import circuit_breaker_manager
        
        # Get circuit breakers for agents
        detection_cb = circuit_breaker_manager.get_agent_circuit_breaker("test_detection")
        diagnosis_cb = circuit_breaker_manager.get_agent_circuit_breaker("test_diagnosis")
        
        # Initial state should be closed
        assert detection_cb.state.value == "closed"
        assert diagnosis_cb.state.value == "closed"
        
        # Process incident
        await coordinator.process_incident(sample_incident)
        
        # Circuit breakers should still be closed (successful processing)
        assert detection_cb.state.value == "closed"
        assert diagnosis_cb.state.value == "closed"
        
        # Check circuit breaker dashboard
        dashboard = circuit_breaker_manager.get_health_dashboard()
        assert dashboard["healthy_services"] >= 2
        assert dashboard["unhealthy_services"] == 0
    
    def test_consensus_engine_statistics_tracking(self, sample_incident):
        """Test consensus engine statistics tracking."""
        consensus_engine = BasicWeightedConsensusEngine()
        
        # Initial stats should be empty
        stats = consensus_engine.get_consensus_statistics()
        assert stats["total_decisions"] == 0
        
        # Process some decisions
        asyncio.run(self._process_multiple_decisions(consensus_engine, sample_incident))
        
        # Check updated stats
        stats = consensus_engine.get_consensus_statistics()
        assert stats["total_decisions"] > 0
        assert "average_confidence" in stats
        assert "escalation_rate" in stats
        assert "conflict_rate" in stats
    
    async def _process_multiple_decisions(self, consensus_engine, sample_incident):
        """Helper to process multiple decisions for statistics."""
        for i in range(3):
            rec = AgentRecommendation(
                agent_name=AgentType.DETECTION,
                incident_id=f"{sample_incident.id}_{i}",
                action_type=ActionType.ESCALATE_INCIDENT,
                action_id=f"action_{i}",
                confidence=0.8,
                risk_level=RiskLevel.MEDIUM,
                estimated_impact="Test action",
                reasoning="Test reasoning",
                urgency=0.7
            )
            
            await consensus_engine.reach_consensus(sample_incident, [rec])
    
    @pytest.mark.asyncio
    async def test_memory_pressure_handling_during_processing(self, coordinator_with_agents):
        """Test memory pressure handling during incident processing."""
        coordinator = coordinator_with_agents
        
        # Get detection agent to test memory management
        detection_agent = None
        for agent in coordinator.agents.values():
            if agent.agent_type == AgentType.DETECTION:
                detection_agent = agent
                break
        
        assert detection_agent is not None
        
        # Check memory stats
        memory_stats = detection_agent.get_memory_stats()
        assert "total_mb" in memory_stats
        assert "percentage" in memory_stats
        assert memory_stats["percentage"] >= 0
        
        # Memory usage should be reasonable
        assert memory_stats["percentage"] < 90  # Should not be using > 90% memory
    
    @pytest.mark.asyncio
    async def test_rate_limiter_integration_with_processing(self):
        """Test rate limiter integration with agent processing."""
        from src.services.rate_limiter import bedrock_rate_limiter, external_service_rate_limiter
        from src.services.rate_limiter import RequestPriority
        
        # Test Bedrock rate limiter
        try:
            model_id = await bedrock_rate_limiter.request_model_access(
                "anthropic.claude-3-sonnet-20240229-v1:0",
                complexity_score=0.8,
                priority=RequestPriority.HIGH
            )
            assert model_id is not None
        except Exception as e:
            # Rate limit exceeded is acceptable
            assert "rate limit" in str(e).lower() or "not available" in str(e).lower()
        
        # Test external service rate limiter
        try:
            access_granted = await external_service_rate_limiter.request_service_access(
                "slack",
                RequestPriority.MEDIUM
            )
            assert isinstance(access_granted, bool)
        except Exception as e:
            # Rate limit exceeded is acceptable
            assert "rate limit" in str(e).lower()
        
        # Check rate limiter status
        bedrock_status = bedrock_rate_limiter.get_status()
        assert "models" in bedrock_status
        assert "queue_length" in bedrock_status


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])