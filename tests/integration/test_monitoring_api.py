"""
Integration tests for monitoring API endpoints.

Tests the FastAPI monitoring routes and their integration with monitoring services.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.routers.monitoring import router as monitoring_router
from src.services.integration_monitor import ServiceStatus, IntegrationType
from src.services.guardrail_tracker import GuardrailType, GuardrailDecision, GuardrailSeverity
from src.services.agent_telemetry import TelemetryEventType, PerformanceCategory
from src.models.agent import AgentType


@pytest.fixture
def app():
    """Create FastAPI app with monitoring router for testing."""
    app = FastAPI()
    app.include_router(monitoring_router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_integration_monitor():
    """Mock integration monitor for testing."""
    from src.services.integration_monitor import IntegrationMonitor, IntegrationHealthReport, ServiceHealthMetrics
    
    monitor = AsyncMock(spec=IntegrationMonitor)
    monitor.monitoring_active = True
    
    # Mock health report
    mock_report = MagicMock(spec=IntegrationHealthReport)
    mock_report.timestamp = datetime.utcnow()
    mock_report.overall_status = ServiceStatus.HEALTHY
    mock_report.healthy_services = 5
    mock_report.degraded_services = 1
    mock_report.unhealthy_services = 0
    mock_report.total_services = 6
    mock_report.system_uptime = 99.5
    mock_report.performance_summary = {
        "average_response_time_ms": 150.0,
        "average_availability": 99.2
    }
    
    monitor.get_integration_health_report = AsyncMock(return_value=mock_report)
    monitor.start_monitoring = AsyncMock()
    
    # Mock service health
    mock_service_health = MagicMock(spec=ServiceHealthMetrics)
    mock_service_health.service_name = "bedrock"
    mock_service_health.integration_type = IntegrationType.BEDROCK
    mock_service_health.status = ServiceStatus.HEALTHY
    mock_service_health.response_time_ms = 120.0
    mock_service_health.error_rate = 0.0
    mock_service_health.availability = 99.8
    mock_service_health.last_check = datetime.utcnow()
    mock_service_health.error_details = None
    mock_service_health.performance_trend = [100, 110, 120, 115, 120]
    mock_service_health.uptime_percentage = 99.8
    
    monitor.get_service_health = AsyncMock(return_value=mock_service_health)
    monitor.get_unhealthy_services = AsyncMock(return_value=[])
    monitor.generate_diagnostic_report = AsyncMock(return_value={
        "service": "bedrock",
        "status": "healthy",
        "diagnostics": {"response_time_ms": 120.0}
    })
    
    return monitor


@pytest.fixture
def mock_guardrail_tracker():
    """Mock guardrail tracker for testing."""
    from src.services.guardrail_tracker import GuardrailTracker, GuardrailMetrics, GuardrailEvent
    
    tracker = AsyncMock(spec=GuardrailTracker)
    tracker.tracking_active = True
    
    # Mock metrics
    mock_metrics = MagicMock(spec=GuardrailMetrics)
    mock_metrics.guardrail_name = "content_safety"
    mock_metrics.guardrail_type = GuardrailType.CONTENT_FILTER
    mock_metrics.total_events = 100
    mock_metrics.allow_count = 95
    mock_metrics.block_count = 5
    mock_metrics.warn_count = 0
    mock_metrics.escalate_count = 0
    mock_metrics.modify_count = 0
    mock_metrics.average_processing_time_ms = 150.0
    mock_metrics.calculate_block_rate = MagicMock(return_value=5.0)
    mock_metrics.calculate_escalation_rate = MagicMock(return_value=0.0)
    
    tracker.get_guardrail_metrics = AsyncMock(return_value={"content_safety": mock_metrics})
    tracker.start_tracking = AsyncMock()
    
    # Mock events
    mock_event = MagicMock(spec=GuardrailEvent)
    mock_event.to_dict = MagicMock(return_value={
        "id": "event-123",
        "timestamp": datetime.utcnow().isoformat(),
        "guardrail_type": "content_filter",
        "decision": "allow"
    })
    
    tracker.get_recent_events = AsyncMock(return_value=[mock_event])
    
    # Mock analytics
    tracker.get_compliance_analytics = AsyncMock(return_value={
        "summary": {
            "total_events_24h": 100,
            "compliance_rate_24h": 95.0,
            "active_guardrails": 5
        },
        "decisions_breakdown_24h": {
            "allow": 95,
            "block": 5,
            "warn": 0,
            "escalate": 0,
            "modify": 0
        }
    })
    
    # Mock compliance report
    from src.services.guardrail_tracker import ComplianceReport
    mock_report = MagicMock(spec=ComplianceReport)
    mock_report.report_id = "compliance-20241018-120000"
    mock_report.generated_at = datetime.utcnow()
    mock_report.period_start = datetime.utcnow() - timedelta(days=7)
    mock_report.period_end = datetime.utcnow()
    mock_report.total_events = 700
    mock_report.total_violations = 35
    mock_report.compliance_rate = 95.0
    mock_report.events_by_type = {"content_filter": 500, "safety_check": 200}
    mock_report.violations_by_severity = {"high": 10, "medium": 15, "low": 10}
    mock_report.policy_violations = []
    mock_report.top_violated_policies = []
    mock_report.recommendations = ["Continue monitoring current policies"]
    
    tracker.generate_compliance_report = AsyncMock(return_value=mock_report)
    
    return tracker


@pytest.fixture
def mock_agent_telemetry():
    """Mock agent telemetry collector for testing."""
    from src.services.agent_telemetry import AgentTelemetryCollector, AgentPerformanceAnalysis, SystemPerformanceReport, TelemetryEvent
    
    telemetry = AsyncMock(spec=AgentTelemetryCollector)
    telemetry.collection_active = True
    
    # Mock performance analysis
    mock_analysis = MagicMock(spec=AgentPerformanceAnalysis)
    mock_analysis.agent_name = "detection_agent"
    mock_analysis.agent_type = AgentType.DETECTION
    mock_analysis.total_executions = 50
    mock_analysis.success_rate = 0.96
    mock_analysis.error_rate = 0.04
    mock_analysis.average_duration_ms = 1200.0
    mock_analysis.median_duration_ms = 1100.0
    mock_analysis.p95_duration_ms = 1800.0
    mock_analysis.performance_category = PerformanceCategory.GOOD
    mock_analysis.performance_trend = "stable"
    mock_analysis.optimization_recommendations = ["Consider caching frequently accessed data"]
    mock_analysis.calculate_efficiency_score = MagicMock(return_value=85.5)
    
    telemetry.analyze_agent_performance = AsyncMock(return_value={"detection_agent": mock_analysis})
    telemetry.start_collection = AsyncMock()
    
    # Mock system performance report
    mock_system_report = MagicMock(spec=SystemPerformanceReport)
    mock_system_report.generated_at = datetime.utcnow()
    mock_system_report.total_agents = 5
    mock_system_report.active_agents = 4
    mock_system_report.total_executions = 200
    mock_system_report.system_success_rate = 0.94
    mock_system_report.consensus_success_rate = 0.98
    mock_system_report.escalation_rate = 0.05
    mock_system_report.performance_trends = {"detection_agent": "stable", "diagnosis_agent": "improving"}
    mock_system_report.bottlenecks = ["High memory usage in diagnosis agent"]
    mock_system_report.system_recommendations = ["Optimize memory usage", "Consider load balancing"]
    
    telemetry.generate_system_performance_report = AsyncMock(return_value=mock_system_report)
    
    # Mock telemetry events
    mock_event = MagicMock(spec=TelemetryEvent)
    mock_event.to_dict = MagicMock(return_value={
        "id": "telemetry-event-123",
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "agent_complete",
        "agent_name": "detection_agent",
        "success": True
    })
    
    telemetry.events = [mock_event]
    
    return telemetry


class TestIntegrationHealthEndpoints:
    """Test integration health monitoring endpoints."""
    
    @patch('src.api.routers.monitoring.get_integration_monitor')
    def test_get_integration_health(self, mock_get_monitor, client, mock_integration_monitor):
        """Test integration health summary endpoint."""
        mock_get_monitor.return_value = mock_integration_monitor
        
        response = client.get("/monitoring/health/integrations")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["overall_status"] == "healthy"
        assert data["healthy_services"] == 5
        assert data["degraded_services"] == 1
        assert data["unhealthy_services"] == 0
        assert data["total_services"] == 6
        assert "timestamp" in data
        assert "system_uptime" in data
    
    @patch('src.api.routers.monitoring.get_integration_monitor')
    def test_get_service_health(self, mock_get_monitor, client, mock_integration_monitor):
        """Test specific service health endpoint."""
        mock_get_monitor.return_value = mock_integration_monitor
        
        response = client.get("/monitoring/health/integrations/bedrock")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["service_name"] == "bedrock"
        assert data["integration_type"] == "bedrock"
        assert data["status"] == "healthy"
        assert data["response_time_ms"] == 120.0
        assert data["error_rate"] == 0.0
        assert data["availability"] == 99.8
    
    @patch('src.api.routers.monitoring.get_integration_monitor')
    def test_get_service_health_not_found(self, mock_get_monitor, client, mock_integration_monitor):
        """Test service health endpoint with non-existent service."""
        mock_integration_monitor.get_service_health = AsyncMock(return_value=None)
        mock_get_monitor.return_value = mock_integration_monitor
        
        response = client.get("/monitoring/health/integrations/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @patch('src.api.routers.monitoring.get_integration_monitor')
    def test_get_unhealthy_services(self, mock_get_monitor, client, mock_integration_monitor):
        """Test unhealthy services endpoint."""
        mock_get_monitor.return_value = mock_integration_monitor
        
        response = client.get("/monitoring/health/integrations/unhealthy")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "unhealthy_count" in data
        assert "services" in data
        assert isinstance(data["services"], list)
    
    @patch('src.api.routers.monitoring.get_integration_monitor')
    def test_get_diagnostics(self, mock_get_monitor, client, mock_integration_monitor):
        """Test diagnostics endpoint."""
        mock_get_monitor.return_value = mock_integration_monitor
        
        response = client.get("/monitoring/diagnostics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "service" in data or "system_diagnostic" in data


class TestGuardrailTrackingEndpoints:
    """Test guardrail tracking endpoints."""
    
    @patch('src.api.routers.monitoring.get_guardrail_tracker')
    def test_get_guardrail_metrics(self, mock_get_tracker, client, mock_guardrail_tracker):
        """Test guardrail metrics endpoint."""
        mock_get_tracker.return_value = mock_guardrail_tracker
        
        response = client.get("/monitoring/guardrails/metrics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "total_guardrails" in data
        assert "metrics" in data
        assert len(data["metrics"]) > 0
        
        metric = data["metrics"][0]
        assert "guardrail_name" in metric
        assert "guardrail_type" in metric
        assert "total_events" in metric
        assert "block_rate" in metric
    
    @patch('src.api.routers.monitoring.get_guardrail_tracker')
    def test_get_guardrail_events(self, mock_get_tracker, client, mock_guardrail_tracker):
        """Test guardrail events endpoint."""
        mock_get_tracker.return_value = mock_guardrail_tracker
        
        response = client.get("/monitoring/guardrails/events?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "period_hours" in data
        assert "total_events" in data
        assert "events" in data
        assert isinstance(data["events"], list)
    
    @patch('src.api.routers.monitoring.get_guardrail_tracker')
    def test_get_guardrail_events_with_filters(self, mock_get_tracker, client, mock_guardrail_tracker):
        """Test guardrail events endpoint with filters."""
        mock_get_tracker.return_value = mock_guardrail_tracker
        
        response = client.get(
            "/monitoring/guardrails/events"
            "?hours=48"
            "&guardrail_type=content_filter"
            "&decision=block"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["period_hours"] == 48
        assert data["filters"]["guardrail_type"] == "content_filter"
        assert data["filters"]["decision"] == "block"
    
    @patch('src.api.routers.monitoring.get_guardrail_tracker')
    def test_get_compliance_analytics(self, mock_get_tracker, client, mock_guardrail_tracker):
        """Test compliance analytics endpoint."""
        mock_get_tracker.return_value = mock_guardrail_tracker
        
        response = client.get("/monitoring/guardrails/compliance")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert "total_events_24h" in data["summary"]
        assert "compliance_rate_24h" in data["summary"]
        assert "decisions_breakdown_24h" in data
    
    @patch('src.api.routers.monitoring.get_guardrail_tracker')
    def test_generate_compliance_report(self, mock_get_tracker, client, mock_guardrail_tracker):
        """Test compliance report generation endpoint."""
        mock_get_tracker.return_value = mock_guardrail_tracker
        
        response = client.get("/monitoring/guardrails/compliance/report?period_days=7")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "report_id" in data
        assert "generated_at" in data
        assert "period" in data
        assert "summary" in data
        assert "breakdown" in data
        assert "policy_analysis" in data
        assert "recommendations" in data


class TestAgentTelemetryEndpoints:
    """Test agent telemetry endpoints."""
    
    @patch('src.api.routers.monitoring.get_agent_telemetry')
    def test_get_agent_performance(self, mock_get_telemetry, client, mock_agent_telemetry):
        """Test agent performance endpoint."""
        mock_get_telemetry.return_value = mock_agent_telemetry
        
        response = client.get("/monitoring/agents/performance?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "analysis_period_hours" in data
        assert "total_agents_analyzed" in data
        assert "analyses" in data
        assert len(data["analyses"]) > 0
        
        analysis = data["analyses"][0]
        assert "agent_name" in analysis
        assert "agent_type" in analysis
        assert "success_rate" in analysis
        assert "performance_category" in analysis
        assert "efficiency_score" in analysis
    
    @patch('src.api.routers.monitoring.get_agent_telemetry')
    def test_get_agent_performance_with_filters(self, mock_get_telemetry, client, mock_agent_telemetry):
        """Test agent performance endpoint with filters."""
        mock_get_telemetry.return_value = mock_agent_telemetry
        
        response = client.get(
            "/monitoring/agents/performance"
            "?agent_name=detection_agent"
            "&agent_type=detection"
            "&hours=48"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["analysis_period_hours"] == 48
        assert data["filters"]["agent_name"] == "detection_agent"
        assert data["filters"]["agent_type"] == "detection"
    
    @patch('src.api.routers.monitoring.get_agent_telemetry')
    def test_get_system_performance(self, mock_get_telemetry, client, mock_agent_telemetry):
        """Test system performance endpoint."""
        mock_get_telemetry.return_value = mock_agent_telemetry
        
        response = client.get("/monitoring/agents/performance/system?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "generated_at" in data
        assert "analysis_period_hours" in data
        assert "total_agents" in data
        assert "active_agents" in data
        assert "system_success_rate" in data
        assert "consensus_success_rate" in data
        assert "escalation_rate" in data
        assert "performance_trends" in data
        assert "bottlenecks" in data
        assert "system_recommendations" in data
    
    @patch('src.api.routers.monitoring.get_agent_telemetry')
    def test_get_telemetry_events(self, mock_get_telemetry, client, mock_agent_telemetry):
        """Test telemetry events endpoint."""
        mock_get_telemetry.return_value = mock_agent_telemetry
        
        response = client.get("/monitoring/agents/telemetry/events?hours=24")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "period_hours" in data
        assert "total_events" in data
        assert "events" in data
        assert isinstance(data["events"], list)


class TestDashboardEndpoints:
    """Test dashboard and summary endpoints."""
    
    @patch('src.api.routers.monitoring.get_integration_monitor')
    @patch('src.api.routers.monitoring.get_guardrail_tracker')
    @patch('src.api.routers.monitoring.get_agent_telemetry')
    def test_get_monitoring_dashboard(
        self, 
        mock_get_telemetry, 
        mock_get_tracker, 
        mock_get_monitor,
        client, 
        mock_integration_monitor, 
        mock_guardrail_tracker, 
        mock_agent_telemetry
    ):
        """Test monitoring dashboard endpoint."""
        mock_get_monitor.return_value = mock_integration_monitor
        mock_get_tracker.return_value = mock_guardrail_tracker
        mock_get_telemetry.return_value = mock_agent_telemetry
        
        response = client.get("/monitoring/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "integration_health" in data
        assert "compliance" in data
        assert "agent_performance" in data
        assert "alerts" in data
        
        # Check integration health section
        integration_health = data["integration_health"]
        assert "overall_status" in integration_health
        assert "healthy_services" in integration_health
        assert "system_uptime" in integration_health
        
        # Check compliance section
        compliance = data["compliance"]
        assert "compliance_rate_24h" in compliance
        assert "total_events_24h" in compliance
        assert "decisions_breakdown" in compliance
        
        # Check agent performance section
        agent_performance = data["agent_performance"]
        assert "system_success_rate" in agent_performance
        assert "total_executions" in agent_performance
        assert "escalation_rate" in agent_performance
    
    @patch('src.api.routers.monitoring.get_integration_monitor')
    @patch('src.api.routers.monitoring.get_guardrail_tracker')
    @patch('src.api.routers.monitoring.get_agent_telemetry')
    def test_get_monitoring_status(
        self, 
        mock_get_telemetry, 
        mock_get_tracker, 
        mock_get_monitor,
        client, 
        mock_integration_monitor, 
        mock_guardrail_tracker, 
        mock_agent_telemetry
    ):
        """Test monitoring status endpoint."""
        mock_get_monitor.return_value = mock_integration_monitor
        mock_get_tracker.return_value = mock_guardrail_tracker
        mock_get_telemetry.return_value = mock_agent_telemetry
        
        response = client.get("/monitoring/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "monitoring_systems" in data
        assert "overall_status" in data
        
        monitoring_systems = data["monitoring_systems"]
        assert "integration_monitor" in monitoring_systems
        assert "guardrail_tracker" in monitoring_systems
        assert "agent_telemetry" in monitoring_systems
        
        # Check each monitoring system status
        for system_name, system_data in monitoring_systems.items():
            assert "active" in system_data
            assert system_data["active"] is True


class TestExportEndpoints:
    """Test data export endpoints."""
    
    @patch('src.api.routers.monitoring.get_integration_monitor')
    def test_export_integration_health(self, mock_get_monitor, client, mock_integration_monitor):
        """Test integration health export endpoint."""
        mock_get_monitor.return_value = mock_integration_monitor
        
        response = client.get("/monitoring/export/integration-health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "export_timestamp" in data
        assert "data_type" in data
        assert data["data_type"] == "integration_health"
        assert "report" in data
    
    @patch('src.api.routers.monitoring.get_guardrail_tracker')
    def test_export_guardrail_events(self, mock_get_tracker, client, mock_guardrail_tracker):
        """Test guardrail events export endpoint."""
        mock_guardrail_tracker.export_events = AsyncMock(return_value='{"events": []}')
        mock_get_tracker.return_value = mock_guardrail_tracker
        
        response = client.get("/monitoring/export/guardrail-events?hours=24&format_type=json")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "export_timestamp" in data
        assert "data_type" in data
        assert data["data_type"] == "guardrail_events"
        assert "format" in data
        assert "period_hours" in data
        assert "data" in data
    
    @patch('src.api.routers.monitoring.get_agent_telemetry')
    def test_export_agent_telemetry(self, mock_get_telemetry, client, mock_agent_telemetry):
        """Test agent telemetry export endpoint."""
        mock_agent_telemetry.export_telemetry_data = AsyncMock(return_value='{"telemetry": []}')
        mock_get_telemetry.return_value = mock_agent_telemetry
        
        response = client.get(
            "/monitoring/export/agent-telemetry"
            "?hours=48"
            "&agent_name=detection_agent"
            "&format_type=json"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "export_timestamp" in data
        assert "data_type" in data
        assert data["data_type"] == "agent_telemetry"
        assert "format" in data
        assert "period_hours" in data
        assert "agent_filter" in data
        assert "data" in data


class TestErrorHandling:
    """Test error handling in monitoring endpoints."""
    
    @patch('src.api.routers.monitoring.get_integration_monitor')
    def test_integration_monitor_error(self, mock_get_monitor, client):
        """Test handling of integration monitor errors."""
        mock_monitor = AsyncMock()
        mock_monitor.monitoring_active = False
        mock_monitor.start_monitoring = AsyncMock()
        mock_monitor.get_integration_health_report = AsyncMock(side_effect=Exception("Monitor error"))
        mock_get_monitor.return_value = mock_monitor
        
        response = client.get("/monitoring/health/integrations")
        
        assert response.status_code == 500
        assert "Monitor error" in response.json()["detail"]
    
    @patch('src.api.routers.monitoring.get_guardrail_tracker')
    def test_guardrail_tracker_error(self, mock_get_tracker, client):
        """Test handling of guardrail tracker errors."""
        mock_tracker = AsyncMock()
        mock_tracker.tracking_active = False
        mock_tracker.start_tracking = AsyncMock()
        mock_tracker.get_guardrail_metrics = AsyncMock(side_effect=Exception("Tracker error"))
        mock_get_tracker.return_value = mock_tracker
        
        response = client.get("/monitoring/guardrails/metrics")
        
        assert response.status_code == 500
        assert "Tracker error" in response.json()["detail"]
    
    @patch('src.api.routers.monitoring.get_agent_telemetry')
    def test_agent_telemetry_error(self, mock_get_telemetry, client):
        """Test handling of agent telemetry errors."""
        mock_telemetry = AsyncMock()
        mock_telemetry.collection_active = False
        mock_telemetry.start_collection = AsyncMock()
        mock_telemetry.analyze_agent_performance = AsyncMock(side_effect=Exception("Telemetry error"))
        mock_get_telemetry.return_value = mock_telemetry
        
        response = client.get("/monitoring/agents/performance")
        
        assert response.status_code == 500
        assert "Telemetry error" in response.json()["detail"]


class TestParameterValidation:
    """Test parameter validation in monitoring endpoints."""
    
    def test_invalid_hours_parameter(self, client):
        """Test validation of hours parameter."""
        # Test hours too low
        response = client.get("/monitoring/guardrails/events?hours=0")
        assert response.status_code == 422
        
        # Test hours too high
        response = client.get("/monitoring/guardrails/events?hours=200")
        assert response.status_code == 422
    
    def test_invalid_enum_parameters(self, client):
        """Test validation of enum parameters."""
        # Test invalid guardrail type
        response = client.get("/monitoring/guardrails/events?guardrail_type=invalid_type")
        assert response.status_code == 422
        
        # Test invalid decision type
        response = client.get("/monitoring/guardrails/events?decision=invalid_decision")
        assert response.status_code == 422
        
        # Test invalid agent type
        response = client.get("/monitoring/agents/performance?agent_type=invalid_agent")
        assert response.status_code == 422