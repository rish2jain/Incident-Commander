"""
Unit tests for the comprehensive monitoring system.

Tests integration monitoring, guardrail tracking, and agent telemetry components.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from src.services.integration_monitor import (
    IntegrationMonitor, ServiceStatus, IntegrationType, ServiceHealthMetrics
)
from src.services.guardrail_tracker import (
    GuardrailTracker, GuardrailEvent, GuardrailType, GuardrailDecision, GuardrailSeverity
)
from src.services.agent_telemetry import (
    AgentTelemetryCollector, TelemetryEvent, TelemetryEventType, PerformanceCategory
)
from src.models.agent import AgentType

# Mark all tests in this module as async
pytestmark = pytest.mark.asyncio


class TestIntegrationMonitor:
    """Test cases for IntegrationMonitor."""
    
    @pytest.fixture
    def monitor(self):
        """Create IntegrationMonitor instance for testing."""
        return IntegrationMonitor()
    
    @pytest.fixture
    def mock_aws_clients(self):
        """Mock AWS clients for testing."""
        return {
            "bedrock": MagicMock(),
            "dynamodb": MagicMock(),
            "s3": MagicMock(),
            "lambda": MagicMock(),
            "cloudwatch": MagicMock(),
        }
    
    async def test_monitor_initialization(self, monitor):
        """Test monitor initializes correctly."""
        assert not monitor.monitoring_active
        assert len(monitor.health_metrics) == 0
        assert monitor.monitoring_interval.total_seconds() == 30  # Default from config
    
    async def test_start_stop_monitoring(self, monitor):
        """Test starting and stopping monitoring."""
        await monitor.start_monitoring()
        assert monitor.monitoring_active
        
        await monitor.stop_monitoring()
        assert not monitor.monitoring_active
    
    @patch('boto3.Session')
    async def test_aws_client_initialization(self, mock_session, monitor):
        """Test AWS client initialization."""
        mock_session.return_value.client.return_value = MagicMock()
        
        monitor._initialize_aws_clients()
        
        # Should have initialized multiple AWS service clients
        assert len(monitor._aws_clients) > 0
        assert "bedrock" in monitor._aws_clients
        assert "dynamodb" in monitor._aws_clients
    
    async def test_bedrock_health_check_success(self, monitor):
        """Test successful Bedrock health check."""
        # Mock Bedrock client
        mock_client = MagicMock()
        mock_client.list_foundation_models.return_value = {
            "modelSummaries": [
                {"modelId": "anthropic.claude-3-sonnet-20240229-v1:0"}
            ]
        }
        monitor._aws_clients["bedrock"] = mock_client
        
        await monitor._check_bedrock_health()
        
        # Should have recorded healthy status
        assert "bedrock" in monitor.health_metrics
        metrics = monitor.health_metrics["bedrock"]
        assert metrics.status == ServiceStatus.HEALTHY
        assert metrics.integration_type == IntegrationType.BEDROCK
    
    async def test_bedrock_health_check_failure(self, monitor):
        """Test Bedrock health check failure."""
        # Mock Bedrock client that raises exception
        mock_client = MagicMock()
        mock_client.list_foundation_models.side_effect = Exception("Connection failed")
        monitor._aws_clients["bedrock"] = mock_client
        
        await monitor._check_bedrock_health()
        
        # Should have recorded unhealthy status
        assert "bedrock" in monitor.health_metrics
        metrics = monitor.health_metrics["bedrock"]
        assert metrics.status == ServiceStatus.UNHEALTHY
        assert "Connection failed" in metrics.error_details
    
    async def test_service_health_metrics_update(self, monitor):
        """Test service health metrics update."""
        monitor._update_service_metrics(
            service_name="test_service",
            integration_type=IntegrationType.DYNAMODB,
            status=ServiceStatus.HEALTHY,
            response_time_ms=50.0,
            error_rate=0.0
        )
        
        assert "test_service" in monitor.health_metrics
        metrics = monitor.health_metrics["test_service"]
        assert metrics.service_name == "test_service"
        assert metrics.status == ServiceStatus.HEALTHY
        assert metrics.response_time_ms == 50.0
        assert metrics.availability == 100.0
    
    async def test_integration_health_report(self, monitor):
        """Test integration health report generation."""
        # Add some test metrics
        monitor._update_service_metrics(
            "service1", IntegrationType.BEDROCK, ServiceStatus.HEALTHY, 100.0, 0.0
        )
        monitor._update_service_metrics(
            "service2", IntegrationType.DYNAMODB, ServiceStatus.DEGRADED, 200.0, 0.1
        )
        monitor._update_service_metrics(
            "service3", IntegrationType.S3, ServiceStatus.UNHEALTHY, 500.0, 0.5
        )
        
        report = await monitor.get_integration_health_report()
        
        assert report.total_services == 3
        assert report.healthy_services == 1
        assert report.degraded_services == 1
        assert report.unhealthy_services == 1
        assert report.overall_status == ServiceStatus.UNHEALTHY
    
    async def test_unhealthy_services_filter(self, monitor):
        """Test filtering of unhealthy services."""
        monitor._update_service_metrics(
            "healthy_service", IntegrationType.BEDROCK, ServiceStatus.HEALTHY, 100.0, 0.0
        )
        monitor._update_service_metrics(
            "degraded_service", IntegrationType.DYNAMODB, ServiceStatus.DEGRADED, 200.0, 0.1
        )
        monitor._update_service_metrics(
            "unhealthy_service", IntegrationType.S3, ServiceStatus.UNHEALTHY, 500.0, 0.5
        )
        
        unhealthy_services = await monitor.get_unhealthy_services()
        
        assert len(unhealthy_services) == 2
        service_names = [svc.service_name for svc in unhealthy_services]
        assert "degraded_service" in service_names
        assert "unhealthy_service" in service_names
        assert "healthy_service" not in service_names
    
    async def test_diagnostic_report_generation(self, monitor):
        """Test diagnostic report generation."""
        # Add test service with issues
        monitor._update_service_metrics(
            "problematic_service", IntegrationType.BEDROCK, ServiceStatus.DEGRADED, 
            2000.0, 0.1, "High response time"
        )
        
        # Test single service diagnostic
        report = await monitor.generate_diagnostic_report("problematic_service")
        
        assert report["service"] == "problematic_service"
        assert report["status"] == "degraded"
        assert "High response time" in report["diagnostics"]["error_details"]
        
        # Test system-wide diagnostic
        system_report = await monitor.generate_diagnostic_report()
        
        assert "system_diagnostic" in system_report
        assert system_report["system_diagnostic"]["unhealthy_services_count"] == 1


class TestGuardrailTracker:
    """Test cases for GuardrailTracker."""
    
    @pytest.fixture
    def tracker(self):
        """Create GuardrailTracker instance for testing."""
        return GuardrailTracker()
    
    @pytest.fixture
    def sample_guardrail_event(self):
        """Create sample guardrail event for testing."""
        return GuardrailEvent(
            id="test-event-123",
            timestamp=datetime.utcnow(),
            guardrail_type=GuardrailType.CONTENT_FILTER,
            guardrail_name="content_safety",
            decision=GuardrailDecision.BLOCK,
            severity=GuardrailSeverity.HIGH,
            agent_name="test_agent",
            incident_id="incident-123",
            confidence_score=0.95,
            reasoning="Detected harmful content",
            processing_time_ms=150.0
        )
    
    async def test_tracker_initialization(self, tracker):
        """Test tracker initializes correctly."""
        assert not tracker.tracking_active
        assert len(tracker.events) == 0
        assert len(tracker.metrics) == 0
    
    async def test_start_stop_tracking(self, tracker):
        """Test starting and stopping tracking."""
        await tracker.start_tracking()
        assert tracker.tracking_active
        
        await tracker.stop_tracking()
        assert not tracker.tracking_active
    
    async def test_record_guardrail_event(self, tracker, sample_guardrail_event):
        """Test recording guardrail events."""
        await tracker.start_tracking()
        await tracker.record_guardrail_event(sample_guardrail_event)
        
        assert len(tracker.events) == 1
        assert tracker.events[0].id == "test-event-123"
        
        # Check metrics were updated
        assert "content_safety" in tracker.metrics
        metrics = tracker.metrics["content_safety"]
        assert metrics.total_events == 1
        assert metrics.block_count == 1
    
    async def test_guardrail_metrics_calculation(self, tracker):
        """Test guardrail metrics calculation."""
        await tracker.start_tracking()
        
        # Record multiple events
        for i in range(10):
            event = GuardrailEvent(
                id=f"event-{i}",
                timestamp=datetime.utcnow(),
                guardrail_type=GuardrailType.CONTENT_FILTER,
                guardrail_name="test_guardrail",
                decision=GuardrailDecision.BLOCK if i < 3 else GuardrailDecision.ALLOW,
                severity=GuardrailSeverity.MEDIUM,
                processing_time_ms=100.0 + i * 10
            )
            await tracker.record_guardrail_event(event)
        
        metrics = tracker.metrics["test_guardrail"]
        assert metrics.total_events == 10
        assert metrics.block_count == 3
        assert metrics.allow_count == 7
        assert metrics.calculate_block_rate() == 30.0  # 3/10 * 100
    
    async def test_recent_events_filtering(self, tracker):
        """Test filtering of recent events."""
        await tracker.start_tracking()
        
        # Add events with different timestamps
        old_event = GuardrailEvent(
            id="old-event",
            timestamp=datetime.utcnow() - timedelta(hours=25),
            guardrail_type=GuardrailType.CONTENT_FILTER,
            guardrail_name="test_guardrail",
            decision=GuardrailDecision.BLOCK,
            severity=GuardrailSeverity.HIGH
        )
        
        recent_event = GuardrailEvent(
            id="recent-event",
            timestamp=datetime.utcnow(),
            guardrail_type=GuardrailType.CONTENT_FILTER,
            guardrail_name="test_guardrail",
            decision=GuardrailDecision.ALLOW,
            severity=GuardrailSeverity.LOW
        )
        
        await tracker.record_guardrail_event(old_event)
        await tracker.record_guardrail_event(recent_event)
        
        # Get recent events (last 24 hours)
        recent_events = await tracker.get_recent_events(hours=24)
        
        assert len(recent_events) == 1
        assert recent_events[0].id == "recent-event"
    
    async def test_compliance_analytics(self, tracker):
        """Test compliance analytics generation."""
        await tracker.start_tracking()
        
        # Add test events
        for i in range(5):
            event = GuardrailEvent(
                id=f"event-{i}",
                timestamp=datetime.utcnow(),
                guardrail_type=GuardrailType.CONTENT_FILTER,
                guardrail_name="test_guardrail",
                decision=GuardrailDecision.ALLOW if i < 4 else GuardrailDecision.BLOCK,
                severity=GuardrailSeverity.MEDIUM
            )
            await tracker.record_guardrail_event(event)
        
        analytics = await tracker.get_compliance_analytics()
        
        assert "summary" in analytics
        assert analytics["summary"]["total_events_24h"] == 5
        assert analytics["summary"]["compliance_rate_24h"] == 80.0  # 4/5 * 100
    
    async def test_compliance_report_generation(self, tracker):
        """Test compliance report generation."""
        await tracker.start_tracking()
        
        # Add test events with policy violations
        violation_event = GuardrailEvent(
            id="violation-event",
            timestamp=datetime.utcnow(),
            guardrail_type=GuardrailType.COMPLIANCE_POLICY,
            guardrail_name="compliance_check",
            decision=GuardrailDecision.BLOCK,
            severity=GuardrailSeverity.HIGH,
            policy_violated="data_protection_policy"
        )
        
        await tracker.record_guardrail_event(violation_event)
        
        report = await tracker.generate_compliance_report(period_days=1)
        
        assert report.total_events == 1
        assert report.total_violations == 1
        assert report.compliance_rate == 0.0  # 100% violations
        assert len(report.policy_violations) == 1
        assert report.policy_violations[0]["policy"] == "data_protection_policy"


class TestAgentTelemetryCollector:
    """Test cases for AgentTelemetryCollector."""
    
    @pytest.fixture
    def telemetry(self):
        """Create AgentTelemetryCollector instance for testing."""
        return AgentTelemetryCollector()
    
    async def test_telemetry_initialization(self, telemetry):
        """Test telemetry collector initializes correctly."""
        assert not telemetry.collection_active
        assert len(telemetry.events) == 0
        assert len(telemetry.active_sessions) == 0
    
    async def test_start_stop_collection(self, telemetry):
        """Test starting and stopping telemetry collection."""
        await telemetry.start_collection()
        assert telemetry.collection_active
        
        await telemetry.stop_collection()
        assert not telemetry.collection_active
    
    async def test_agent_session_tracking(self, telemetry):
        """Test agent execution session tracking."""
        await telemetry.start_collection()
        
        # Start agent session
        session_id = await telemetry.record_agent_start(
            agent_name="test_agent",
            agent_type=AgentType.DETECTION,
            incident_id="incident-123"
        )
        
        assert session_id in telemetry.active_sessions
        assert len(telemetry.events) == 1
        
        # Complete agent session
        await telemetry.record_agent_complete(
            session_id=session_id,
            success=True,
            confidence_score=0.85,
            memory_usage_mb=256.0,
            cpu_usage_percent=45.0
        )
        
        assert session_id not in telemetry.active_sessions
        assert len(telemetry.events) == 2
        
        # Check completion event
        completion_event = telemetry.events[-1]
        assert completion_event.event_type == TelemetryEventType.AGENT_COMPLETE
        assert completion_event.success is True
        assert completion_event.confidence_score == 0.85
    
    async def test_agent_error_recording(self, telemetry):
        """Test agent error event recording."""
        await telemetry.start_collection()
        
        await telemetry.record_agent_error(
            agent_name="test_agent",
            agent_type=AgentType.DIAGNOSIS,
            error_message="Connection timeout",
            incident_id="incident-123"
        )
        
        assert len(telemetry.events) == 1
        error_event = telemetry.events[0]
        assert error_event.event_type == TelemetryEventType.AGENT_ERROR
        assert error_event.success is False
        assert error_event.error_message == "Connection timeout"
    
    async def test_consensus_event_recording(self, telemetry):
        """Test consensus event recording."""
        await telemetry.start_collection()
        
        await telemetry.record_consensus_event(
            event_type=TelemetryEventType.CONSENSUS_COMPLETE,
            participating_agents=["agent1", "agent2", "agent3"],
            duration_ms=500.0,
            success=True,
            incident_id="incident-123"
        )
        
        assert len(telemetry.events) == 1
        consensus_event = telemetry.events[0]
        assert consensus_event.event_type == TelemetryEventType.CONSENSUS_COMPLETE
        assert consensus_event.metadata["participating_agents"] == ["agent1", "agent2", "agent3"]
    
    async def test_agent_performance_analysis(self, telemetry):
        """Test agent performance analysis."""
        await telemetry.start_collection()
        
        # Simulate multiple agent executions
        for i in range(10):
            session_id = await telemetry.record_agent_start(
                agent_name="test_agent",
                agent_type=AgentType.DETECTION
            )
            
            await telemetry.record_agent_complete(
                session_id=session_id,
                success=i < 8,  # 80% success rate
                confidence_score=0.8 + (i * 0.02),
                memory_usage_mb=200.0 + (i * 10),
                cpu_usage_percent=30.0 + (i * 2)
            )
        
        # Analyze performance
        analyses = await telemetry.analyze_agent_performance(
            agent_name="test_agent",
            hours=1
        )
        
        assert "test_agent" in analyses
        analysis = analyses["test_agent"]
        
        assert analysis.total_executions == 10
        assert analysis.successful_executions == 8
        assert analysis.success_rate == 0.8
        assert analysis.performance_category in [
            PerformanceCategory.GOOD, PerformanceCategory.ACCEPTABLE
        ]
    
    async def test_performance_categorization(self, telemetry):
        """Test performance categorization logic."""
        # Test excellent performance
        category = telemetry._categorize_performance(
            success_rate=0.99,
            average_duration_ms=500,
            agent_type=AgentType.DETECTION
        )
        assert category == PerformanceCategory.EXCELLENT
        
        # Test poor performance
        category = telemetry._categorize_performance(
            success_rate=0.85,
            average_duration_ms=5000,
            agent_type=AgentType.DETECTION
        )
        assert category == PerformanceCategory.POOR
        
        # Test critical performance
        category = telemetry._categorize_performance(
            success_rate=0.75,
            average_duration_ms=10000,
            agent_type=AgentType.DETECTION
        )
        assert category == PerformanceCategory.CRITICAL
    
    async def test_system_performance_report(self, telemetry):
        """Test system-wide performance report generation."""
        await telemetry.start_collection()
        
        # Add some test data
        for agent_name in ["agent1", "agent2"]:
            for i in range(5):
                session_id = await telemetry.record_agent_start(
                    agent_name=agent_name,
                    agent_type=AgentType.DETECTION
                )
                
                await telemetry.record_agent_complete(
                    session_id=session_id,
                    success=True,
                    confidence_score=0.9
                )
        
        report = await telemetry.generate_system_performance_report(hours=1)
        
        assert report.total_agents >= 2
        assert report.active_agents == 2
        assert report.total_executions == 10
        assert report.system_success_rate == 1.0
        assert len(report.agent_analyses) == 2
    
    async def test_optimization_recommendations(self, telemetry):
        """Test optimization recommendation generation."""
        recommendations = telemetry._generate_optimization_recommendations(
            agent_name="slow_agent",
            agent_type=AgentType.DETECTION,
            success_rate=0.85,  # Below 90%
            average_duration_ms=45000,  # Above target
            average_memory_mb=600,  # High memory
            average_cpu_percent=85  # High CPU
        )
        
        assert len(recommendations) > 0
        assert any("success rate" in rec.lower() for rec in recommendations)
        assert any("response time" in rec.lower() for rec in recommendations)
        assert any("memory" in rec.lower() for rec in recommendations)
        assert any("cpu" in rec.lower() for rec in recommendations)
    
    async def test_performance_trend_analysis(self, telemetry):
        """Test performance trend analysis."""
        # Create events with improving performance
        events = []
        for i in range(20):
            event = TelemetryEvent(
                id=f"event-{i}",
                timestamp=datetime.utcnow(),
                event_type=TelemetryEventType.AGENT_COMPLETE,
                agent_name="test_agent",
                agent_type=AgentType.DETECTION,
                duration_ms=1000 - (i * 20),  # Decreasing duration (improving)
                success=True
            )
            events.append(event)
        
        trend = telemetry._analyze_performance_trend(events)
        assert trend == "improving"
        
        # Create events with degrading performance
        events = []
        for i in range(20):
            event = TelemetryEvent(
                id=f"event-{i}",
                timestamp=datetime.utcnow(),
                event_type=TelemetryEventType.AGENT_COMPLETE,
                agent_name="test_agent",
                agent_type=AgentType.DETECTION,
                duration_ms=500 + (i * 50),  # Increasing duration (degrading)
                success=i < 15  # Decreasing success rate
            )
            events.append(event)
        
        trend = telemetry._analyze_performance_trend(events)
        assert trend == "degrading"


class TestMonitoringIntegration:
    """Integration tests for monitoring system components."""
    
    @pytest.fixture
    async def monitoring_system(self):
        """Create integrated monitoring system for testing."""
        integration_monitor = IntegrationMonitor()
        guardrail_tracker = GuardrailTracker()
        agent_telemetry = AgentTelemetryCollector()
        
        # Start all monitoring components
        await integration_monitor.start_monitoring()
        await guardrail_tracker.start_tracking()
        await agent_telemetry.start_collection()
        
        return {
            "integration_monitor": integration_monitor,
            "guardrail_tracker": guardrail_tracker,
            "agent_telemetry": agent_telemetry
        }
    
    async def test_monitoring_system_startup(self, monitoring_system):
        """Test that all monitoring components start correctly."""
        assert monitoring_system["integration_monitor"].monitoring_active
        assert monitoring_system["guardrail_tracker"].tracking_active
        assert monitoring_system["agent_telemetry"].collection_active
    
    async def test_cross_component_data_flow(self, monitoring_system):
        """Test data flow between monitoring components."""
        integration_monitor = monitoring_system["integration_monitor"]
        guardrail_tracker = monitoring_system["guardrail_tracker"]
        agent_telemetry = monitoring_system["agent_telemetry"]
        
        # Simulate agent execution with guardrail check
        session_id = await agent_telemetry.record_agent_start(
            agent_name="test_agent",
            agent_type=AgentType.DETECTION,
            incident_id="incident-123"
        )
        
        # Simulate guardrail event during agent execution
        guardrail_event = GuardrailEvent(
            id="guardrail-event-123",
            timestamp=datetime.utcnow(),
            guardrail_type=GuardrailType.CONTENT_FILTER,
            guardrail_name="content_safety",
            decision=GuardrailDecision.ALLOW,
            severity=GuardrailSeverity.LOW,
            agent_name="test_agent",
            incident_id="incident-123"
        )
        
        await guardrail_tracker.record_guardrail_event(guardrail_event)
        
        # Complete agent execution
        await agent_telemetry.record_agent_complete(
            session_id=session_id,
            success=True,
            confidence_score=0.9
        )
        
        # Verify data was recorded in all systems
        assert len(agent_telemetry.events) >= 2  # Start and complete events
        assert len(guardrail_tracker.events) == 1
        
        # Verify cross-references
        telemetry_events = [e for e in agent_telemetry.events if e.incident_id == "incident-123"]
        assert len(telemetry_events) >= 2
        
        guardrail_events = await guardrail_tracker.get_recent_events(hours=1)
        assert len(guardrail_events) == 1
        assert guardrail_events[0].incident_id == "incident-123"
    
    async def test_monitoring_performance_impact(self, monitoring_system):
        """Test that monitoring has minimal performance impact."""
        agent_telemetry = monitoring_system["agent_telemetry"]
        
        # Measure time for multiple operations
        start_time = datetime.utcnow()
        
        # Simulate high-frequency operations
        for i in range(100):
            session_id = await agent_telemetry.record_agent_start(
                agent_name=f"agent_{i % 5}",
                agent_type=AgentType.DETECTION
            )
            
            await agent_telemetry.record_agent_complete(
                session_id=session_id,
                success=True
            )
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete 200 operations (100 start + 100 complete) in reasonable time
        assert duration < 5.0  # Less than 5 seconds
        assert len(agent_telemetry.events) == 200
    
    async def test_monitoring_memory_management(self, monitoring_system):
        """Test memory management in monitoring components."""
        agent_telemetry = monitoring_system["agent_telemetry"]
        guardrail_tracker = monitoring_system["guardrail_tracker"]
        
        # Fill up to memory limits
        max_events = agent_telemetry.max_events_in_memory
        
        # Add more events than the limit
        for i in range(max_events + 100):
            session_id = await agent_telemetry.record_agent_start(
                agent_name="test_agent",
                agent_type=AgentType.DETECTION
            )
            
            await agent_telemetry.record_agent_complete(
                session_id=session_id,
                success=True
            )
        
        # Should not exceed memory limit
        assert len(agent_telemetry.events) <= max_events
        
        # Similar test for guardrail tracker
        max_guardrail_events = guardrail_tracker.max_events_in_memory
        
        for i in range(max_guardrail_events + 50):
            event = GuardrailEvent(
                id=f"event-{i}",
                timestamp=datetime.utcnow(),
                guardrail_type=GuardrailType.CONTENT_FILTER,
                guardrail_name="test_guardrail",
                decision=GuardrailDecision.ALLOW,
                severity=GuardrailSeverity.LOW
            )
            await guardrail_tracker.record_guardrail_event(event)
        
        assert len(guardrail_tracker.events) <= max_guardrail_events