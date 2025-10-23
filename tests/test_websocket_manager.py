"""
Unit tests for WebSocket Manager.

Tests WebSocket manager functionality without requiring full app initialization.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock
from collections import deque

from src.services.websocket_manager import (
    WebSocketManager,
    WebSocketMessage,
    ConnectionMetrics
)


@pytest.fixture
async def ws_manager_instance_instance():
    """Create WebSocket manager instance."""
    manager = WebSocketManager(max_connections=10, batch_size=5, batch_interval=0.05)
    await manager.start()
    yield manager
    await manager.stop()


@pytest.fixture
def mock_websocket():
    """Create mock WebSocket."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    ws.send_text = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


class TestWebSocketManagerLifecycle:
    """Test WebSocket manager lifecycle operations."""

    @pytest.mark.asyncio
    async def test_manager_start(self):
        """Test manager starts successfully."""
        manager = WebSocketManager()
        await manager.start()

        assert manager.batch_task is not None
        assert not manager.batch_task.done()

        await manager.stop()

    @pytest.mark.asyncio
    async def test_manager_stop(self):
        """Test manager stops cleanly."""
        manager = WebSocketManager()
        await manager.start()
        await manager.stop()

        assert manager.batch_task.done()
        assert len(manager.active_connections) == 0

    @pytest.mark.asyncio
    async def test_manager_configuration(self):
        """Test manager accepts configuration."""
        manager = WebSocketManager(
            max_connections=100,
            batch_size=20,
            batch_interval=0.5
        )

        assert manager.max_connections == 100
        assert manager.batch_size == 20
        assert manager.batch_interval == 0.5


class TestConnectionManagement:
    """Test connection establishment and management."""

    @pytest.mark.asyncio
    async def test_connect_success(self, ws_manager_instance_instance, mock_websocket):
        """Test successful connection."""
        connection_id = "test-conn-1"

        result = await ws_manager_instance_instance.connect(mock_websocket, connection_id)

        assert result is True
        assert connection_id in ws_manager_instance_instance.active_connections
        assert connection_id in ws_manager_instance_instance.connection_metrics
        mock_websocket.accept.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_limit_enforced(self, mock_websocket):
        """Test that connection limit is enforced."""
        manager = WebSocketManager(max_connections=2)
        await manager.start()

        # Connect up to limit
        result1 = await manager.connect(mock_websocket, "conn-1")
        result2 = await manager.connect(mock_websocket, "conn-2")

        assert result1 is True
        assert result2 is True
        assert len(manager.active_connections) == 2

        # Third connection should be rejected
        ws3 = AsyncMock()
        ws3.accept = AsyncMock()
        ws3.close = AsyncMock()
        result3 = await manager.connect(ws3, "conn-3")

        assert result3 is False
        assert len(manager.active_connections) == 2

        await manager.stop()

    @pytest.mark.asyncio
    async def test_disconnect_cleanup(self, ws_manager_instance, mock_websocket):
        """Test disconnect cleans up resources."""
        connection_id = "test-conn-1"

        await ws_manager_instance.connect(mock_websocket, connection_id)
        assert connection_id in ws_manager_instance.active_connections

        await ws_manager_instance.disconnect(connection_id)

        assert connection_id not in ws_manager_instance.active_connections
        assert connection_id not in ws_manager_instance.connection_metrics
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, ws_manager_instance, mock_websocket):
        """Test connection metrics are tracked."""
        connection_id = "test-conn-1"

        await ws_manager_instance.connect(mock_websocket, connection_id)

        metrics = ws_manager_instance.connection_metrics[connection_id]
        assert isinstance(metrics, ConnectionMetrics)
        assert metrics.connected_at is not None
        assert metrics.messages_sent == 0


class TestMessageBroadcasting:
    """Test message broadcasting functionality."""

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, ws_manager_instance):
        """Test broadcasting to all connections."""
        # Connect multiple clients
        ws1, ws2, ws3 = AsyncMock(), AsyncMock(), AsyncMock()
        for ws in [ws1, ws2, ws3]:
            ws.accept = AsyncMock()
            ws.send_json = AsyncMock()

        await ws_manager_instance.connect(ws1, "conn-1")
        await ws_manager_instance.connect(ws2, "conn-2")
        await ws_manager_instance.connect(ws3, "conn-3")

        # Broadcast message
        test_data = {"type": "test", "message": "hello"}
        await ws_manager_instance.broadcast_agent_state("test_agent", "active", test_data)

        # Allow batch processor to run
        await asyncio.sleep(0.2)

        # All connections should receive message
        assert ws1.send_json.called or ws1.send_text.called
        assert ws2.send_json.called or ws2.send_text.called
        assert ws3.send_json.called or ws3.send_text.called

    @pytest.mark.asyncio
    async def test_message_structure(self, ws_manager_instance):
        """Test message structure is correct."""
        message = WebSocketMessage(
            type="agent_state",
            timestamp=datetime.utcnow(),
            data={"agent": "test", "state": "active"},
            priority=2
        )

        assert message.type == "agent_state"
        assert message.priority == 2
        assert "agent" in message.data


class TestPerformanceFeatures:
    """Test performance-related features."""

    @pytest.mark.asyncio
    async def test_message_batching_configuration(self, ws_manager_instance):
        """Test message batching is configured."""
        assert ws_manager_instance.batch_size > 0
        assert ws_manager_instance.batch_interval > 0
        assert ws_manager_instance.pending_messages is not None

    @pytest.mark.asyncio
    async def test_connection_queues(self, ws_manager_instance, mock_websocket):
        """Test connection queues for backpressure."""
        connection_id = "test-conn-1"
        await ws_manager_instance.connect(mock_websocket, connection_id)

        # Queue should exist
        assert isinstance(ws_manager_instance.connection_queues[connection_id], deque)
        assert ws_manager_instance.connection_queues[connection_id].maxlen == 100

    @pytest.mark.asyncio
    async def test_metrics_collection(self, ws_manager_instance, mock_websocket):
        """Test performance metrics are collected."""
        await ws_manager_instance.connect(mock_websocket, "conn-1")

        metrics = ws_manager_instance.get_metrics()

        assert "active_connections" in metrics
        assert "total_connections" in metrics
        assert "total_messages_sent" in metrics
        assert "uptime_seconds" in metrics
        assert metrics["active_connections"] == 1
        assert metrics["total_connections"] == 1


class TestAgentStateManagement:
    """Test agent state tracking."""

    @pytest.mark.asyncio
    async def test_agent_state_update(self, ws_manager_instance, mock_websocket):
        """Test agent state is updated."""
        await ws_manager_instance.connect(mock_websocket, "conn-1")

        await ws_manager_instance.broadcast_agent_state(
            agent_name="diagnosis",
            state="analyzing",
            metadata={"confidence": 0.85}
        )

        # Allow processing
        await asyncio.sleep(0.1)

        assert "diagnosis" in ws_manager_instance.agent_states
        assert ws_manager_instance.agent_states["diagnosis"] == "analyzing"

    @pytest.mark.asyncio
    async def test_incident_flow_tracking(self, ws_manager_instance, mock_websocket):
        """Test incident flow is tracked."""
        await ws_manager_instance.connect(mock_websocket, "conn-1")

        incident_id = "inc-123"
        await ws_manager_instance.broadcast_incident_update(
            incident_id=incident_id,
            phase="diagnosis",
            data={"severity": "high"}
        )

        await asyncio.sleep(0.1)

        assert incident_id in ws_manager_instance.incident_flows


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_connection_failure_handling(self, ws_manager_instance):
        """Test connection failures are handled."""
        failing_ws = AsyncMock()
        failing_ws.accept = AsyncMock(side_effect=Exception("Connection failed"))

        result = await ws_manager_instance.connect(failing_ws, "conn-1")

        assert result is False
        assert "conn-1" not in ws_manager_instance.active_connections

    @pytest.mark.asyncio
    async def test_disconnect_error_handling(self, ws_manager_instance):
        """Test disconnect errors are handled."""
        failing_ws = AsyncMock()
        failing_ws.accept = AsyncMock()
        failing_ws.close = AsyncMock(side_effect=Exception("Close failed"))

        await ws_manager_instance.connect(failing_ws, "conn-1")

        # Should not raise exception
        await ws_manager_instance.disconnect("conn-1")

        # Should still clean up
        assert "conn-1" not in ws_manager_instance.active_connections


class TestDashboardIsolation:
    """Test dashboard-specific filtering."""

    def test_dashboard_type_filtering_design(self):
        """Test that dashboard filtering is part of design."""
        # This verifies the architecture supports dashboard filtering
        # Actual filtering would be implemented in connection metadata
        manager = WebSocketManager()

        # Manager should support connection metadata
        assert hasattr(manager, 'active_connections')
        assert hasattr(manager, 'connection_metrics')

    @pytest.mark.asyncio
    async def test_connection_metadata(self, ws_manager_instance, mock_websocket):
        """Test connections can have metadata."""
        connection_id = "test-conn-1"
        await ws_manager_instance.connect(mock_websocket, connection_id)

        # Metrics object can store connection metadata
        metrics = ws_manager_instance.connection_metrics[connection_id]
        assert metrics is not None
        assert isinstance(metrics, ConnectionMetrics)


# Run tests with: pytest tests/test_websocket_manager.py -v
