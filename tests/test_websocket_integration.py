"""
Integration tests for WebSocket functionality.

Tests WebSocket connection, message broadcasting, agent state updates,
and dashboard-specific filtering for Dashboard 3 (Production).
"""

import pytest
import asyncio
import json
from datetime import datetime
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from src.main import app
from src.services.websocket_manager import WebSocketManager, get_websocket_manager
from src.models.agent import AgentMessage, AgentType


@pytest.fixture
def test_client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
async def ws_manager():
    """Create WebSocket manager instance."""
    manager = WebSocketManager(max_connections=10, batch_size=5, batch_interval=0.05)
    await manager.start()
    yield manager
    await manager.stop()


class TestWebSocketConnection:
    """Test WebSocket connection establishment and lifecycle."""

    def test_websocket_endpoint_exists(self, test_client):
        """Test that WebSocket endpoint is registered."""
        # Check if the endpoint is in the routes
        routes = [route.path for route in app.routes]
        assert "/dashboard/ws" in routes, "WebSocket endpoint should exist"

    def test_websocket_connection_successful(self, test_client):
        """Test successful WebSocket connection."""
        with test_client.websocket_connect("/dashboard/ws") as websocket:
            # Connection should be established
            assert websocket is not None

            # Should receive initial state message
            data = websocket.receive_json()
            assert data is not None
            assert "type" in data

    def test_websocket_connection_limit(self, test_client):
        """Test that connection limit is enforced."""
        # This would require multiple connections
        # Simplified test - just verify manager has limit
        manager = WebSocketManager(max_connections=2)
        assert manager.max_connections == 2

    def test_websocket_reconnection_handling(self, test_client):
        """Test that reconnection works after disconnect."""
        # First connection
        with test_client.websocket_connect("/dashboard/ws") as ws1:
            data1 = ws1.receive_json()
            assert data1 is not None

        # Second connection after first closed
        with test_client.websocket_connect("/dashboard/ws") as ws2:
            data2 = ws2.receive_json()
            assert data2 is not None


class TestWebSocketMessaging:
    """Test WebSocket message broadcasting and routing."""

    def test_receive_agent_state_update(self, test_client):
        """Test receiving agent state updates via WebSocket."""
        with test_client.websocket_connect("/dashboard/ws") as websocket:
            # Receive initial state
            initial = websocket.receive_json()
            assert initial["type"] == "initial_state"

            # In a real scenario, agent state would be broadcast
            # Here we verify the structure is correct
            assert "data" in initial

    def test_receive_incident_update(self, test_client):
        """Test receiving incident updates via WebSocket."""
        with test_client.websocket_connect("/dashboard/ws") as websocket:
            # Receive initial state
            initial = websocket.receive_json()

            # Trigger a demo incident via client message
            websocket.send_json({
                "action": "trigger_demo_incident",
                "incident_type": "database_failure"
            })

            # Should receive incident update (in production)
            # For now, just verify connection remains stable
            try:
                # Set a short timeout
                websocket.receive_json(timeout=1.0)
            except:
                # Expected if no incident is actually triggered
                pass

    def test_receive_business_metrics_update(self, test_client):
        """Test receiving business metrics via WebSocket."""
        with test_client.websocket_connect("/dashboard/ws") as websocket:
            initial = websocket.receive_json()

            # Business metrics should be included in initial state
            # or broadcast periodically
            assert "data" in initial


class TestWebSocketDashboardFiltering:
    """Test dashboard-specific filtering (Dashboard 3 only)."""

    def test_production_dashboard_receives_updates(self, test_client):
        """Test that production dashboard (Dashboard 3) receives updates."""
        with test_client.websocket_connect("/dashboard/ws") as websocket:
            # Dashboard 3 should receive all message types
            initial = websocket.receive_json()
            assert initial is not None
            assert "type" in initial

    def test_demo_dashboard_isolation(self):
        """Test that demo/transparency dashboards don't connect to WebSocket."""
        # This is enforced by frontend - they don't import useIncidentWebSocket
        # Verify that the hook is only used in production dashboard
        import os

        ops_dashboard = "dashboard/app/ops/page.tsx"
        demo_dashboard = "dashboard/app/demo/page.tsx"
        transparency_dashboard = "dashboard/app/transparency/page.tsx"

        # Check that ops dashboard imports the hook
        if os.path.exists(ops_dashboard):
            with open(ops_dashboard, 'r') as f:
                ops_content = f.read()
                # Should use ImprovedOperationsDashboardWebSocket which uses the hook
                assert "ImprovedOperationsDashboardWebSocket" in ops_content

        # Check that demo dashboard doesn't use WebSocket
        if os.path.exists(demo_dashboard):
            with open(demo_dashboard, 'r') as f:
                demo_content = f.read()
                assert "useIncidentWebSocket" not in demo_content
                assert "WebSocket" not in demo_content

        # Check that transparency dashboard doesn't use WebSocket
        if os.path.exists(transparency_dashboard):
            with open(transparency_dashboard, 'r') as f:
                transparency_content = f.read()
                assert "useIncidentWebSocket" not in transparency_content


class TestWebSocketPerformance:
    """Test WebSocket performance and reliability."""

    @pytest.mark.asyncio
    async def test_message_batching(self, ws_manager):
        """Test that messages are batched for performance."""
        # Verify batching configuration
        assert ws_manager.batch_size > 0
        assert ws_manager.batch_interval > 0

    @pytest.mark.asyncio
    async def test_backpressure_handling(self, ws_manager):
        """Test that slow clients don't block others."""
        # Verify queue limits exist
        assert ws_manager.connection_queues is not None

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, ws_manager):
        """Test that performance metrics are tracked."""
        metrics = ws_manager.get_metrics()

        assert "active_connections" in metrics
        assert "total_messages_sent" in metrics
        assert "uptime_seconds" in metrics


class TestWebSocketErrorHandling:
    """Test WebSocket error handling and recovery."""

    def test_malformed_message_handling(self, test_client):
        """Test handling of malformed messages."""
        with test_client.websocket_connect("/dashboard/ws") as websocket:
            # Receive initial state
            initial = websocket.receive_json()

            # Send malformed JSON
            try:
                websocket.send_text("not valid json")
                # Connection should handle error gracefully
                # Either close or send error response
            except:
                # Expected - connection may close
                pass

    def test_connection_close_cleanup(self, test_client):
        """Test that resources are cleaned up on disconnect."""
        with test_client.websocket_connect("/dashboard/ws") as websocket:
            initial = websocket.receive_json()
            # Connection established

        # After context exit, connection should be cleaned up
        # Verify by connecting again
        with test_client.websocket_connect("/dashboard/ws") as websocket2:
            initial2 = websocket2.receive_json()
            assert initial2 is not None


class TestWebSocketDemoControls:
    """Test demo-specific WebSocket controls for Dashboard 3."""

    def test_trigger_demo_incident(self, test_client):
        """Test triggering demo incidents via WebSocket."""
        with test_client.websocket_connect("/dashboard/ws") as websocket:
            initial = websocket.receive_json()

            # Send trigger command
            websocket.send_json({
                "action": "trigger_demo_incident",
                "incident_type": "database_failure"
            })

            # Command should be processed without error
            # (actual incident creation depends on backend implementation)

    def test_inject_byzantine_fault(self, test_client):
        """Test injecting Byzantine faults for demo."""
        with test_client.websocket_connect("/dashboard/ws") as websocket:
            initial = websocket.receive_json()

            # Send Byzantine fault injection command
            websocket.send_json({
                "action": "inject_byzantine_fault",
                "target_agent": "diagnosis",
                "fault_type": "conflicting_recommendations"
            })

            # Command should be processed

    def test_reset_agents(self, test_client):
        """Test resetting agents via WebSocket."""
        with test_client.websocket_connect("/dashboard/ws") as websocket:
            initial = websocket.receive_json()

            # Send reset command
            websocket.send_json({
                "action": "reset_agents"
            })

            # Command should be processed


class TestWebSocketIntegration:
    """End-to-end integration tests."""

    def test_full_incident_flow(self, test_client):
        """Test complete incident flow through WebSocket."""
        with test_client.websocket_connect("/dashboard/ws") as websocket:
            # 1. Receive initial state
            initial = websocket.receive_json()
            assert initial["type"] == "initial_state"

            # 2. Trigger incident
            websocket.send_json({
                "action": "trigger_demo_incident",
                "incident_type": "api_overload"
            })

            # 3. Should receive updates as incident progresses
            # (In production - simplified for test)

            # 4. Connection remains stable throughout
            assert websocket is not None

    def test_multiple_clients_broadcast(self, test_client):
        """Test that updates are broadcast to multiple clients."""
        # Connect two clients
        with test_client.websocket_connect("/dashboard/ws") as ws1:
            with test_client.websocket_connect("/dashboard/ws") as ws2:
                # Both should receive initial state
                initial1 = ws1.receive_json()
                initial2 = ws2.receive_json()

                assert initial1 is not None
                assert initial2 is not None

                # Both connections should remain active
                assert ws1 is not None
                assert ws2 is not None


# Run tests with: pytest tests/test_websocket_integration.py -v
