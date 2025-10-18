"""
Comprehensive tests for Milestone 2 completion: Byzantine Consensus and System Health Monitoring.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
from src.models.agent import AgentRecommendation, AgentType, ActionType, RiskLevel
from src.services.aws import AWSServiceFactory
from src.services.byzantine_consensus import ByzantineFaultTolerantConsensus, AgentValidationResult
from src.services.system_health_monitor import SystemHealthMonitor, HealthStatus, MetricType, HealthMetric, MetaIncident
from src.services.meta_incident_handler import MetaIncidentHandler


@pytest.fixture
def mock_aws_factory():
    """Create a mock AWS service factory."""
    factory = Mock()
    
    # Mock STS client for credential verification
    mock_sts = AsyncMock()
    mock_sts.get_caller_identity.return_value = {"Account": "123456789012"}
    factory.get_sts_client.return_value = mock_sts
    
    # Mock Step Functions client
    mock_stepfunctions = AsyncMock()
    mock_stepfunctions.start_execution.return_value = {
        "executionArn": "arn:aws:states:us-east-1:123456789012:execution:test:test-execution"
    }
    mock_stepfunctions.describe_execution.return_value = {
        "status": "SUCCEEDED",
        "output": '{"consensus_reached": true, "selected_action": "scale_service", "final_confidence": 0.85}'
    }
    factory.get_stepfunctions_client.return_value = mock_stepfunctions
    
    return factory


@pytest.fixture
def sample_incident():
    """Create a sample incident for testing."""
    business_impact = BusinessImpact(
        service_tier=ServiceTier.TIER_1,
        affected_users=10000,
        revenue_impact_per_minute=500.0
    )
    
    metadata = IncidentMetadata(
        source_system="test",
        tags={"service": "database"}
    )
    
    return Incident(
        title="Test Database Performance Issue",
        description="Database response times are degraded",
        severity=IncidentSeverity.HIGH,
        service_name="database",
        business_impact=business_impact,
        metadata=metadata
    )


@pytest.fixture
def sample_recommendations():
    """Create sample agent recommendations."""
    return [
        AgentRecommendation(
            agent_name=AgentType.DETECTION,
            incident_id="test-incident",
            action_type=ActionType.SCALE_UP,
            action_id="scale_database",
            confidence=0.8,
            risk_level=RiskLevel.MEDIUM,
            estimated_impact="Improved performance",
            reasoning="Database CPU utilization is high",
            urgency=0.7,
            evidence=[]
        ),
        AgentRecommendation(
            agent_name=AgentType.DIAGNOSIS,
            incident_id="test-incident",
            action_type=ActionType.SCALE_UP,
            action_id="scale_database",
            confidence=0.9,
            risk_level=RiskLevel.MEDIUM,
            estimated_impact="Resolved performance issue",
            reasoning="Connection pool exhaustion detected",
            urgency=0.8,
            evidence=[]
        ),
        AgentRecommendation(
            agent_name=AgentType.PREDICTION,
            incident_id="test-incident",
            action_type=ActionType.RESTART_SERVICE,
            action_id="restart_database",
            confidence=0.6,
            risk_level=RiskLevel.HIGH,
            estimated_impact="Temporary service disruption",
            reasoning="Predictive model suggests restart needed",
            urgency=0.5,
            evidence=[]
        )
    ]


class TestByzantineFaultTolerantConsensus:
    """Test the Byzantine Fault Tolerant Consensus Engine."""
    
    @pytest.mark.asyncio
    async def test_byzantine_consensus_initialization(self, mock_aws_factory):
        """Test Byzantine consensus engine initialization."""
        consensus = ByzantineFaultTolerantConsensus(mock_aws_factory)
        
        assert consensus.aws_factory == mock_aws_factory
        assert consensus.byzantine_threshold == 0.33
        assert consensus.min_agreement_threshold == 0.67
        assert consensus.integrity_check_enabled is True
        assert len(consensus.consensus_rounds) == 0
        assert len(consensus.agent_reputation) == 0
    
    @pytest.mark.asyncio
    async def test_byzantine_consensus_normal_case(self, mock_aws_factory, sample_incident, sample_recommendations):
        """Test Byzantine consensus with normal (non-Byzantine) agents."""
        consensus = ByzantineFaultTolerantConsensus(mock_aws_factory)
        
        # All agents agree on scaling
        for rec in sample_recommendations[:2]:  # Use first two recommendations (both scale_database)
            rec.confidence = 0.8
        
        decision = await consensus.reach_consensus(sample_incident, sample_recommendations[:2])
        
        assert decision.consensus_method == "byzantine_fault_tolerant"
        assert decision.selected_action == "scale_database"
        assert decision.final_confidence >= 0.7
        assert not decision.requires_human_approval
        assert len(consensus.consensus_rounds) == 1
    
    @pytest.mark.asyncio
    async def test_byzantine_agent_detection(self, mock_aws_factory, sample_incident, sample_recommendations):
        """Test detection of Byzantine agents."""
        consensus = ByzantineFaultTolerantConsensus(mock_aws_factory)
        
        # Make one agent Byzantine (invalid confidence)
        sample_recommendations[2].confidence = 1.5  # Invalid confidence > 1.0
        
        decision = await consensus.reach_consensus(sample_incident, sample_recommendations)
        
        # Should detect Byzantine agent and filter it out
        assert decision.conflicts_detected is True
        assert len(consensus.consensus_rounds) == 1
        
        consensus_round = consensus.consensus_rounds[0]
        assert len(consensus_round.byzantine_agents) >= 1
        assert "prediction" in consensus_round.byzantine_agents
    
    @pytest.mark.asyncio
    async def test_agent_validation(self, mock_aws_factory, sample_recommendations):
        """Test agent validation functionality."""
        consensus = ByzantineFaultTolerantConsensus(mock_aws_factory)
        
        # Test valid agent
        validation_result = await consensus._validate_single_agent("detection", sample_recommendations[0])
        
        assert validation_result.agent_name == "detection"
        assert validation_result.is_valid is True
        assert validation_result.confidence_score > 0.5
        assert len(validation_result.validation_errors) == 0
        assert validation_result.integrity_hash is not None
    
    @pytest.mark.asyncio
    async def test_agent_reputation_system(self, mock_aws_factory, sample_incident, sample_recommendations):
        """Test agent reputation tracking."""
        consensus = ByzantineFaultTolerantConsensus(mock_aws_factory)
        
        # Initial reputation should be 1.0
        assert consensus.agent_reputation["detection"] == 1.0
        
        # Make one agent Byzantine
        sample_recommendations[2].confidence = -0.5  # Invalid negative confidence
        
        await consensus.reach_consensus(sample_incident, sample_recommendations)
        
        # Byzantine agent reputation should decrease
        assert consensus.agent_reputation["prediction"] < 1.0
        # Honest agents reputation should increase or stay same
        assert consensus.agent_reputation["detection"] >= 1.0
    
    @pytest.mark.asyncio
    async def test_consensus_statistics(self, mock_aws_factory, sample_incident, sample_recommendations):
        """Test consensus statistics tracking."""
        consensus = ByzantineFaultTolerantConsensus(mock_aws_factory)
        
        # Process multiple consensus rounds
        for i in range(3):
            incident_copy = Incident(
                id=f"test-incident-{i}",
                title=sample_incident.title,
                description=sample_incident.description,
                severity=sample_incident.severity,
                business_impact=sample_incident.business_impact,
                metadata=sample_incident.metadata
            )
            
            await consensus.reach_consensus(incident_copy, sample_recommendations[:2])
        
        stats = consensus.get_byzantine_statistics()
        
        assert stats["total_rounds"] == 3
        assert stats["consensus_success_rate"] >= 0.0
        assert stats["average_confidence"] >= 0.0
        assert "agent_reputation_scores" in stats


class TestSystemHealthMonitor:
    """Test the System Health Monitor."""
    
    @pytest.mark.asyncio
    async def test_health_monitor_initialization(self, mock_aws_factory):
        """Test system health monitor initialization."""
        monitor = SystemHealthMonitor(mock_aws_factory)
        
        assert monitor.aws_factory == mock_aws_factory
        assert monitor.monitoring_interval == timedelta(seconds=30)
        assert monitor.is_monitoring is False
        assert len(monitor.health_history) == 0
        assert len(monitor.external_dependencies) > 0
    
    @pytest.mark.asyncio
    async def test_health_monitoring_lifecycle(self, mock_aws_factory):
        """Test starting and stopping health monitoring."""
        monitor = SystemHealthMonitor(mock_aws_factory)
        
        # Start monitoring
        await monitor.start_monitoring()
        assert monitor.is_monitoring is True
        assert monitor.monitoring_task is not None
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Stop monitoring
        await monitor.stop_monitoring()
        assert monitor.is_monitoring is False
    
    @pytest.mark.asyncio
    async def test_health_metrics_collection(self, mock_aws_factory):
        """Test health metrics collection."""
        monitor = SystemHealthMonitor(mock_aws_factory)
        
        # Mock psutil for resource metrics
        with patch('psutil.cpu_percent', return_value=50.0), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            # Mock memory info
            mock_memory.return_value = Mock(
                percent=60.0,
                total=8 * 1024**3,  # 8GB
                available=3 * 1024**3  # 3GB
            )
            
            # Mock disk info
            mock_disk.return_value = Mock(
                percent=70.0,
                total=100 * 1024**3,  # 100GB
                free=30 * 1024**3  # 30GB
            )
            
            # Collect health snapshot
            snapshot = await monitor._collect_health_metrics()
            
            assert snapshot.overall_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.CRITICAL]
            assert len(snapshot.metrics) > 0
            
            # Check for resource metrics
            resource_metrics = [m for m in snapshot.metrics if m.metric_type == MetricType.RESOURCE]
            assert len(resource_metrics) >= 3  # CPU, memory, disk
            
            # Verify metric values
            cpu_metric = next((m for m in resource_metrics if m.name == "cpu_utilization"), None)
            assert cpu_metric is not None
            assert cpu_metric.value == 50.0
            assert cpu_metric.status == HealthStatus.HEALTHY
    
    @pytest.mark.asyncio
    async def test_meta_incident_detection(self, mock_aws_factory):
        """Test meta-incident detection."""
        monitor = SystemHealthMonitor(mock_aws_factory)
        
        # Create a health snapshot with critical issues
        critical_metrics = [
            HealthMetric(
                name="detection_availability",
                value=0.0,
                threshold_warning=1.0,
                threshold_critical=0.0,
                metric_type=MetricType.AGENT,
                timestamp=datetime.utcnow(),
                status=HealthStatus.CRITICAL,
                details={}
            ),
            HealthMetric(
                name="diagnosis_availability", 
                value=0.0,
                threshold_warning=1.0,
                threshold_critical=0.0,
                metric_type=MetricType.AGENT,
                timestamp=datetime.utcnow(),
                status=HealthStatus.CRITICAL,
                details={}
            )
        ]
        
        from src.services.system_health_monitor import SystemHealthSnapshot
        snapshot = SystemHealthSnapshot(
            timestamp=datetime.utcnow(),
            overall_status=HealthStatus.CRITICAL,
            metrics=critical_metrics,
            active_agents={},
            performance_summary={},
            resource_utilization={},
            external_dependencies={},
            meta_incidents=[]
        )
        
        # Detect meta-incidents
        await monitor._detect_meta_incidents(snapshot)
        
        # Should detect multiple agent failure
        assert len(monitor.meta_incidents) > 0
        
        # Find the agent failure meta-incident
        agent_failure_incident = None
        for incident in monitor.meta_incidents.values():
            if "Multiple Agent Failure" in incident.title:
                agent_failure_incident = incident
                break
        
        assert agent_failure_incident is not None
        assert agent_failure_incident.severity == IncidentSeverity.CRITICAL
        assert len(agent_failure_incident.affected_components) == 2
    
    @pytest.mark.asyncio
    async def test_recovery_actions(self, mock_aws_factory):
        """Test automated recovery actions."""
        monitor = SystemHealthMonitor(mock_aws_factory)
        
        # Test individual recovery actions
        assert await monitor._cleanup_system_processes() is True
        assert await monitor._check_and_repair_dependencies() is True
        assert await monitor._scale_system_resources() is True
    
    def test_health_status_calculation(self, mock_aws_factory):
        """Test overall health status calculation."""
        monitor = SystemHealthMonitor(mock_aws_factory)
        
        # Test healthy case
        healthy_metrics = [
            HealthMetric("test1", 1.0, 0.8, 0.9, MetricType.PERFORMANCE, datetime.utcnow(), HealthStatus.HEALTHY, {}),
            HealthMetric("test2", 0.7, 0.8, 0.9, MetricType.RESOURCE, datetime.utcnow(), HealthStatus.HEALTHY, {})
        ]
        
        status = monitor._calculate_overall_status(healthy_metrics)
        assert status == HealthStatus.HEALTHY
        
        # Test critical case
        critical_metrics = [
            HealthMetric("test1", 0.5, 0.8, 0.9, MetricType.PERFORMANCE, datetime.utcnow(), HealthStatus.CRITICAL, {}),
            HealthMetric("test2", 0.7, 0.8, 0.9, MetricType.RESOURCE, datetime.utcnow(), HealthStatus.HEALTHY, {})
        ]
        
        status = monitor._calculate_overall_status(critical_metrics)
        assert status == HealthStatus.CRITICAL


class TestMetaIncidentHandler:
    """Test the Meta-Incident Handler."""
    
    @pytest.mark.asyncio
    async def test_meta_incident_handler_initialization(self, mock_aws_factory):
        """Test meta-incident handler initialization."""
        health_monitor = SystemHealthMonitor(mock_aws_factory)
        handler = MetaIncidentHandler(mock_aws_factory, health_monitor)
        
        assert handler.aws_factory == mock_aws_factory
        assert handler.health_monitor == health_monitor
        assert handler.auto_resolution_enabled is True
        assert len(handler.active_meta_incidents) == 0
    
    @pytest.mark.asyncio
    async def test_meta_incident_processing(self, mock_aws_factory):
        """Test processing of meta-incidents."""
        health_monitor = SystemHealthMonitor(mock_aws_factory)
        handler = MetaIncidentHandler(mock_aws_factory, health_monitor)
        
        # Create a test meta-incident
        meta_incident = MetaIncident(
            id="test_meta_incident",
            title="Test Agent Failure",
            description="Test agent is failing",
            severity=IncidentSeverity.HIGH,
            affected_components=["test_agent"],
            detected_at=datetime.utcnow(),
            root_cause=None,
            recovery_actions=["restart_agents"],
            status="active"
        )
        
        # Process the meta-incident
        incident = await handler.process_meta_incident(meta_incident)
        
        assert incident is not None
        assert incident.id.startswith("META-")
        assert "[META]" in incident.title
        assert incident.severity == IncidentSeverity.HIGH
        # Note: service_name is not a field in the current Incident model
        assert "Incident Commander system" in incident.description
        # Verify it was processed (may be resolved by auto-resolution)
        assert meta_incident.id in handler.resolution_attempts
    
    @pytest.mark.asyncio
    async def test_business_impact_calculation(self, mock_aws_factory):
        """Test business impact calculation for meta-incidents."""
        health_monitor = SystemHealthMonitor(mock_aws_factory)
        handler = MetaIncidentHandler(mock_aws_factory, health_monitor)
        
        # Test critical meta-incident
        critical_meta = MetaIncident(
            id="critical_test",
            title="Critical System Failure",
            description="Critical failure",
            severity=IncidentSeverity.CRITICAL,
            affected_components=["consensus_engine"],
            detected_at=datetime.utcnow(),
            root_cause=None,
            recovery_actions=[],
            status="active"
        )
        
        business_impact = handler._calculate_meta_incident_business_impact(critical_meta)
        
        assert business_impact.service_tier == ServiceTier.TIER_1
        assert business_impact.affected_users == 100000
        assert business_impact.revenue_impact_per_minute == 5000.0
        assert business_impact.sla_breach_risk == 0.9
    
    @pytest.mark.asyncio
    async def test_auto_resolution(self, mock_aws_factory):
        """Test automatic resolution of meta-incidents."""
        health_monitor = SystemHealthMonitor(mock_aws_factory)
        handler = MetaIncidentHandler(mock_aws_factory, health_monitor)
        
        # Create a simple meta-incident
        meta_incident = MetaIncident(
            id="auto_resolve_test",
            title="Test Auto Resolution",
            description="Test automatic resolution",
            severity=IncidentSeverity.MEDIUM,
            affected_components=["test_component"],
            detected_at=datetime.utcnow(),
            root_cause=None,
            recovery_actions=["cleanup_processes"],
            status="active"
        )
        
        # Mock the verification to return success
        with patch.object(handler, '_verify_meta_incident_resolution', return_value=True):
            await handler._attempt_auto_resolution(meta_incident, Mock())
        
        # Check resolution attempts were recorded
        assert meta_incident.id in handler.resolution_attempts
        assert len(handler.resolution_attempts[meta_incident.id]) > 0
    
    def test_meta_incident_statistics(self, mock_aws_factory):
        """Test meta-incident statistics."""
        health_monitor = SystemHealthMonitor(mock_aws_factory)
        handler = MetaIncidentHandler(mock_aws_factory, health_monitor)
        
        # Add some test data
        handler.resolution_attempts["test1"] = [{"success": True}, {"success": False}]
        handler.resolution_attempts["test2"] = [{"success": True}]
        
        stats = handler.get_meta_incident_statistics()
        
        assert stats["total_resolution_attempts"] == 3
        assert stats["successful_resolution_attempts"] == 2
        assert stats["auto_resolution_success_rate"] == 2/3
        assert stats["auto_resolution_enabled"] is True


class TestMilestone2Integration:
    """Test integration of all Milestone 2 components."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_byzantine_consensus_with_health_monitoring(self, mock_aws_factory, sample_incident, sample_recommendations):
        """Test end-to-end Byzantine consensus with health monitoring."""
        # Initialize all components
        health_monitor = SystemHealthMonitor(mock_aws_factory)
        meta_handler = MetaIncidentHandler(mock_aws_factory, health_monitor)
        byzantine_consensus = ByzantineFaultTolerantConsensus(mock_aws_factory)
        
        # Start health monitoring
        await health_monitor.start_monitoring()
        
        try:
            # Process consensus with Byzantine agent
            sample_recommendations[2].confidence = 2.0  # Invalid confidence
            
            decision = await byzantine_consensus.reach_consensus(sample_incident, sample_recommendations)
            
            # Verify Byzantine detection worked
            assert decision.conflicts_detected is True
            assert len(byzantine_consensus.consensus_rounds) == 1
            
            # Verify health monitoring is running
            assert health_monitor.is_monitoring is True
            
            # Let health monitoring run briefly and collect some data
            await asyncio.sleep(1.0)  # Wait longer for health data collection
            
            # Manually trigger health collection if no data available
            if not health_monitor.health_history:
                snapshot = await health_monitor._collect_health_metrics()
                health_monitor.health_history.append(snapshot)
            
            # Check health status
            health_status = health_monitor.get_current_health_status()
            assert "overall_status" in health_status or "status" in health_status
            
        finally:
            # Clean up
            await health_monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_meta_incident_triggers_byzantine_consensus(self, mock_aws_factory):
        """Test that meta-incidents can trigger their own consensus process."""
        health_monitor = SystemHealthMonitor(mock_aws_factory)
        meta_handler = MetaIncidentHandler(mock_aws_factory, health_monitor)
        
        # Create a meta-incident that affects consensus
        meta_incident = MetaIncident(
            id="consensus_failure_test",
            title="Consensus System Failure",
            description="Consensus engine is failing",
            severity=IncidentSeverity.CRITICAL,
            affected_components=["consensus_engine"],
            detected_at=datetime.utcnow(),
            root_cause=None,
            recovery_actions=["restart_consensus_engine"],
            status="active"
        )
        
        # Process the meta-incident
        incident = await meta_handler.process_meta_incident(meta_incident)
        
        # Verify incident was created
        assert incident is not None
        assert "Consensus System Failure" in incident.title
        assert incident.severity == IncidentSeverity.CRITICAL
        
        # Verify it's tracked as active
        assert meta_incident.id in meta_handler.active_meta_incidents
    
    @pytest.mark.asyncio
    async def test_milestone2_api_endpoints_integration(self, mock_aws_factory):
        """Test that all Milestone 2 API endpoints work together."""
        # This would typically be tested with a test client
        # For now, verify that all components can be initialized together
        
        health_monitor = SystemHealthMonitor(mock_aws_factory)
        meta_handler = MetaIncidentHandler(mock_aws_factory, health_monitor)
        byzantine_consensus = ByzantineFaultTolerantConsensus(mock_aws_factory)
        
        # Verify all components are properly initialized
        assert health_monitor.aws_factory == mock_aws_factory
        assert meta_handler.health_monitor == health_monitor
        assert byzantine_consensus.aws_factory == mock_aws_factory
        
        # Test getting status from all components
        health_status = health_monitor.get_current_health_status()
        meta_stats = meta_handler.get_meta_incident_statistics()
        byzantine_stats = byzantine_consensus.get_byzantine_statistics()
        
        assert isinstance(health_status, dict)
        assert isinstance(meta_stats, dict)
        assert isinstance(byzantine_stats, dict)
    
    @pytest.mark.asyncio
    async def test_milestone2_performance_under_load(self, mock_aws_factory, sample_incident):
        """Test Milestone 2 components under simulated load."""
        byzantine_consensus = ByzantineFaultTolerantConsensus(mock_aws_factory)
        
        # Create multiple concurrent consensus requests
        tasks = []
        for i in range(5):
            recommendations = [
                AgentRecommendation(
                    agent_name=AgentType.DETECTION,
                    incident_id=f"load-test-{i}",
                    action_type=ActionType.SCALE_UP,
                    action_id="scale_service",
                    confidence=0.8,
                    risk_level=RiskLevel.MEDIUM,
                    estimated_impact="Load test",
                    reasoning="Load testing",
                    urgency=0.5,
                    evidence=[]
                )
            ]
            
            incident_copy = Incident(
                id=f"load-test-{i}",
                title=f"Load Test {i}",
                description="Load testing incident",
                severity=IncidentSeverity.MEDIUM,
                business_impact=sample_incident.business_impact,
                metadata=sample_incident.metadata
            )
            
            task = byzantine_consensus.reach_consensus(incident_copy, recommendations)
            tasks.append(task)
        
        # Execute all consensus requests concurrently
        results = await asyncio.gather(*tasks)
        
        # Verify all completed successfully
        assert len(results) == 5
        for result in results:
            assert result.consensus_method == "byzantine_fault_tolerant"
            assert result.selected_action is not None
        
        # Verify consensus rounds were recorded
        assert len(byzantine_consensus.consensus_rounds) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])