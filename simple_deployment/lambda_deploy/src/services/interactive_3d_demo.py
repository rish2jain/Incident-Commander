"""
Interactive 3D Demo Controller.

Provides demo scenario controls within 3D interface and performance
monitoring overlay with real-time metrics for enhanced presentations.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from src.utils.logging import get_logger
from src.services.visual_dashboard import get_visual_dashboard, AgentState
from src.services.realtime_visualization import get_realtime_visualizer
from src.services.websocket_manager import get_websocket_manager, WebSocketMessage

logger = get_logger("interactive_3d_demo")


class DemoControlAction(Enum):
    """Available demo control actions."""
    START_SCENARIO = "start_scenario"
    PAUSE_DEMO = "pause_demo"
    RESUME_DEMO = "resume_demo"
    RESET_SCENE = "reset_scene"
    ADJUST_SPEED = "adjust_speed"
    TOGGLE_METRICS = "toggle_metrics"
    CHANGE_CAMERA = "change_camera"
    HIGHLIGHT_AGENT = "highlight_agent"
    ZOOM_TO_INCIDENT = "zoom_to_incident"


@dataclass
class DemoScenarioConfig:
    """Configuration for demo scenarios."""
    scenario_id: str
    name: str
    description: str
    duration_seconds: int
    complexity: str  # low, medium, high
    agents_involved: List[str]
    key_features: List[str]
    camera_positions: List[Dict[str, float]]  # Predefined camera angles
    
    
@dataclass
class PerformanceMetrics:
    """Real-time performance metrics for overlay."""
    fps: float
    frame_time_ms: float
    agent_count: int
    connection_count: int
    incident_count: int
    memory_usage_mb: float
    cpu_usage_percent: float
    network_latency_ms: float
    render_calls: int
    timestamp: str


@dataclass
class CameraPosition:
    """3D camera position and orientation."""
    x: float
    y: float
    z: float
    target_x: float = 0.0
    target_y: float = 0.0
    target_z: float = 0.0
    fov: float = 75.0
    name: str = "default"


class Interactive3DDemoController:
    """
    Interactive 3D Demo Controller for enhanced presentations.
    
    Provides demo scenario controls, camera management, performance
    monitoring, and interactive features within the 3D interface.
    """
    
    def __init__(self):
        self.visual_dashboard = get_visual_dashboard()
        self.realtime_visualizer = get_realtime_visualizer()
        self.websocket_manager = get_websocket_manager()
        
        # Demo state
        self.current_scenario: Optional[str] = None
        self.demo_paused = False
        self.demo_speed = 1.0
        self.metrics_overlay_enabled = True
        self.auto_camera_enabled = True
        
        # Performance tracking
        self.performance_history: List[PerformanceMetrics] = []
        self.last_performance_update = time.time()
        
        # Camera presets
        self.camera_presets = {
            "overview": CameraPosition(0, 15, 20, 0, 0, 0, 75, "Overview"),
            "agent_focus": CameraPosition(0, 8, 12, 0, 0, 0, 60, "Agent Focus"),
            "incident_view": CameraPosition(0, 5, 8, 0, 2, 0, 50, "Incident View"),
            "side_view": CameraPosition(15, 10, 0, 0, 0, 0, 65, "Side View"),
            "top_down": CameraPosition(0, 25, 0, 0, 0, 0, 90, "Top Down"),
            "cinematic": CameraPosition(-10, 12, 15, 0, 0, 0, 55, "Cinematic")
        }
        
        self.current_camera = "overview"
        
        # Demo scenarios
        self.demo_scenarios = {
            "database_cascade": DemoScenarioConfig(
                scenario_id="database_cascade",
                name="Database Cascade Failure",
                description="Critical database connection pool exhaustion causing cascade failures",
                duration_seconds=180,
                complexity="high",
                agents_involved=["detection", "diagnosis", "prediction", "resolution", "communication"],
                key_features=["Multi-agent coordination", "Consensus decision making", "Automated rollback"],
                camera_positions=[
                    {"preset": "overview", "duration": 30},
                    {"preset": "agent_focus", "duration": 60},
                    {"preset": "incident_view", "duration": 60},
                    {"preset": "cinematic", "duration": 30}
                ]
            ),
            "ddos_attack": DemoScenarioConfig(
                scenario_id="ddos_attack",
                name="DDoS Attack Mitigation",
                description="Large-scale DDoS attack overwhelming API gateway",
                duration_seconds=120,
                complexity="medium",
                agents_involved=["detection", "diagnosis", "resolution", "communication"],
                key_features=["Rapid detection", "Traffic analysis", "Auto-scaling response"],
                camera_positions=[
                    {"preset": "overview", "duration": 20},
                    {"preset": "agent_focus", "duration": 50},
                    {"preset": "side_view", "duration": 50}
                ]
            ),
            "memory_leak": DemoScenarioConfig(
                scenario_id="memory_leak",
                name="Memory Leak Detection",
                description="Application memory leak causing gradual performance degradation",
                duration_seconds=90,
                complexity="low",
                agents_involved=["detection", "prediction", "resolution"],
                key_features=["Predictive analysis", "Gradual escalation", "Proactive resolution"],
                camera_positions=[
                    {"preset": "overview", "duration": 30},
                    {"preset": "agent_focus", "duration": 60}
                ]
            )
        }
        
        # Control callbacks
        self.control_callbacks: Dict[str, Callable] = {}
        
        logger.info("Interactive 3D Demo Controller initialized")
    
    async def initialize_demo_interface(self) -> Dict[str, Any]:
        """Initialize the interactive demo interface."""
        # Initialize visual dashboard
        scene_state = await self.visual_dashboard.initialize_3d_scene()
        
        # Set initial camera position
        await self.set_camera_position("overview")
        
        # Start performance monitoring
        asyncio.create_task(self._performance_monitoring_loop())
        
        # Broadcast demo interface initialization
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_demo_interface_initialized",
            timestamp=datetime.utcnow(),
            data={
                "scene_state": scene_state,
                "camera_presets": {name: asdict(pos) for name, pos in self.camera_presets.items()},
                "demo_scenarios": {name: asdict(config) for name, config in self.demo_scenarios.items()},
                "controls": {
                    "demo_speed": self.demo_speed,
                    "metrics_overlay": self.metrics_overlay_enabled,
                    "auto_camera": self.auto_camera_enabled,
                    "current_camera": self.current_camera
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        logger.info("3D demo interface initialized")
        return scene_state
    
    async def start_interactive_scenario(self, scenario_id: str, 
                                       custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Start an interactive demo scenario with 3D controls."""
        if scenario_id not in self.demo_scenarios:
            raise ValueError(f"Unknown scenario: {scenario_id}")
        
        scenario = self.demo_scenarios[scenario_id]
        self.current_scenario = scenario_id
        self.demo_paused = False
        
        # Apply custom configuration if provided
        if custom_config:
            for key, value in custom_config.items():
                if hasattr(scenario, key):
                    setattr(scenario, key, value)
        
        # Initialize agents for scenario
        await self._initialize_scenario_agents(scenario)
        
        # Set initial camera position
        if scenario.camera_positions:
            first_camera = scenario.camera_positions[0]
            await self.set_camera_position(first_camera["preset"])
        
        # Start scenario execution
        asyncio.create_task(self._execute_scenario_with_controls(scenario))
        
        # Broadcast scenario start
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_demo_scenario_started",
            timestamp=datetime.utcnow(),
            data={
                "scenario": asdict(scenario),
                "controls_enabled": True,
                "interactive_features": [
                    "Camera control",
                    "Speed adjustment", 
                    "Agent highlighting",
                    "Metrics overlay",
                    "Pause/Resume"
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        logger.info(f"Started interactive scenario: {scenario_id}")
        return {"scenario_id": scenario_id, "status": "started", "interactive": True}
    
    async def handle_demo_control(self, action: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle interactive demo control actions."""
        params = parameters or {}
        
        try:
            if action == DemoControlAction.PAUSE_DEMO.value:
                return await self._pause_demo()
            elif action == DemoControlAction.RESUME_DEMO.value:
                return await self._resume_demo()
            elif action == DemoControlAction.ADJUST_SPEED.value:
                speed = params.get("speed", 1.0)
                return await self._adjust_demo_speed(speed)
            elif action == DemoControlAction.CHANGE_CAMERA.value:
                preset = params.get("preset", "overview")
                return await self.set_camera_position(preset)
            elif action == DemoControlAction.TOGGLE_METRICS.value:
                return await self._toggle_metrics_overlay()
            elif action == DemoControlAction.HIGHLIGHT_AGENT.value:
                agent_id = params.get("agent_id")
                return await self._highlight_agent(agent_id)
            elif action == DemoControlAction.ZOOM_TO_INCIDENT.value:
                incident_id = params.get("incident_id")
                return await self._zoom_to_incident(incident_id)
            elif action == DemoControlAction.RESET_SCENE.value:
                return await self._reset_scene()
            else:
                raise ValueError(f"Unknown control action: {action}")
                
        except Exception as e:
            logger.error(f"Error handling demo control {action}: {e}")
            return {"status": "error", "message": str(e)}
    
    async def set_camera_position(self, preset_name: str, 
                                animate: bool = True, 
                                duration_ms: int = 1500) -> Dict[str, Any]:
        """Set camera position using preset or custom position."""
        if preset_name not in self.camera_presets:
            raise ValueError(f"Unknown camera preset: {preset_name}")
        
        camera_pos = self.camera_presets[preset_name]
        self.current_camera = preset_name
        
        # Broadcast camera change
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_camera_change",
            timestamp=datetime.utcnow(),
            data={
                "camera_position": asdict(camera_pos),
                "animate": animate,
                "duration_ms": duration_ms,
                "preset_name": preset_name,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        logger.debug(f"Set camera to preset: {preset_name}")
        return {"camera_preset": preset_name, "position": asdict(camera_pos)}
    
    async def add_performance_overlay(self, metrics: PerformanceMetrics) -> None:
        """Add performance metrics to 3D overlay."""
        if not self.metrics_overlay_enabled:
            return
        
        # Store metrics history
        self.performance_history.append(metrics)
        
        # Keep only last 60 seconds of data (assuming 1 update per second)
        if len(self.performance_history) > 60:
            self.performance_history = self.performance_history[-60:]
        
        # Calculate performance trends
        recent_metrics = self.performance_history[-10:] if len(self.performance_history) >= 10 else self.performance_history
        avg_fps = sum(m.fps for m in recent_metrics) / len(recent_metrics)
        avg_frame_time = sum(m.frame_time_ms for m in recent_metrics) / len(recent_metrics)
        
        # Determine performance status
        performance_status = "excellent"
        if avg_fps < 45:
            performance_status = "poor"
        elif avg_fps < 55:
            performance_status = "fair"
        elif avg_fps < 58:
            performance_status = "good"
        
        # Broadcast performance overlay update
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_performance_overlay",
            timestamp=datetime.utcnow(),
            data={
                "current_metrics": asdict(metrics),
                "trends": {
                    "avg_fps": round(avg_fps, 1),
                    "avg_frame_time": round(avg_frame_time, 2),
                    "performance_status": performance_status
                },
                "overlay_config": {
                    "position": "top_right",
                    "opacity": 0.8,
                    "auto_hide": False
                },
                "timestamp": metrics.timestamp
            }
        ))
    
    async def create_custom_camera_path(self, waypoints: List[Dict[str, float]], 
                                      duration_seconds: int = 10) -> Dict[str, Any]:
        """Create custom camera animation path."""
        if len(waypoints) < 2:
            raise ValueError("Camera path requires at least 2 waypoints")
        
        # Broadcast camera path animation
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_camera_path",
            timestamp=datetime.utcnow(),
            data={
                "waypoints": waypoints,
                "duration_seconds": duration_seconds,
                "interpolation": "smooth",
                "loop": False,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        logger.info(f"Created custom camera path with {len(waypoints)} waypoints")
        return {"waypoints": len(waypoints), "duration": duration_seconds}
    
    async def get_demo_controls_state(self) -> Dict[str, Any]:
        """Get current state of demo controls."""
        return {
            "current_scenario": self.current_scenario,
            "demo_paused": self.demo_paused,
            "demo_speed": self.demo_speed,
            "metrics_overlay_enabled": self.metrics_overlay_enabled,
            "auto_camera_enabled": self.auto_camera_enabled,
            "current_camera": self.current_camera,
            "available_cameras": list(self.camera_presets.keys()),
            "available_scenarios": list(self.demo_scenarios.keys()),
            "performance_history_length": len(self.performance_history),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _pause_demo(self) -> Dict[str, Any]:
        """Pause the current demo scenario."""
        self.demo_paused = True
        
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_demo_paused",
            timestamp=datetime.utcnow(),
            data={"timestamp": datetime.utcnow().isoformat()}
        ))
        
        logger.info("Demo paused")
        return {"status": "paused"}
    
    async def _resume_demo(self) -> Dict[str, Any]:
        """Resume the current demo scenario."""
        self.demo_paused = False
        
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_demo_resumed",
            timestamp=datetime.utcnow(),
            data={"timestamp": datetime.utcnow().isoformat()}
        ))
        
        logger.info("Demo resumed")
        return {"status": "resumed"}
    
    async def _adjust_demo_speed(self, speed: float) -> Dict[str, Any]:
        """Adjust demo playback speed."""
        self.demo_speed = max(0.1, min(5.0, speed))  # Clamp between 0.1x and 5.0x
        
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_demo_speed_changed",
            timestamp=datetime.utcnow(),
            data={
                "speed": self.demo_speed,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        logger.info(f"Demo speed adjusted to {self.demo_speed}x")
        return {"speed": self.demo_speed}
    
    async def _toggle_metrics_overlay(self) -> Dict[str, Any]:
        """Toggle performance metrics overlay."""
        self.metrics_overlay_enabled = not self.metrics_overlay_enabled
        
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_metrics_overlay_toggled",
            timestamp=datetime.utcnow(),
            data={
                "enabled": self.metrics_overlay_enabled,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        logger.info(f"Metrics overlay {'enabled' if self.metrics_overlay_enabled else 'disabled'}")
        return {"metrics_overlay": self.metrics_overlay_enabled}
    
    async def _highlight_agent(self, agent_id: str) -> Dict[str, Any]:
        """Highlight specific agent in 3D scene."""
        if not agent_id:
            return {"status": "error", "message": "Agent ID required"}
        
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_agent_highlight",
            timestamp=datetime.utcnow(),
            data={
                "agent_id": agent_id,
                "highlight_duration_ms": 3000,
                "highlight_effect": "glow_pulse",
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        logger.debug(f"Highlighted agent: {agent_id}")
        return {"highlighted_agent": agent_id}
    
    async def _zoom_to_incident(self, incident_id: str) -> Dict[str, Any]:
        """Zoom camera to specific incident."""
        if not incident_id:
            return {"status": "error", "message": "Incident ID required"}
        
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_zoom_to_incident",
            timestamp=datetime.utcnow(),
            data={
                "incident_id": incident_id,
                "zoom_duration_ms": 2000,
                "zoom_level": 1.5,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        logger.debug(f"Zoomed to incident: {incident_id}")
        return {"zoomed_to_incident": incident_id}
    
    async def _reset_scene(self) -> Dict[str, Any]:
        """Reset 3D scene to initial state."""
        await self.visual_dashboard.clear_scene()
        await self.set_camera_position("overview")
        
        self.current_scenario = None
        self.demo_paused = False
        self.demo_speed = 1.0
        
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_scene_reset",
            timestamp=datetime.utcnow(),
            data={"timestamp": datetime.utcnow().isoformat()}
        ))
        
        logger.info("3D scene reset")
        return {"status": "reset"}
    
    async def _initialize_scenario_agents(self, scenario: DemoScenarioConfig) -> None:
        """Initialize agents for scenario visualization."""
        for agent_type in scenario.agents_involved:
            agent_id = f"{agent_type}_agent"
            await self.visual_dashboard.add_agent(agent_id, agent_type)
    
    async def _execute_scenario_with_controls(self, scenario: DemoScenarioConfig) -> None:
        """Execute scenario with interactive controls."""
        start_time = time.time()
        camera_index = 0
        next_camera_time = start_time
        
        try:
            while time.time() - start_time < scenario.duration_seconds:
                # Handle pause
                while self.demo_paused:
                    await asyncio.sleep(0.1)
                
                # Adjust timing based on speed
                await asyncio.sleep(0.1 / self.demo_speed)
                
                # Auto camera transitions
                if (self.auto_camera_enabled and 
                    scenario.camera_positions and 
                    camera_index < len(scenario.camera_positions) and
                    time.time() >= next_camera_time):
                    
                    camera_config = scenario.camera_positions[camera_index]
                    await self.set_camera_position(camera_config["preset"])
                    
                    next_camera_time = time.time() + camera_config["duration"]
                    camera_index += 1
                
                # Update frame count for FPS calculation
                self.visual_dashboard.increment_frame_count()
            
            logger.info(f"Completed scenario: {scenario.scenario_id}")
            
        except Exception as e:
            logger.error(f"Error executing scenario {scenario.scenario_id}: {e}")
    
    async def _performance_monitoring_loop(self) -> None:
        """Continuous performance monitoring loop."""
        while True:
            try:
                current_time = time.time()
                
                # Calculate frame time
                frame_time_ms = (current_time - self.last_performance_update) * 1000
                self.last_performance_update = current_time
                
                # Get scene state for metrics
                scene_state = await self.visual_dashboard.get_scene_state()
                performance = scene_state["performance"]
                
                # Create performance metrics
                metrics = PerformanceMetrics(
                    fps=performance["current_fps"],
                    frame_time_ms=frame_time_ms,
                    agent_count=performance["agents_count"],
                    connection_count=performance["connections_count"],
                    incident_count=performance["incidents_count"],
                    memory_usage_mb=50.0,  # Placeholder - would integrate with actual monitoring
                    cpu_usage_percent=25.0,  # Placeholder
                    network_latency_ms=15.0,  # Placeholder
                    render_calls=performance["agents_count"] * 3 + performance["connections_count"],
                    timestamp=datetime.utcnow().isoformat()
                )
                
                # Add to overlay
                await self.add_performance_overlay(metrics)
                
                # Wait for next update (target 1 FPS for performance monitoring)
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                await asyncio.sleep(1.0)


# Global interactive demo controller
_interactive_demo_controller: Optional[Interactive3DDemoController] = None


def get_interactive_demo_controller() -> Interactive3DDemoController:
    """Get the global interactive demo controller."""
    global _interactive_demo_controller
    if _interactive_demo_controller is None:
        _interactive_demo_controller = Interactive3DDemoController()
    return _interactive_demo_controller