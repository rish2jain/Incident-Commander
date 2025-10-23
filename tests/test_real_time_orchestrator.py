"""
Integration tests for Real-Time Orchestrator.

Tests real-time incident processing with WebSocket streaming,
agent state updates, and incident flow visualization.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock, patch

from src.orchestrator.real_time_orchestrator import RealTimeOrchestrator, get_real_time_orchestrator
from src.models.incident import Incident
from src.models.real_time_models import (
    AgentState,
    IncidentPhase,
    AgentUpdate,
    IncidentFlowUpdate,
    SystemHealthMetrics,
    BusinessMetrics,
)


@pytest.fixture
async def orchestrator():
    """Create orchestrator instance with mocked WebSocket manager."""
    orch = RealTimeOrchestrator()
    orch.ws_manager = AsyncMock()
    orch.ws_manager.get_metrics = Mock(return_value={
        "active_connections": 5,
        "total_messages_sent": 100
    })
    yield orch


@pytest.fixture
def sample_incident():
    """Create sample incident for testing."""
    return Incident(
        id="test-incident-123",
        title="Test Database Outage",
        description="Database connection pool exhausted",
        severity="high",
        affected_services=["api-service", "web-app"],
        detected_at=datetime.utcnow()
    )


class TestOrchestratorLifecycle:
    """Test orchestrator initialization and lifecycle."""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initializes correctly."""
        orch = RealTimeOrchestrator()

        assert orch.ws_manager is None
        assert len(orch.active_incidents) == 0
        assert len(orch.processing_times) == 6  # One per phase (including complete and verification)

    @pytest.mark.asyncio
    async def test_orchestrator_singleton(self):
        """Test orchestrator singleton pattern."""
        mock_ws_manager = AsyncMock()
        with patch('src.orchestrator.real_time_orchestrator.get_websocket_manager', return_value=mock_ws_manager):
            orch1 = await get_real_time_orchestrator()
            orch2 = await get_real_time_orchestrator()

            assert orch1 is orch2


class TestAgentStateBroadcasting:
    """Test real-time agent state broadcasting."""

    @pytest.mark.asyncio
    async def test_broadcast_agent_update(self, orchestrator):
        """Test broadcasting agent status update."""
        await orchestrator._broadcast_agent_update(
            incident_id="inc-123",
            agent_name="detection_agent",
            agent_type="detection",
            state=AgentState.PROCESSING,
            phase=IncidentPhase.DETECTION,
            progress=0.5
        )

        # Verify WebSocket manager was called
        orchestrator.ws_manager.broadcast_agent_state.assert_called_once()

        call_args = orchestrator.ws_manager.broadcast_agent_state.call_args
        payload = call_args[0][0]  # First positional argument
        assert payload["agent_name"] == "detection_agent"
        assert payload["state"] == AgentState.PROCESSING.value

    @pytest.mark.asyncio
    async def test_broadcast_error_notification(self, orchestrator):
        """Test broadcasting error notifications."""
        await orchestrator._broadcast_error(
            error_type="agent_failure",
            error_message="Agent crashed unexpectedly",
            severity="high",
            incident_id="inc-123"
        )

        # Verify error was broadcast
        orchestrator.ws_manager.broadcast_message.assert_called_once()


class TestIncidentFlowTracking:
    """Test incident flow visualization."""

    @pytest.mark.asyncio
    async def test_broadcast_incident_flow(self, orchestrator, sample_incident):
        """Test broadcasting incident flow updates."""
        incident_id = sample_incident.id
        orchestrator.active_incidents[incident_id] = {
            "incident": sample_incident,
            "completed_phases": [IncidentPhase.DETECTION],
            "active_agents": ["diagnosis_agent"],
            "progress": 0.2
        }

        await orchestrator._broadcast_incident_flow(
            incident_id=incident_id,
            current_phase=IncidentPhase.DIAGNOSIS,
            phase_progress=0.5
        )

        # Verify flow update was broadcast
        orchestrator.ws_manager.broadcast_incident_update.assert_called_once()

        call_args = orchestrator.ws_manager.broadcast_incident_update.call_args
        payload = call_args[0][0]  # First positional argument
        assert payload["incident_id"] == incident_id
        assert payload["phase"] == IncidentPhase.DIAGNOSIS.value


class TestIncidentProcessing:
    """Test real-time incident processing workflow."""

    @pytest.mark.asyncio
    async def test_process_incident_success(self, orchestrator, sample_incident):
        """Test successful incident processing."""
        # Mock agent callbacks
        callbacks = {
            "detection": AsyncMock(return_value={"status": "success"}),
            "diagnosis": AsyncMock(return_value={"status": "success"}),
            "prediction": AsyncMock(return_value={"status": "success"}),
            "resolution": AsyncMock(return_value={"status": "success"}),
        }

        result = await orchestrator.process_incident_realtime(
            incident=sample_incident,
            agent_callbacks=callbacks
        )

        # Verify result
        assert result["status"] == "completed"
        assert result["incident_id"] == sample_incident.id
        assert result["processing_duration"] > 0
        assert result["phases_completed"] == 4  # Detection, diagnosis, prediction, resolution

        # Verify all callbacks were called
        for callback in callbacks.values():
            callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_incident_with_phase_failure(self, orchestrator, sample_incident):
        """Test incident processing with phase failure."""
        # Mock callbacks with one failing
        callbacks = {
            "detection": AsyncMock(return_value={"status": "success"}),
            "diagnosis": AsyncMock(side_effect=Exception("Diagnosis failed")),
        }

        with pytest.raises(Exception, match="Diagnosis failed"):
            await orchestrator.process_incident_realtime(
                incident=sample_incident,
                agent_callbacks=callbacks
            )

        # Verify error was broadcast
        assert orchestrator.ws_manager.broadcast_message.called

    @pytest.mark.asyncio
    async def test_agent_execution_tracking(self, orchestrator):
        """Test agent execution context manager."""
        incident_id = "inc-123"
        agent_name = "test_agent"

        async with orchestrator._track_agent_execution(
            incident_id=incident_id,
            agent_name=agent_name,
            agent_type="detection",
            phase=IncidentPhase.DETECTION
        ):
            # Simulate work
            await asyncio.sleep(0.1)

        # Verify state transitions were broadcast
        assert orchestrator.ws_manager.broadcast_agent_state.call_count >= 3

        # Check final state was COMPLETED
        final_call = orchestrator.ws_manager.broadcast_agent_state.call_args
        assert "COMPLETED" in str(final_call) or AgentState.COMPLETED.value in str(final_call)

    @pytest.mark.asyncio
    async def test_agent_execution_timeout(self, orchestrator):
        """Test agent execution timeout handling."""
        incident_id = "inc-123"

        with pytest.raises(asyncio.TimeoutError):
            async with orchestrator._track_agent_execution(
                incident_id=incident_id,
                agent_name="slow_agent",
                agent_type="detection",
                phase=IncidentPhase.DETECTION
            ):
                raise asyncio.TimeoutError("Agent timed out")

        # Verify timeout was broadcast
        assert orchestrator.ws_manager.broadcast_agent_state.called
        assert orchestrator.ws_manager.broadcast_message.called  # Error notification


class TestSystemHealth:
    """Test system health metrics."""

    @pytest.mark.asyncio
    async def test_get_system_health(self, orchestrator):
        """Test system health metrics calculation."""
        # Add some active incidents
        orchestrator.active_incidents["inc-1"] = {"start_time": datetime.utcnow()}
        orchestrator.active_incidents["inc-2"] = {"start_time": datetime.utcnow()}

        health = await orchestrator.get_system_health()

        # Verify health metrics
        assert isinstance(health, SystemHealthMetrics)
        assert health.current_incidents == 2
        assert health.active_agents > 0
        assert health.processing_capacity >= 0.0
        assert health.processing_capacity <= 1.0
        assert health.websocket_connections == 5  # From mocked metrics

    @pytest.mark.asyncio
    async def test_broadcast_system_health(self, orchestrator):
        """Test broadcasting system health."""
        await orchestrator.broadcast_system_health()

        # Verify health was broadcast
        orchestrator.ws_manager.broadcast_message.assert_called_once()

        call_args = orchestrator.ws_manager.broadcast_message.call_args[0][0]
        assert call_args["event_type"] == "system_health"


class TestProcessingMetrics:
    """Test processing time tracking."""

    @pytest.mark.asyncio
    async def test_processing_time_tracking(self, orchestrator, sample_incident):
        """Test that processing times are tracked."""
        initial_times = len(orchestrator.processing_times[IncidentPhase.DETECTION.value])

        callbacks = {
            "detection": AsyncMock(return_value={"status": "success"}),
            "diagnosis": AsyncMock(return_value={"status": "success"}),
            "prediction": AsyncMock(return_value={"status": "success"}),
            "resolution": AsyncMock(return_value={"status": "success"}),
        }

        await orchestrator.process_incident_realtime(
            incident=sample_incident,
            agent_callbacks=callbacks
        )

        # Verify processing times were recorded
        final_times = len(orchestrator.processing_times[IncidentPhase.DETECTION.value])
        assert final_times > initial_times


class TestConcurrentProcessing:
    """Test concurrent incident processing."""

    @pytest.mark.asyncio
    async def test_multiple_concurrent_incidents(self, orchestrator):
        """Test processing multiple incidents concurrently."""
        incidents = [
            Incident(
                id=f"inc-{i}",
                title=f"Test Incident {i}",
                description="Test",
                severity="medium",
                detected_at=datetime.utcnow()
            )
            for i in range(3)
        ]

        callbacks = {
            "detection": AsyncMock(return_value={"status": "success"}),
            "diagnosis": AsyncMock(return_value={"status": "success"}),
            "prediction": AsyncMock(return_value={"status": "success"}),
            "resolution": AsyncMock(return_value={"status": "success"}),
        }

        # Process concurrently
        tasks = [
            orchestrator.process_incident_realtime(incident, callbacks)
            for incident in incidents
        ]

        results = await asyncio.gather(*tasks, return_exceptions=False)

        # Verify all completed
        assert len(results) == 3
        for result in results:
            assert result["status"] == "completed"


class TestDataModels:
    """Test data model creation and validation."""

    def test_agent_update_model(self):
        """Test AgentUpdate model creation."""
        update = AgentUpdate(
            agent_name="detection_agent",
            agent_type="detection",
            incident_id="inc-123",
            state=AgentState.PROCESSING,
            phase=IncidentPhase.DETECTION,
            progress=0.5,
            confidence=0.85
        )

        assert update.agent_name == "detection_agent"
        assert update.state == AgentState.PROCESSING
        assert update.progress == 0.5
        assert update.update_id is not None

    def test_incident_flow_update_model(self):
        """Test IncidentFlowUpdate model creation."""
        flow = IncidentFlowUpdate(
            incident_id="inc-123",
            current_phase=IncidentPhase.DIAGNOSIS,
            completed_phases=[IncidentPhase.DETECTION],
            overall_progress=0.25,
            phase_progress=0.5
        )

        assert flow.incident_id == "inc-123"
        assert flow.current_phase == IncidentPhase.DIAGNOSIS
        assert len(flow.completed_phases) == 1
        assert flow.overall_progress == 0.25

    def test_system_health_metrics_model(self):
        """Test SystemHealthMetrics model creation."""
        health = SystemHealthMetrics(
            active_agents=4,
            healthy_agents=4,
            degraded_agents=0,
            error_agents=0,
            current_incidents=2,
            queue_depth=0,
            processing_capacity=0.8,
            average_latency_ms=50.0,
            p95_latency_ms=100.0,
            p99_latency_ms=150.0,
            websocket_connections=10,
            websocket_latency_ms=25.0,
            messages_per_second=50.0
        )

        assert health.active_agents == 4
        assert health.processing_capacity == 0.8
        assert health.websocket_connections == 10


# Run tests with: pytest tests/test_real_time_orchestrator.py -v
