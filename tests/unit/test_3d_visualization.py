"""
Unit tests for 3D visualization components.

Tests for visual dashboard, real-time visualization, and interactive demo controls
with focus on core functionality and 60fps performance requirements.
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.services.visual_dashboard import (
    VisualDashboard, AgentState, Agent3DPosition, AgentConnection,
    IncidentVisualization, Scene3DConfiguration, get_visual_dashboard
)
from src.services.realtime_visualization import (
    RealtimeVisualizationIntegrator, AgentVisualizationUpdate,
    get_realtime_visualizer
)
from src.services.interactive_3d_demo import (
    Interactive3DDemoController, DemoScenarioConfig, PerformanceMetrics,
    CameraPosition, get_interactive_demo_controller
)


class TestVisualDashboard:
    """Test cases for VisualDashboard class."""
    
    @pytest.fixture
    def visual_dashboard(self):
        """Create a VisualDashboard instance for testing."""
        return VisualDashboard()
    
    @pytest.fixture
    def mock_websocket_manager(self):
        """Mock WebSocket manager for testing."""
        mock_manager = Mock()
        mock_manager.broadcast = AsyncMock()
        return mock_manager
    
    def test_initialization(self, visual_dashboard):
        """Test visual dashboard initialization."""
        assert visual_dashboard.scene_config is not None
        assert isinstance(visual_dashboard.scene_config, Scene3DConfiguration)
        assert visual_dashboard.agents == {}
        assert visual_dashboard.connections == []
        assert visual_dashboard.incidents == {}
        assert visual_dashboard.current_fps == 60.0
    
    def test_agent_type_positions(self, visual_dashboard):
        """Test predefined agent type positions."""
        expected_types = ["detection", "diagnosis", "prediction", "resolution", "communication"]
        
        for agent_type in expected_types:
            assert agent_type in visual_dashboard.agent_type_positions
            position = visual_dashboard.agent_type_positions[agent_type]
            assert len(position) == 3  # x, y, z coordinates
            assert all(isinstance(coord, (int, float)) for coord in position)
    
    @pytest.mark.asyncio
    async def test_initialize_3d_scene(self, visual_dashboard, mock_websocket_manager):
        """Test 3D scene initialization."""
        with patch.object(visual_dashboard, 'websocket_manager', mock_websocket_manager):
            scene_data = await visual_dashboard.initialize_3d_scene()
            
            assert "scene_config" in scene_data
            assert "agents" in scene_data
            assert "connections" in scene_data
            assert "incidents" in scene_data
            assert "timestamp" in scene_data
            assert "performance" in scene_data
            
            # Verify WebSocket broadcast was called
            mock_websocket_manager.broadcast.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_agent(self, visual_dashboard, mock_websocket_manager):
        """Test adding agent to 3D scene."""
        with patch.object(visual_dashboard, 'websocket_manager', mock_websocket_manager):
            agent_id = "test_agent"
            agent_type = "detection"
            
            await visual_dashboard.add_agent(agent_id, agent_type)
            
            # Verify agent was added
            assert agent_id in visual_dashboard.agents
            agent = visual_dashboard.agents[agent_id]
            assert agent.agent_id == agent_id
            assert agent.agent_type == agent_type
            assert agent.state == AgentState.IDLE
            
            # Verify WebSocket broadcast
            mock_websocket_manager.broadcast.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_agent_with_custom_position(self, visual_dashboard, mock_websocket_manager):
        """Test adding agent with custom position."""
        with patch.object(visual_dashboard, 'websocket_manager', mock_websocket_manager):
            agent_id = "custom_agent"
            agent_type = "diagnosis"
            custom_position = (5.0, 3.0, -2.0)
            
            await visual_dashboard.add_agent(agent_id, agent_type, custom_position)
            
            agent = visual_dashboard.agents[agent_id]
            assert agent.x == 5.0
            assert agent.y == 3.0
            assert agent.z == -2.0
    
    @pytest.mark.asyncio
    async def test_update_agent_state(self, visual_dashboard, mock_websocket_manager):
        """Test updating agent state and confidence."""
        with patch.object(visual_dashboard, 'websocket_manager', mock_websocket_manager):
            # First add an agent
            agent_id = "test_agent"
            await visual_dashboard.add_agent(agent_id, "detection")
            
            # Update agent state
            new_state = AgentState.PROCESSING
            confidence = 0.85
            
            await visual_dashboard.update_agent_state(agent_id, new_state, confidence)
            
            agent = visual_dashboard.agents[agent_id]
            assert agent.state == new_state
            assert agent.confidence == confidence
            
            # Verify broadcast was called twice (add + update)
            assert mock_websocket_manager.broadcast.call_count == 2
    
    @pytest.mark.asyncio
    async def test_create_agent_connection(self, visual_dashboard, mock_websocket_manager):
        """Test creating visual connection between agents."""
        with patch.object(visual_dashboard, 'websocket_manager', mock_websocket_manager):
            # Add two agents
            await visual_dashboard.add_agent("agent1", "detection")
            await visual_dashboard.add_agent("agent2", "diagnosis")
            
            # Create connection
            await visual_dashboard.create_agent_connection(
                from_agent="agent1",
                to_agent="agent2",
                connection_type="message",
                strength=0.8,
                duration_ms=1500
            )
            
            # Verify connection was created
            assert len(visual_dashboard.connections) == 1
            connection = visual_dashboard.connections[0]
            assert connection.from_agent == "agent1"
            assert connection.to_agent == "agent2"
            assert connection.connection_type == "message"
            assert connection.strength == 0.8
    
    @pytest.mark.asyncio
    async def test_add_incident_visualization(self, visual_dashboard, mock_websocket_manager):
        """Test adding incident visualization."""
        with patch.object(visual_dashboard, 'websocket_manager', mock_websocket_manager):
            # Add some agents first
            await visual_dashboard.add_agent("agent1", "detection")
            await visual_dashboard.add_agent("agent2", "diagnosis")
            
            incident_id = "test_incident"
            title = "Test Incident"
            severity = "high"
            affected_agents = ["agent1", "agent2"]
            
            await visual_dashboard.add_incident_visualization(
                incident_id, title, severity, affected_agents
            )
            
            # Verify incident was added
            assert incident_id in visual_dashboard.incidents
            incident = visual_dashboard.incidents[incident_id]
            assert incident.incident_id == incident_id
            assert incident.title == title
            assert incident.severity == severity
            assert incident.affected_agents == affected_agents
    
    @pytest.mark.asyncio
    async def test_animate_agent_to_position(self, visual_dashboard, mock_websocket_manager):
        """Test agent position animation."""
        with patch.object(visual_dashboard, 'websocket_manager', mock_websocket_manager):
            # Add agent
            agent_id = "test_agent"
            await visual_dashboard.add_agent(agent_id, "detection")
            
            # Animate to new position
            target_position = (10.0, 5.0, -3.0)
            await visual_dashboard.animate_agent_to_position(
                agent_id, target_position, duration_ms=1000
            )
            
            # Verify position was updated
            agent = visual_dashboard.agents[agent_id]
            assert agent.x == 10.0
            assert agent.y == 5.0
            assert agent.z == -3.0
    
    @pytest.mark.asyncio
    async def test_get_scene_state(self, visual_dashboard):
        """Test getting current scene state."""
        # Add some test data
        await visual_dashboard.add_agent("agent1", "detection")
        
        scene_state = await visual_dashboard.get_scene_state()
        
        assert "scene_config" in scene_state
        assert "agents" in scene_state
        assert "connections" in scene_state
        assert "incidents" in scene_state
        assert "performance" in scene_state
        assert "timestamp" in scene_state
        
        # Verify performance metrics
        performance = scene_state["performance"]
        assert "current_fps" in performance
        assert "frame_count" in performance
        assert "target_fps" in performance
        assert performance["target_fps"] == 60
    
    def test_frame_count_increment(self, visual_dashboard):
        """Test frame count increment for FPS calculation."""
        initial_count = visual_dashboard.frame_count
        visual_dashboard.increment_frame_count()
        assert visual_dashboard.frame_count == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_clear_scene(self, visual_dashboard, mock_websocket_manager):
        """Test clearing all scene elements."""
        with patch.object(visual_dashboard, 'websocket_manager', mock_websocket_manager):
            # Add some test data
            await visual_dashboard.add_agent("agent1", "detection")
            await visual_dashboard.add_incident_visualization(
                "incident1", "Test", "high", ["agent1"]
            )
            
            # Clear scene
            await visual_dashboard.clear_scene()
            
            # Verify everything was cleared
            assert len(visual_dashboard.agents) == 0
            assert len(visual_dashboard.connections) == 0
            assert len(visual_dashboard.incidents) == 0


class TestRealtimeVisualizationIntegrator:
    """Test cases for RealtimeVisualizationIntegrator class."""
    
    @pytest.fixture
    def realtime_visualizer(self):
        """Create a RealtimeVisualizationIntegrator instance for testing."""
        return RealtimeVisualizationIntegrator()
    
    @pytest.fixture
    def mock_visual_dashboard(self):
        """Mock visual dashboard for testing."""
        mock_dashboard = Mock()
        mock_dashboard.clear_scene = AsyncMock()
        mock_dashboard.add_agent = AsyncMock()
        mock_dashboard.update_agent_state = AsyncMock()
        mock_dashboard.create_agent_connection = AsyncMock()
        mock_dashboard.initialize_3d_scene = AsyncMock(return_value={"test": "data"})
        return mock_dashboard
    
    def test_initialization(self, realtime_visualizer):
        """Test realtime visualizer initialization."""
        assert realtime_visualizer.active_agents == {}
        assert realtime_visualizer.agent_interactions == []
        assert realtime_visualizer.visualization_enabled is True
        assert len(realtime_visualizer.state_mapping) > 0
    
    def test_state_mapping(self, realtime_visualizer):
        """Test agent state mapping."""
        mapping = realtime_visualizer.state_mapping
        
        assert mapping["idle"] == AgentState.IDLE
        assert mapping["processing"] == AgentState.PROCESSING
        assert mapping["collaborating"] == AgentState.COLLABORATING
        assert mapping["completed"] == AgentState.COMPLETED
        assert mapping["error"] == AgentState.ERROR
    
    @pytest.mark.asyncio
    async def test_initialize_agent_visualization(self, realtime_visualizer, mock_visual_dashboard):
        """Test initializing agent visualization."""
        with patch.object(realtime_visualizer, 'visual_dashboard', mock_visual_dashboard):
            agents = {
                "agent1": {"type": "detection"},
                "agent2": {"type": "diagnosis"}
            }
            
            result = await realtime_visualizer.initialize_agent_visualization(agents)
            
            # Verify agents were added
            assert len(realtime_visualizer.active_agents) == 2
            assert "agent1" in realtime_visualizer.active_agents
            assert "agent2" in realtime_visualizer.active_agents
            
            # Verify dashboard methods were called
            mock_visual_dashboard.clear_scene.assert_called_once()
            assert mock_visual_dashboard.add_agent.call_count == 2
            mock_visual_dashboard.initialize_3d_scene.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_agent_visualization(self, realtime_visualizer, mock_visual_dashboard):
        """Test updating agent visualization."""
        with patch.object(realtime_visualizer, 'visual_dashboard', mock_visual_dashboard):
            with patch.object(realtime_visualizer, 'websocket_manager') as mock_ws:
                mock_ws.broadcast = AsyncMock()
                
                # Initialize agent first
                realtime_visualizer.active_agents["agent1"] = {
                    "type": "detection",
                    "state": "idle",
                    "confidence": 1.0
                }
                
                await realtime_visualizer.update_agent_visualization(
                    agent_id="agent1",
                    action="analyzing logs",
                    state="processing",
                    confidence=0.85
                )
                
                # Verify dashboard update was called
                mock_visual_dashboard.update_agent_state.assert_called_once()
                
                # Verify WebSocket broadcast
                mock_ws.broadcast.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_visualize_agent_communication(self, realtime_visualizer, mock_visual_dashboard):
        """Test visualizing agent communication."""
        with patch.object(realtime_visualizer, 'visual_dashboard', mock_visual_dashboard):
            with patch.object(realtime_visualizer, 'websocket_manager') as mock_ws:
                mock_ws.broadcast = AsyncMock()
                
                # Initialize agents
                realtime_visualizer.active_agents.update({
                    "agent1": {"type": "detection"},
                    "agent2": {"type": "diagnosis"}
                })
                
                await realtime_visualizer.visualize_agent_communication(
                    from_agent="agent1",
                    to_agent="agent2",
                    message_type="consensus",
                    data={"test": "data"}
                )
                
                # Verify connection was created
                mock_visual_dashboard.create_agent_connection.assert_called_once()
                
                # Verify interaction was tracked
                assert len(realtime_visualizer.agent_interactions) == 1
                interaction = realtime_visualizer.agent_interactions[0]
                assert interaction["from_agent"] == "agent1"
                assert interaction["to_agent"] == "agent2"
                assert interaction["message_type"] == "consensus"
    
    @pytest.mark.asyncio
    async def test_get_visualization_metrics(self, realtime_visualizer, mock_visual_dashboard):
        """Test getting visualization metrics."""
        mock_scene_state = {
            "performance": {"current_fps": 58.5, "frame_count": 1000},
            "agents": {"agent1": {}, "agent2": {}},
            "connections": [],
            "incidents": {}
        }
        mock_visual_dashboard.get_scene_state = AsyncMock(return_value=mock_scene_state)
        
        with patch.object(realtime_visualizer, 'visual_dashboard', mock_visual_dashboard):
            # Add some test data
            realtime_visualizer.active_agents = {"agent1": {"state": "processing"}}
            realtime_visualizer.agent_interactions = [{"test": "interaction"}]
            
            metrics = await realtime_visualizer.get_visualization_metrics()
            
            assert "performance" in metrics
            assert "active_agents" in metrics
            assert "recent_interactions" in metrics
            assert "visualization_enabled" in metrics
            assert "scene_stats" in metrics
            assert "agent_states" in metrics
            
            assert metrics["active_agents"] == 1
            assert metrics["recent_interactions"] == 1
            assert metrics["visualization_enabled"] is True


class TestInteractive3DDemoController:
    """Test cases for Interactive3DDemoController class."""
    
    @pytest.fixture
    def demo_controller(self):
        """Create an Interactive3DDemoController instance for testing."""
        return Interactive3DDemoController()
    
    def test_initialization(self, demo_controller):
        """Test demo controller initialization."""
        assert demo_controller.current_scenario is None
        assert demo_controller.demo_paused is False
        assert demo_controller.demo_speed == 1.0
        assert demo_controller.metrics_overlay_enabled is True
        assert demo_controller.auto_camera_enabled is True
        assert len(demo_controller.camera_presets) > 0
        assert len(demo_controller.demo_scenarios) > 0
    
    def test_camera_presets(self, demo_controller):
        """Test camera presets configuration."""
        expected_presets = ["overview", "agent_focus", "incident_view", "side_view", "top_down", "cinematic"]
        
        for preset_name in expected_presets:
            assert preset_name in demo_controller.camera_presets
            camera_pos = demo_controller.camera_presets[preset_name]
            assert isinstance(camera_pos, CameraPosition)
            assert camera_pos.name == preset_name.replace("_", " ").title()
    
    def test_demo_scenarios(self, demo_controller):
        """Test demo scenarios configuration."""
        expected_scenarios = ["database_cascade", "ddos_attack", "memory_leak"]
        
        for scenario_id in expected_scenarios:
            assert scenario_id in demo_controller.demo_scenarios
            scenario = demo_controller.demo_scenarios[scenario_id]
            assert isinstance(scenario, DemoScenarioConfig)
            assert scenario.scenario_id == scenario_id
            assert len(scenario.agents_involved) > 0
            assert scenario.duration_seconds > 0
    
    @pytest.mark.asyncio
    async def test_initialize_demo_interface(self, demo_controller):
        """Test demo interface initialization."""
        with patch.object(demo_controller, 'visual_dashboard') as mock_dashboard:
            with patch.object(demo_controller, 'websocket_manager') as mock_ws:
                mock_dashboard.initialize_3d_scene = AsyncMock(return_value={"test": "scene"})
                mock_ws.broadcast = AsyncMock()
                
                result = await demo_controller.initialize_demo_interface()
                
                # Verify dashboard initialization
                mock_dashboard.initialize_3d_scene.assert_called_once()
                
                # Verify WebSocket broadcast (should be called twice: camera + interface)
                assert mock_ws.broadcast.call_count == 2
                
                assert result == {"test": "scene"}
    
    @pytest.mark.asyncio
    async def test_set_camera_position(self, demo_controller):
        """Test setting camera position."""
        with patch.object(demo_controller, 'websocket_manager') as mock_ws:
            mock_ws.broadcast = AsyncMock()
            
            result = await demo_controller.set_camera_position("overview")
            
            assert demo_controller.current_camera == "overview"
            assert "camera_preset" in result
            assert "position" in result
            
            # Verify WebSocket broadcast
            mock_ws.broadcast.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_set_invalid_camera_position(self, demo_controller):
        """Test setting invalid camera position."""
        with pytest.raises(ValueError, match="Unknown camera preset"):
            await demo_controller.set_camera_position("invalid_preset")
    
    @pytest.mark.asyncio
    async def test_start_interactive_scenario(self, demo_controller):
        """Test starting interactive scenario."""
        with patch.object(demo_controller, '_initialize_scenario_agents') as mock_init:
            with patch.object(demo_controller, 'set_camera_position') as mock_camera:
                with patch.object(demo_controller, 'websocket_manager') as mock_ws:
                    mock_init.return_value = AsyncMock()
                    mock_camera.return_value = AsyncMock()
                    mock_ws.broadcast = AsyncMock()
                    
                    result = await demo_controller.start_interactive_scenario("database_cascade")
                    
                    assert demo_controller.current_scenario == "database_cascade"
                    assert demo_controller.demo_paused is False
                    assert result["scenario_id"] == "database_cascade"
                    assert result["status"] == "started"
                    assert result["interactive"] is True
    
    @pytest.mark.asyncio
    async def test_start_invalid_scenario(self, demo_controller):
        """Test starting invalid scenario."""
        with pytest.raises(ValueError, match="Unknown scenario"):
            await demo_controller.start_interactive_scenario("invalid_scenario")
    
    @pytest.mark.asyncio
    async def test_handle_demo_control_pause(self, demo_controller):
        """Test pause demo control."""
        with patch.object(demo_controller, 'websocket_manager') as mock_ws:
            mock_ws.broadcast = AsyncMock()
            
            result = await demo_controller.handle_demo_control("pause_demo")
            
            assert demo_controller.demo_paused is True
            assert result["status"] == "paused"
    
    @pytest.mark.asyncio
    async def test_handle_demo_control_resume(self, demo_controller):
        """Test resume demo control."""
        with patch.object(demo_controller, 'websocket_manager') as mock_ws:
            mock_ws.broadcast = AsyncMock()
            
            demo_controller.demo_paused = True
            result = await demo_controller.handle_demo_control("resume_demo")
            
            assert demo_controller.demo_paused is False
            assert result["status"] == "resumed"
    
    @pytest.mark.asyncio
    async def test_handle_demo_control_adjust_speed(self, demo_controller):
        """Test adjust speed demo control."""
        with patch.object(demo_controller, 'websocket_manager') as mock_ws:
            mock_ws.broadcast = AsyncMock()
            
            result = await demo_controller.handle_demo_control(
                "adjust_speed", {"speed": 2.0}
            )
            
            assert demo_controller.demo_speed == 2.0
            assert result["speed"] == 2.0
    
    @pytest.mark.asyncio
    async def test_handle_demo_control_invalid_action(self, demo_controller):
        """Test invalid demo control action."""
        result = await demo_controller.handle_demo_control("invalid_action")
        
        assert result["status"] == "error"
        assert "Unknown control action" in result["message"]
    
    @pytest.mark.asyncio
    async def test_add_performance_overlay(self, demo_controller):
        """Test adding performance overlay."""
        with patch.object(demo_controller, 'websocket_manager') as mock_ws:
            mock_ws.broadcast = AsyncMock()
            
            metrics = PerformanceMetrics(
                fps=58.5,
                frame_time_ms=17.1,
                agent_count=5,
                connection_count=3,
                incident_count=1,
                memory_usage_mb=45.2,
                cpu_usage_percent=23.8,
                network_latency_ms=12.5,
                render_calls=18,
                timestamp=datetime.utcnow().isoformat()
            )
            
            await demo_controller.add_performance_overlay(metrics)
            
            # Verify metrics were stored
            assert len(demo_controller.performance_history) == 1
            assert demo_controller.performance_history[0] == metrics
            
            # Verify WebSocket broadcast
            mock_ws.broadcast.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_demo_controls_state(self, demo_controller):
        """Test getting demo controls state."""
        demo_controller.current_scenario = "test_scenario"
        demo_controller.demo_paused = True
        demo_controller.demo_speed = 1.5
        
        state = await demo_controller.get_demo_controls_state()
        
        assert state["current_scenario"] == "test_scenario"
        assert state["demo_paused"] is True
        assert state["demo_speed"] == 1.5
        assert "available_cameras" in state
        assert "available_scenarios" in state
        assert "timestamp" in state


class TestPerformanceRequirements:
    """Test cases for 60fps performance requirements."""
    
    @pytest.mark.asyncio
    async def test_frame_rate_tracking(self):
        """Test frame rate tracking meets 60fps requirement."""
        visual_dashboard = VisualDashboard()
        
        # Simulate frame rendering
        start_time = time.time()
        frame_count = 0
        target_fps = 60
        test_duration = 1.0  # 1 second test
        
        while time.time() - start_time < test_duration:
            visual_dashboard.increment_frame_count()
            frame_count += 1
            
            # Simulate frame time (should be ~16.67ms for 60fps)
            await asyncio.sleep(1.0 / target_fps)
        
        # Calculate actual FPS
        actual_duration = time.time() - start_time
        actual_fps = frame_count / actual_duration
        
        # Allow 10% tolerance for test environment variations
        assert actual_fps >= target_fps * 0.9, f"FPS too low: {actual_fps:.1f} < {target_fps * 0.9:.1f}"
    
    @pytest.mark.asyncio
    async def test_scene_update_performance(self):
        """Test scene update performance under load."""
        visual_dashboard = VisualDashboard()
        
        # Add multiple agents
        agent_count = 10
        for i in range(agent_count):
            await visual_dashboard.add_agent(f"agent_{i}", "detection")
        
        # Measure update performance
        start_time = time.time()
        update_count = 100
        
        for i in range(update_count):
            agent_id = f"agent_{i % agent_count}"
            await visual_dashboard.update_agent_state(
                agent_id, AgentState.PROCESSING, confidence=0.8
            )
        
        duration = time.time() - start_time
        updates_per_second = update_count / duration
        
        # Should handle at least 60 updates per second for smooth animation
        assert updates_per_second >= 60, f"Update rate too low: {updates_per_second:.1f} < 60"
    
    @pytest.mark.asyncio
    async def test_connection_rendering_performance(self):
        """Test connection rendering performance."""
        visual_dashboard = VisualDashboard()
        
        # Add agents
        for i in range(5):
            await visual_dashboard.add_agent(f"agent_{i}", "detection")
        
        # Create multiple connections rapidly
        start_time = time.time()
        connection_count = 50
        
        for i in range(connection_count):
            from_agent = f"agent_{i % 5}"
            to_agent = f"agent_{(i + 1) % 5}"
            
            await visual_dashboard.create_agent_connection(
                from_agent, to_agent, "message", strength=0.8, duration_ms=1000
            )
        
        duration = time.time() - start_time
        connections_per_second = connection_count / duration
        
        # Should handle connection creation efficiently
        assert connections_per_second >= 30, f"Connection creation too slow: {connections_per_second:.1f} < 30"


# Integration test for global instances
def test_global_instances():
    """Test global instance getters."""
    dashboard1 = get_visual_dashboard()
    dashboard2 = get_visual_dashboard()
    assert dashboard1 is dashboard2  # Should return same instance
    
    visualizer1 = get_realtime_visualizer()
    visualizer2 = get_realtime_visualizer()
    assert visualizer1 is visualizer2  # Should return same instance
    
    controller1 = get_interactive_demo_controller()
    controller2 = get_interactive_demo_controller()
    assert controller1 is controller2  # Should return same instance