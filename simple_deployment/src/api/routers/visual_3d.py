"""
3D Visual Dashboard API endpoints.

FastAPI routes for 3D dashboard configuration, control, and real-time
visualization updates with WebSocket support.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from pydantic import BaseModel, Field

from src.utils.logging import get_logger
from src.services.visual_dashboard import get_visual_dashboard, AgentState, Scene3DConfiguration
from src.services.realtime_visualization import get_realtime_visualizer
from src.services.interactive_3d_demo import get_interactive_demo_controller, DemoControlAction
from src.services.websocket_manager import get_websocket_manager
from src.services.visual_3d_integration import get_visual_3d_integration

logger = get_logger("visual_3d_api")

router = APIRouter(prefix="/3d", tags=["3D Visualization"])


# Pydantic models for API requests/responses

class Agent3DRequest(BaseModel):
    """Request model for adding agent to 3D scene."""
    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Type of agent (detection, diagnosis, etc.)")
    position: Optional[Dict[str, float]] = Field(None, description="Custom position {x, y, z}")


class AgentStateUpdate(BaseModel):
    """Request model for updating agent state."""
    agent_id: str = Field(..., description="Agent identifier")
    state: str = Field(..., description="New agent state")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Agent confidence level")


class AgentConnectionRequest(BaseModel):
    """Request model for creating agent connection."""
    from_agent: str = Field(..., description="Source agent ID")
    to_agent: str = Field(..., description="Target agent ID")
    connection_type: str = Field("message", description="Type of connection")
    strength: float = Field(1.0, ge=0.0, le=1.0, description="Connection strength")
    duration_ms: int = Field(2000, ge=100, le=10000, description="Duration in milliseconds")


class IncidentVisualizationRequest(BaseModel):
    """Request model for adding incident visualization."""
    incident_id: str = Field(..., description="Incident identifier")
    title: str = Field(..., description="Incident title")
    severity: str = Field(..., description="Incident severity level")
    affected_agents: List[str] = Field(..., description="List of affected agent IDs")


class CameraPositionRequest(BaseModel):
    """Request model for camera position change."""
    preset_name: Optional[str] = Field(None, description="Camera preset name")
    position: Optional[Dict[str, float]] = Field(None, description="Custom camera position")
    animate: bool = Field(True, description="Whether to animate transition")
    duration_ms: int = Field(1500, ge=100, le=5000, description="Animation duration")


class DemoControlRequest(BaseModel):
    """Request model for demo control actions."""
    action: str = Field(..., description="Control action to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")


class SceneConfigUpdate(BaseModel):
    """Request model for scene configuration updates."""
    camera_position: Optional[List[float]] = Field(None, description="Camera position [x, y, z]")
    camera_target: Optional[List[float]] = Field(None, description="Camera target [x, y, z]")
    scene_bounds: Optional[List[float]] = Field(None, description="Scene bounds [width, height, depth]")
    agent_spacing: Optional[float] = Field(None, ge=1.0, le=20.0, description="Agent spacing")
    animation_speed: Optional[float] = Field(None, ge=0.1, le=5.0, description="Animation speed")
    show_grid: Optional[bool] = Field(None, description="Show grid")
    show_connections: Optional[bool] = Field(None, description="Show connections")
    show_metrics_overlay: Optional[bool] = Field(None, description="Show metrics overlay")


# 3D Scene Management Endpoints

@router.get("/scene/state")
async def get_scene_state():
    """Get current 3D scene state including agents, connections, and incidents."""
    try:
        visual_dashboard = get_visual_dashboard()
        scene_state = await visual_dashboard.get_scene_state()
        
        return {
            "status": "success",
            "data": scene_state,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting scene state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scene/initialize")
async def initialize_scene():
    """Initialize 3D scene with default configuration."""
    try:
        visual_dashboard = get_visual_dashboard()
        scene_data = await visual_dashboard.initialize_3d_scene()
        
        return {
            "status": "success",
            "message": "3D scene initialized",
            "data": scene_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error initializing scene: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scene/clear")
async def clear_scene():
    """Clear all agents, connections, and incidents from scene."""
    try:
        visual_dashboard = get_visual_dashboard()
        await visual_dashboard.clear_scene()
        
        return {
            "status": "success",
            "message": "3D scene cleared",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing scene: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/scene/config")
async def update_scene_config(config_update: SceneConfigUpdate):
    """Update 3D scene configuration."""
    try:
        visual_dashboard = get_visual_dashboard()
        
        # Convert Pydantic model to dict, excluding None values
        config_dict = {k: v for k, v in config_update.model_dump().items() if v is not None}
        
        await visual_dashboard.update_scene_config(config_dict)
        
        return {
            "status": "success",
            "message": "Scene configuration updated",
            "updated_config": config_dict,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating scene config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Agent Management Endpoints

@router.post("/agents/add")
async def add_agent_to_scene(agent_request: Agent3DRequest):
    """Add an agent to the 3D scene."""
    try:
        visual_dashboard = get_visual_dashboard()
        
        custom_position = None
        if agent_request.position:
            pos = agent_request.position
            custom_position = (pos.get("x", 0), pos.get("y", 0), pos.get("z", 0))
        
        await visual_dashboard.add_agent(
            agent_id=agent_request.agent_id,
            agent_type=agent_request.agent_type,
            custom_position=custom_position
        )
        
        return {
            "status": "success",
            "message": f"Agent {agent_request.agent_id} added to scene",
            "agent_id": agent_request.agent_id,
            "agent_type": agent_request.agent_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error adding agent to scene: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/agents/state")
async def update_agent_state(state_update: AgentStateUpdate):
    """Update agent state and confidence for visualization."""
    try:
        visual_dashboard = get_visual_dashboard()
        
        # Map string state to AgentState enum
        state_mapping = {
            "idle": AgentState.IDLE,
            "processing": AgentState.PROCESSING,
            "collaborating": AgentState.COLLABORATING,
            "completed": AgentState.COMPLETED,
            "error": AgentState.ERROR
        }
        
        agent_state = state_mapping.get(state_update.state.lower(), AgentState.PROCESSING)
        
        await visual_dashboard.update_agent_state(
            agent_id=state_update.agent_id,
            state=agent_state,
            confidence=state_update.confidence
        )
        
        return {
            "status": "success",
            "message": f"Agent {state_update.agent_id} state updated",
            "agent_id": state_update.agent_id,
            "new_state": state_update.state,
            "confidence": state_update.confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating agent state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/animate")
async def animate_agent_position(
    agent_id: str,
    target_x: float,
    target_y: float,
    target_z: float,
    duration_ms: int = Query(1000, ge=100, le=5000)
):
    """Animate agent movement to new position."""
    try:
        visual_dashboard = get_visual_dashboard()
        
        await visual_dashboard.animate_agent_to_position(
            agent_id=agent_id,
            target_position=(target_x, target_y, target_z),
            duration_ms=duration_ms
        )
        
        return {
            "status": "success",
            "message": f"Agent {agent_id} animation started",
            "agent_id": agent_id,
            "target_position": {"x": target_x, "y": target_y, "z": target_z},
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error animating agent position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Connection Management Endpoints

@router.post("/connections/create")
async def create_agent_connection(connection_request: AgentConnectionRequest):
    """Create visual connection between two agents."""
    try:
        visual_dashboard = get_visual_dashboard()
        
        await visual_dashboard.create_agent_connection(
            from_agent=connection_request.from_agent,
            to_agent=connection_request.to_agent,
            connection_type=connection_request.connection_type,
            strength=connection_request.strength,
            duration_ms=connection_request.duration_ms
        )
        
        return {
            "status": "success",
            "message": "Agent connection created",
            "connection": {
                "from_agent": connection_request.from_agent,
                "to_agent": connection_request.to_agent,
                "type": connection_request.connection_type,
                "strength": connection_request.strength,
                "duration_ms": connection_request.duration_ms
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating agent connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Incident Visualization Endpoints

@router.post("/incidents/add")
async def add_incident_visualization(incident_request: IncidentVisualizationRequest):
    """Add incident visualization to 3D scene."""
    try:
        visual_dashboard = get_visual_dashboard()
        
        await visual_dashboard.add_incident_visualization(
            incident_id=incident_request.incident_id,
            title=incident_request.title,
            severity=incident_request.severity,
            affected_agents=incident_request.affected_agents
        )
        
        return {
            "status": "success",
            "message": "Incident visualization added",
            "incident": {
                "id": incident_request.incident_id,
                "title": incident_request.title,
                "severity": incident_request.severity,
                "affected_agents": incident_request.affected_agents
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error adding incident visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/incidents/{incident_id}/status")
async def update_incident_status(incident_id: str, status: str):
    """Update incident visualization status."""
    try:
        visual_dashboard = get_visual_dashboard()
        
        await visual_dashboard.update_incident_status(incident_id, status)
        
        return {
            "status": "success",
            "message": f"Incident {incident_id} status updated",
            "incident_id": incident_id,
            "new_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating incident status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Camera Control Endpoints

@router.post("/camera/position")
async def set_camera_position(camera_request: CameraPositionRequest):
    """Set camera position using preset or custom coordinates."""
    try:
        demo_controller = get_interactive_demo_controller()
        
        if camera_request.preset_name:
            result = await demo_controller.set_camera_position(
                preset_name=camera_request.preset_name,
                animate=camera_request.animate,
                duration_ms=camera_request.duration_ms
            )
        else:
            # Handle custom position (would need to be implemented)
            raise HTTPException(status_code=400, detail="Custom camera positions not yet implemented")
        
        return {
            "status": "success",
            "message": "Camera position updated",
            "camera": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error setting camera position: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/camera/presets")
async def get_camera_presets():
    """Get available camera presets."""
    try:
        demo_controller = get_interactive_demo_controller()
        
        return {
            "status": "success",
            "presets": list(demo_controller.camera_presets.keys()),
            "current_camera": demo_controller.current_camera,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting camera presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Demo Control Endpoints

@router.post("/demo/initialize")
async def initialize_demo_interface():
    """Initialize interactive demo interface."""
    try:
        demo_controller = get_interactive_demo_controller()
        scene_state = await demo_controller.initialize_demo_interface()
        
        return {
            "status": "success",
            "message": "Demo interface initialized",
            "data": scene_state,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error initializing demo interface: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demo/scenario/{scenario_id}")
async def start_interactive_scenario(scenario_id: str, custom_config: Optional[Dict[str, Any]] = None):
    """Start an interactive demo scenario with 3D controls."""
    try:
        demo_controller = get_interactive_demo_controller()
        result = await demo_controller.start_interactive_scenario(scenario_id, custom_config)
        
        return {
            "status": "success",
            "message": f"Interactive scenario {scenario_id} started",
            "data": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting interactive scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demo/control")
async def handle_demo_control(control_request: DemoControlRequest):
    """Handle interactive demo control actions."""
    try:
        demo_controller = get_interactive_demo_controller()
        result = await demo_controller.handle_demo_control(
            action=control_request.action,
            parameters=control_request.parameters
        )
        
        return {
            "status": "success",
            "message": f"Demo control action {control_request.action} executed",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error handling demo control: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demo/scenarios")
async def get_demo_scenarios():
    """Get available demo scenarios."""
    try:
        demo_controller = get_interactive_demo_controller()
        
        return {
            "status": "success",
            "scenarios": {name: {
                "name": config.name,
                "description": config.description,
                "duration_seconds": config.duration_seconds,
                "complexity": config.complexity,
                "agents_involved": config.agents_involved,
                "key_features": config.key_features
            } for name, config in demo_controller.demo_scenarios.items()},
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting demo scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demo/controls/state")
async def get_demo_controls_state():
    """Get current state of demo controls."""
    try:
        demo_controller = get_interactive_demo_controller()
        state = await demo_controller.get_demo_controls_state()
        
        return {
            "status": "success",
            "data": state,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting demo controls state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Real-time Visualization Endpoints

@router.get("/visualization/metrics")
async def get_visualization_metrics():
    """Get real-time visualization performance metrics."""
    try:
        realtime_visualizer = get_realtime_visualizer()
        metrics = await realtime_visualizer.get_visualization_metrics()
        
        return {
            "status": "success",
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting visualization metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visualization/toggle")
async def toggle_visualization(enabled: bool):
    """Enable or disable real-time visualization."""
    try:
        realtime_visualizer = get_realtime_visualizer()
        await realtime_visualizer.toggle_visualization(enabled)
        
        return {
            "status": "success",
            "message": f"Visualization {'enabled' if enabled else 'disabled'}",
            "enabled": enabled,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error toggling visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket Endpoint for Real-time 3D Updates

@router.websocket("/ws")
async def websocket_3d_visualization(websocket: WebSocket):
    """
    WebSocket endpoint for real-time 3D visualization updates.
    
    Provides dedicated WebSocket connection for 3D visualization data including:
    - Agent state changes
    - Connection animations
    - Incident visualizations
    - Performance metrics
    - Camera controls
    """
    websocket_manager = get_websocket_manager()
    
    try:
        # Accept connection and register for 3D updates
        await websocket_manager.connect(websocket, {
            "connection_type": "3d_visualization",
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "origin": websocket.headers.get("origin", "unknown")
        })
        
        # Send initial 3D scene state
        visual_dashboard = get_visual_dashboard()
        scene_state = await visual_dashboard.get_scene_state()
        
        await websocket_manager.send_to_connection(websocket, {
            "type": "3d_initial_state",
            "data": scene_state
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    # Handle client-side 3D events
                    if message_type == "3d_frame_rendered":
                        # Client reports frame rendered - update FPS tracking
                        visual_dashboard.increment_frame_count()
                    
                    elif message_type == "3d_interaction":
                        # Handle 3D scene interactions from client
                        interaction_data = message.get("data", {})
                        logger.debug(f"3D interaction: {interaction_data}")
                    
                    elif message_type == "ping":
                        await websocket_manager.send_to_connection(websocket, {
                            "type": "pong",
                            "data": {"timestamp": datetime.utcnow().isoformat()}
                        })
                
                except json.JSONDecodeError:
                    # Ignore malformed messages
                    pass
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket 3D error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket 3D connection error: {e}")
    finally:
        await websocket_manager.disconnect(websocket)


# Health Check Endpoint

@router.get("/health")
async def health_check():
    """Health check for 3D visualization services."""
    try:
        visual_dashboard = get_visual_dashboard()
        scene_state = await visual_dashboard.get_scene_state()
        
        realtime_visualizer = get_realtime_visualizer()
        viz_metrics = await realtime_visualizer.get_visualization_metrics()
        
        demo_controller = get_interactive_demo_controller()
        demo_state = await demo_controller.get_demo_controls_state()
        
        return {
            "status": "healthy",
            "services": {
                "visual_dashboard": "operational",
                "realtime_visualizer": "operational" if viz_metrics["visualization_enabled"] else "disabled",
                "demo_controller": "operational",
                "websocket_manager": "operational"
            },
            "performance": scene_state["performance"],
            "scene_stats": {
                "agents": len(scene_state["agents"]),
                "connections": len(scene_state["connections"]),
                "incidents": len(scene_state["incidents"])
            },
            "demo_status": {
                "current_scenario": demo_state["current_scenario"],
                "demo_paused": demo_state["demo_paused"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"3D visualization health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/integration/status")
async def get_3d_integration_status():
    """Get 3D visualization WebSocket integration status."""
    try:
        visual_3d_integration = get_visual_3d_integration()
        status = await visual_3d_integration.get_visualization_status()
        
        return {
            "status": "success",
            "integration_status": status,
            "websocket_features": {
                "real_time_streaming": status["streaming_active"],
                "agent_state_updates": True,
                "connection_visualization": True,
                "incident_visualization": True,
                "performance_monitoring": True
            },
            "performance_metrics": {
                "target_fps": status["target_fps"],
                "actual_fps": status["actual_fps"],
                "frames_streamed": status["frames_streamed"],
                "websocket_clients": status["websocket_clients"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting 3D integration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integration/start-streaming")
async def start_3d_streaming():
    """Start real-time 3D visualization streaming."""
    try:
        visual_3d_integration = get_visual_3d_integration()
        await visual_3d_integration.start_real_time_streaming()
        
        return {
            "status": "success",
            "message": "3D visualization streaming started",
            "streaming_active": True,
            "target_fps": 60,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting 3D streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integration/stop-streaming")
async def stop_3d_streaming():
    """Stop real-time 3D visualization streaming."""
    try:
        visual_3d_integration = get_visual_3d_integration()
        await visual_3d_integration.stop_real_time_streaming()
        
        return {
            "status": "success",
            "message": "3D visualization streaming stopped",
            "streaming_active": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error stopping 3D streaming: {e}")
        raise HTTPException(status_code=500, detail=str(e))