"""
Integration tests for 3D visualization API endpoints.

Tests for FastAPI routes, WebSocket connections, and end-to-end
3D visualization functionality with performance validation.
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
from unittest.mock import Mock, AsyncMock, patch

from src.main import app
from src.services.visual_dashboard import AgentState
from src.services.interactive_3d_demo import DemoControlAction


class TestVisual3DAPIEndpoints:
    """Test cases for 3D visualization API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_visual_dashboard(self):
        """Mock visual dashboard for API testing."""
        mock_dashboard = Mock()
        mock_dashboard.get_scene_state = AsyncMock(return_value={
            "scene_config": {"test": "config"},
            "agents": {},
            "connections": [],
            "incidents": {},
            "performance": {"current_fps": 60.0, "frame_count": 1000},
            "timestamp": "2024-01-01T00:00:00"
        })
        mock_dashboard.initialize_3d_scene = AsyncMock(return_value={"initialized": True})
        mock_dashboard.clear_scene = AsyncMock()
        mock_dashboard.add_agent = AsyncMock()
        mock_dashboard.update_agent_state = AsyncMock()
        mock_dashboard.animate_agent_to_position = AsyncMock()
        mock_dashboard.create_agent_connection = AsyncMock()
        mock_dashboard.add_incident_visualization = AsyncMock()
        mock_dashboard.update_incident_status = AsyncMock()
        mock_dashboard.update_scene_config = AsyncMock()
        return mock_dashboard
    
    def test_get_scene_state(self, client, mock_visual_dashboard):
        """Test GET /3d/scene/state endpoint."""
        with patch('src.api.routers.visual_3d.get_visual_dashboard', return_value=mock_visual_dashboard):
            response = client.get("/3d/scene/state")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "data" in data
            assert "timestamp" in data
    
    def test_initialize_scene(self, client, mock_visual_dashboard):
        """Test POST /3d/scene/initialize endpoint."""
        with patch('src.api.routers.visual_3d.get_visual_dashboard', return_value=mock_visual_dashboard):
            response = client.post("/3d/scene/initialize")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "3D scene initialized"
            assert "data" in data
            
            mock_visual_dashboard.initialize_3d_scene.assert_called_once()
    
    def test_clear_scene(self, client, mock_visual_dashboard):
        """Test POST /3d/scene/clear endpoint."""
        with patch('src.api.routers.visual_3d.get_visual_dashboard', return_value=mock_visual_dashboard):
            response = client.post("/3d/scene/clear")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "3D scene cleared"
            
            mock_visual_dashboard.clear_scene.assert_called_once()
    
    def test_update_scene_config(self, client, mock_visual_dashboard):
        """Test PUT /3d/scene/config endpoint."""
        config_update = {
            "animation_speed": 1.5,
            "show_grid": True,
            "agent_spacing": 6.0
        }
        
        with patch('src.api.routers.visual_3d.get_visual_dashboard', return_value=mock_visual_dashboard):
            response = client.put("/3d/scene/config", json=config_update)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "Scene configuration updated"
            assert data["updated_config"] == config_update
            
            mock_visual_dashboard.update_scene_config.assert_called_once_with(config_update)
    
    def test_add_agent_to_scene(self, client, mock_visual_dashboard):
        """Test POST /3d/agents/add endpoint."""
        agent_request = {
            "agent_id": "test_agent",
            "agent_type": "detection",
            "position": {"x": 5.0, "y": 2.0, "z": -1.0}
        }
        
        with patch('src.api.routers.visual_3d.get_visual_dashboard', return_value=mock_visual_dashboard):
            response = client.post("/3d/agents/add", json=agent_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["agent_id"] == "test_agent"
            assert data["agent_type"] == "detection"
            
            mock_visual_dashboard.add_agent.assert_called_once()
    
    def test_update_agent_state(self, client, mock_visual_dashboard):
        """Test PUT /3d/agents/state endpoint."""
        state_update = {
            "agent_id": "test_agent",
            "state": "processing",
            "confidence": 0.85
        }
        
        with patch('src.api.routers.visual_3d.get_visual_dashboard', return_value=mock_visual_dashboard):
            response = client.put("/3d/agents/state", json=state_update)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["agent_id"] == "test_agent"
            assert data["new_state"] == "processing"
            assert data["confidence"] == 0.85
            
            mock_visual_dashboard.update_agent_state.assert_called_once()
    
    def test_animate_agent_position(self, client, mock_visual_dashboard):
        """Test POST /3d/agents/animate endpoint."""
        params = {
            "agent_id": "test_agent",
            "target_x": 10.0,
            "target_y": 5.0,
            "target_z": -2.0,
            "duration_ms": 1500
        }
        
        with patch('src.api.routers.visual_3d.get_visual_dashboard', return_value=mock_visual_dashboard):
            response = client.post("/3d/agents/animate", params=params)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["agent_id"] == "test_agent"
            assert data["target_position"]["x"] == 10.0
            assert data["duration_ms"] == 1500
    
    def test_create_agent_connection(self, client, mock_visual_dashboard):
        """Test POST /3d/connections/create endpoint."""
        connection_request = {
            "from_agent": "agent1",
            "to_agent": "agent2",
            "connection_type": "consensus",
            "strength": 0.9,
            "duration_ms": 2500
        }
        
        with patch('src.api.routers.visual_3d.get_visual_dashboard', return_value=mock_visual_dashboard):
            response = client.post("/3d/connections/create", json=connection_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "Agent connection created"
            assert data["connection"]["from_agent"] == "agent1"
            assert data["connection"]["to_agent"] == "agent2"
    
    def test_add_incident_visualization(self, client, mock_visual_dashboard):
        """Test POST /3d/incidents/add endpoint."""
        incident_request = {
            "incident_id": "test_incident",
            "title": "Test Incident",
            "severity": "high",
            "affected_agents": ["agent1", "agent2"]
        }
        
        with patch('src.api.routers.visual_3d.get_visual_dashboard', return_value=mock_visual_dashboard):
            response = client.post("/3d/incidents/add", json=incident_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "Incident visualization added"
            assert data["incident"]["id"] == "test_incident"
    
    def test_update_incident_status(self, client, mock_visual_dashboard):
        """Test PUT /3d/incidents/{incident_id}/status endpoint."""
        with patch('src.api.routers.visual_3d.get_visual_dashboard', return_value=mock_visual_dashboard):
            response = client.put("/3d/incidents/test_incident/status?status=resolved")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["incident_id"] == "test_incident"
            assert data["new_status"] == "resolved"
    
    def test_get_camera_presets(self, client):
        """Test GET /3d/camera/presets endpoint."""
        with patch('src.api.routers.visual_3d.get_interactive_demo_controller') as mock_controller:
            mock_instance = Mock()
            mock_instance.camera_presets = {"overview": Mock(), "agent_focus": Mock()}
            mock_instance.current_camera = "overview"
            mock_controller.return_value = mock_instance
            
            response = client.get("/3d/camera/presets")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "presets" in data
            assert "current_camera" in data
    
    def test_set_camera_position(self, client):
        """Test POST /3d/camera/position endpoint."""
        camera_request = {
            "preset_name": "overview",
            "animate": True,
            "duration_ms": 1500
        }
        
        with patch('src.api.routers.visual_3d.get_interactive_demo_controller') as mock_controller:
            mock_instance = Mock()
            mock_instance.set_camera_position = AsyncMock(return_value={"test": "result"})
            mock_controller.return_value = mock_instance
            
            response = client.post("/3d/camera/position", json=camera_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "Camera position updated"
    
    def test_initialize_demo_interface(self, client):
        """Test POST /3d/demo/initialize endpoint."""
        with patch('src.api.routers.visual_3d.get_interactive_demo_controller') as mock_controller:
            mock_instance = Mock()
            mock_instance.initialize_demo_interface = AsyncMock(return_value={"initialized": True})
            mock_controller.return_value = mock_instance
            
            response = client.post("/3d/demo/initialize")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["message"] == "Demo interface initialized"
    
    def test_start_interactive_scenario(self, client):
        """Test POST /3d/demo/scenario/{scenario_id} endpoint."""
        with patch('src.api.routers.visual_3d.get_interactive_demo_controller') as mock_controller:
            mock_instance = Mock()
            mock_instance.start_interactive_scenario = AsyncMock(return_value={
                "scenario_id": "database_cascade",
                "status": "started",
                "interactive": True
            })
            mock_controller.return_value = mock_instance
            
            response = client.post("/3d/demo/scenario/database_cascade")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["data"]["scenario_id"] == "database_cascade"
    
    def test_start_invalid_scenario(self, client):
        """Test starting invalid scenario returns 400."""
        with patch('src.api.routers.visual_3d.get_interactive_demo_controller') as mock_controller:
            mock_instance = Mock()
            mock_instance.start_interactive_scenario = AsyncMock(
                side_effect=ValueError("Unknown scenario: invalid")
            )
            mock_controller.return_value = mock_instance
            
            response = client.post("/3d/demo/scenario/invalid")
            
            assert response.status_code == 400
    
    def test_handle_demo_control(self, client):
        """Test POST /3d/demo/control endpoint."""
        control_request = {
            "action": "pause_demo",
            "parameters": {}
        }
        
        with patch('src.api.routers.visual_3d.get_interactive_demo_controller') as mock_controller:
            mock_instance = Mock()
            mock_instance.handle_demo_control = AsyncMock(return_value={"status": "paused"})
            mock_controller.return_value = mock_instance
            
            response = client.post("/3d/demo/control", json=control_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["result"]["status"] == "paused"
    
    def test_get_demo_scenarios(self, client):
        """Test GET /3d/demo/scenarios endpoint."""
        with patch('src.api.routers.visual_3d.get_interactive_demo_controller') as mock_controller:
            mock_scenario = Mock()
            mock_scenario.name = "Test Scenario"
            mock_scenario.description = "Test Description"
            mock_scenario.duration_seconds = 120
            mock_scenario.complexity = "medium"
            mock_scenario.agents_involved = ["agent1", "agent2"]
            mock_scenario.key_features = ["feature1", "feature2"]
            
            mock_instance = Mock()
            mock_instance.demo_scenarios = {"test_scenario": mock_scenario}
            mock_controller.return_value = mock_instance
            
            response = client.get("/3d/demo/scenarios")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "scenarios" in data
    
    def test_get_visualization_metrics(self, client):
        """Test GET /3d/visualization/metrics endpoint."""
        with patch('src.api.routers.visual_3d.get_realtime_visualizer') as mock_visualizer:
            mock_instance = Mock()
            mock_instance.get_visualization_metrics = AsyncMock(return_value={
                "performance": {"fps": 60.0},
                "active_agents": 5,
                "visualization_enabled": True
            })
            mock_visualizer.return_value = mock_instance
            
            response = client.get("/3d/visualization/metrics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert "data" in data
    
    def test_toggle_visualization(self, client):
        """Test POST /3d/visualization/toggle endpoint."""
        with patch('src.api.routers.visual_3d.get_realtime_visualizer') as mock_visualizer:
            mock_instance = Mock()
            mock_instance.toggle_visualization = AsyncMock()
            mock_visualizer.return_value = mock_instance
            
            response = client.post("/3d/visualization/toggle?enabled=false")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["enabled"] is False
    
    def test_health_check(self, client, mock_visual_dashboard):
        """Test GET /3d/health endpoint."""
        with patch('src.api.routers.visual_3d.get_visual_dashboard', return_value=mock_visual_dashboard):
            with patch('src.api.routers.visual_3d.get_realtime_visualizer') as mock_visualizer:
                with patch('src.api.routers.visual_3d.get_interactive_demo_controller') as mock_controller:
                    # Setup mocks
                    mock_viz_instance = Mock()
                    mock_viz_instance.get_visualization_metrics = AsyncMock(return_value={
                        "visualization_enabled": True
                    })
                    mock_visualizer.return_value = mock_viz_instance
                    
                    mock_demo_instance = Mock()
                    mock_demo_instance.get_demo_controls_state = AsyncMock(return_value={
                        "current_scenario": None,
                        "demo_paused": False
                    })
                    mock_controller.return_value = mock_demo_instance
                    
                    response = client.get("/3d/health")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["status"] == "healthy"
                    assert "services" in data
                    assert "performance" in data
                    assert "scene_stats" in data


class TestWebSocketIntegration:
    """Test cases for WebSocket integration."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment."""
        with patch('src.api.routers.visual_3d.get_websocket_manager') as mock_ws_manager:
            with patch('src.api.routers.visual_3d.get_visual_dashboard') as mock_dashboard:
                # Setup mocks
                mock_manager = Mock()
                mock_manager.connect = AsyncMock()
                mock_manager.send_to_connection = AsyncMock()
                mock_manager.disconnect = AsyncMock()
                mock_ws_manager.return_value = mock_manager
                
                mock_dash_instance = Mock()
                mock_dash_instance.get_scene_state = AsyncMock(return_value={"test": "state"})
                mock_dash_instance.increment_frame_count = Mock()
                mock_dashboard.return_value = mock_dash_instance
                
                # Test WebSocket connection (simplified)
                client = TestClient(app)
                
                with client.websocket_connect("/3d/ws") as websocket:
                    # Verify connection was established
                    mock_manager.connect.assert_called_once()
                    
                    # Send test message
                    websocket.send_text(json.dumps({"type": "ping"}))
                    
                    # Verify response handling
                    mock_manager.send_to_connection.assert_called()


class TestPerformanceIntegration:
    """Integration tests for performance requirements."""
    
    def test_api_response_times(self, client):
        """Test API response times meet performance requirements."""
        import time
        
        with patch('src.api.routers.visual_3d.get_visual_dashboard') as mock_dashboard:
            mock_instance = Mock()
            mock_instance.get_scene_state = AsyncMock(return_value={"test": "data"})
            mock_dashboard.return_value = mock_instance
            
            # Test multiple endpoints for response time
            endpoints = [
                "/3d/scene/state",
                "/3d/camera/presets",
                "/3d/health"
            ]
            
            for endpoint in endpoints:
                start_time = time.time()
                response = client.get(endpoint)
                duration = time.time() - start_time
                
                assert response.status_code == 200
                # API responses should be under 100ms for smooth 60fps operation
                assert duration < 0.1, f"Endpoint {endpoint} too slow: {duration:.3f}s"
    
    def test_concurrent_requests(self, client):
        """Test handling concurrent requests efficiently."""
        import concurrent.futures
        import time
        
        with patch('src.api.routers.visual_3d.get_visual_dashboard') as mock_dashboard:
            mock_instance = Mock()
            mock_instance.get_scene_state = AsyncMock(return_value={"test": "data"})
            mock_dashboard.return_value = mock_instance
            
            def make_request():
                return client.get("/3d/scene/state")
            
            # Test 10 concurrent requests
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request) for _ in range(10)]
                responses = [future.result() for future in futures]
            
            duration = time.time() - start_time
            
            # All requests should succeed
            assert all(r.status_code == 200 for r in responses)
            
            # Should handle 10 concurrent requests in under 1 second
            assert duration < 1.0, f"Concurrent requests too slow: {duration:.3f}s"


class TestErrorHandling:
    """Test error handling in API endpoints."""
    
    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON in requests."""
        response = client.post(
            "/3d/agents/add",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        incomplete_request = {
            "agent_id": "test_agent"
            # Missing agent_type
        }
        
        response = client.post("/3d/agents/add", json=incomplete_request)
        
        assert response.status_code == 422  # Validation error
    
    def test_invalid_parameter_values(self, client):
        """Test handling of invalid parameter values."""
        invalid_request = {
            "agent_id": "test_agent",
            "agent_type": "detection",
            "confidence": 1.5  # Invalid: should be 0.0-1.0
        }
        
        response = client.put("/3d/agents/state", json=invalid_request)
        
        assert response.status_code == 422  # Validation error
    
    def test_service_error_handling(self, client):
        """Test handling of service layer errors."""
        with patch('src.api.routers.visual_3d.get_visual_dashboard') as mock_dashboard:
            mock_instance = Mock()
            mock_instance.get_scene_state = AsyncMock(side_effect=Exception("Service error"))
            mock_dashboard.return_value = mock_instance
            
            response = client.get("/3d/scene/state")
            
            assert response.status_code == 500
            data = response.json()
            assert "Service error" in data["detail"]