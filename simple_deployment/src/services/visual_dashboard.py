"""
3D Visual Dashboard service for real-time agent visualization.

Provides 3D scene management, agent positioning, and state visualization
for enhanced demo presentations and system monitoring.
"""

import asyncio
import json
import math
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from src.utils.logging import get_logger
from src.services.websocket_manager import get_websocket_manager, WebSocketMessage

logger = get_logger("visual_dashboard")


class AgentState(Enum):
    """Agent visualization states."""
    IDLE = "idle"
    PROCESSING = "processing"
    COLLABORATING = "collaborating"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class Agent3DPosition:
    """3D position and state for agent visualization."""
    agent_id: str
    agent_type: str
    x: float
    y: float
    z: float
    state: AgentState
    confidence: float = 1.0
    last_updated: str = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.utcnow().isoformat()


@dataclass
class AgentConnection:
    """Connection between two agents for visualization."""
    from_agent: str
    to_agent: str
    connection_type: str  # "message", "data", "consensus"
    strength: float  # 0.0 to 1.0
    created_at: str
    duration_ms: int = 2000  # How long to show the connection
    
    def __post_init__(self):
        if not hasattr(self, 'created_at') or self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class IncidentVisualization:
    """3D visualization data for an incident."""
    incident_id: str
    title: str
    severity: str
    position: Tuple[float, float, float]  # Center position
    radius: float  # Visualization radius
    affected_agents: List[str]
    created_at: str
    status: str = "active"  # active, resolving, resolved
    
    def __post_init__(self):
        if not hasattr(self, 'created_at') or self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class Scene3DConfiguration:
    """3D scene configuration parameters."""
    camera_position: Tuple[float, float, float] = (0, 10, 15)
    camera_target: Tuple[float, float, float] = (0, 0, 0)
    scene_bounds: Tuple[float, float, float] = (20, 15, 20)  # width, height, depth
    agent_spacing: float = 5.0
    animation_speed: float = 1.0
    show_grid: bool = True
    show_connections: bool = True
    show_metrics_overlay: bool = True


class VisualDashboard:
    """
    3D Visual Dashboard for real-time agent visualization.
    
    Manages 3D scene state, agent positioning, and real-time updates
    for enhanced demo presentations and system monitoring.
    """
    
    def __init__(self):
        self.scene_config = Scene3DConfiguration()
        self.agents: Dict[str, Agent3DPosition] = {}
        self.connections: List[AgentConnection] = []
        self.incidents: Dict[str, IncidentVisualization] = {}
        self.websocket_manager = get_websocket_manager()
        
        # Agent type positioning (circular arrangement)
        self.agent_type_positions = {
            "detection": (0, 0, 8),
            "diagnosis": (-6, 0, 4),
            "prediction": (6, 0, 4),
            "resolution": (0, 0, -4),
            "communication": (0, 0, -8)
        }
        
        # Performance metrics
        self.frame_count = 0
        self.last_fps_check = time.time()
        self.current_fps = 60.0
        
        logger.info("3D Visual Dashboard initialized")
    
    async def initialize_3d_scene(self) -> Dict[str, Any]:
        """
        Initialize 3D visualization environment.
        
        Returns:
            Scene configuration and initial state
        """
        scene_data = {
            "scene_config": asdict(self.scene_config),
            "agents": {agent_id: asdict(agent) for agent_id, agent in self.agents.items()},
            "connections": [asdict(conn) for conn in self.connections],
            "incidents": {inc_id: asdict(inc) for inc_id, inc in self.incidents.items()},
            "timestamp": datetime.utcnow().isoformat(),
            "performance": {
                "target_fps": 60,
                "current_fps": self.current_fps,
                "frame_count": self.frame_count
            }
        }
        
        # Broadcast scene initialization to connected clients
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_scene_initialized",
            timestamp=datetime.utcnow(),
            data=scene_data
        ))
        
        logger.info("3D scene initialized with configuration")
        return scene_data
    
    async def add_agent(self, agent_id: str, agent_type: str, 
                       custom_position: Optional[Tuple[float, float, float]] = None) -> None:
        """Add an agent to the 3D scene."""
        if custom_position:
            x, y, z = custom_position
        else:
            # Use predefined position for agent type
            base_x, base_y, base_z = self.agent_type_positions.get(
                agent_type, (0, 0, 0)
            )
            
            # Add slight randomization to avoid overlap
            x = base_x + (hash(agent_id) % 200 - 100) / 100.0  # ±1.0 variation
            y = base_y + (hash(agent_id) % 100) / 100.0        # 0-1.0 variation
            z = base_z + (hash(agent_id) % 200 - 100) / 100.0  # ±1.0 variation
        
        agent_position = Agent3DPosition(
            agent_id=agent_id,
            agent_type=agent_type,
            x=x, y=y, z=z,
            state=AgentState.IDLE
        )
        
        self.agents[agent_id] = agent_position
        
        # Broadcast agent addition
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_agent_added",
            timestamp=datetime.utcnow(),
            data={
                "agent": asdict(agent_position),
                "scene_stats": {
                    "total_agents": len(self.agents),
                    "active_connections": len(self.connections)
                }
            }
        ))
        
        logger.info(f"Added agent {agent_id} ({agent_type}) to 3D scene at ({x:.1f}, {y:.1f}, {z:.1f})")
    
    async def update_agent_state(self, agent_id: str, state: AgentState, 
                               confidence: float = None) -> None:
        """Update agent state and confidence for visualization."""
        if agent_id not in self.agents:
            logger.warning(f"Agent {agent_id} not found in 3D scene")
            return
        
        agent = self.agents[agent_id]
        agent.state = state
        if confidence is not None:
            agent.confidence = max(0.0, min(1.0, confidence))
        agent.last_updated = datetime.utcnow().isoformat()
        
        # Broadcast agent state update
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_agent_state_updated",
            timestamp=datetime.utcnow(),
            data={
                "agent_id": agent_id,
                "state": state.value,
                "confidence": agent.confidence,
                "position": {"x": agent.x, "y": agent.y, "z": agent.z},
                "timestamp": agent.last_updated
            }
        ))
        
        logger.debug(f"Updated agent {agent_id} state to {state.value} (confidence: {agent.confidence:.2f})")
    
    async def animate_agent_to_position(self, agent_id: str, 
                                      target_position: Tuple[float, float, float],
                                      duration_ms: int = 1000) -> None:
        """Animate agent movement to new position."""
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        start_pos = (agent.x, agent.y, agent.z)
        target_x, target_y, target_z = target_position
        
        # Broadcast animation start
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_agent_animation",
            timestamp=datetime.utcnow(),
            data={
                "agent_id": agent_id,
                "animation_type": "move",
                "start_position": {"x": start_pos[0], "y": start_pos[1], "z": start_pos[2]},
                "target_position": {"x": target_x, "y": target_y, "z": target_z},
                "duration_ms": duration_ms,
                "easing": "ease-in-out"
            }
        ))
        
        # Update agent position immediately (client handles animation)
        agent.x, agent.y, agent.z = target_position
        agent.last_updated = datetime.utcnow().isoformat()
        
        logger.debug(f"Animating agent {agent_id} to position ({target_x:.1f}, {target_y:.1f}, {target_z:.1f})")
    
    async def create_agent_connection(self, from_agent: str, to_agent: str,
                                    connection_type: str = "message",
                                    strength: float = 1.0,
                                    duration_ms: int = 2000) -> None:
        """Create visual connection between two agents."""
        if from_agent not in self.agents or to_agent not in self.agents:
            logger.warning(f"Cannot create connection: agent not found ({from_agent} -> {to_agent})")
            return
        
        connection = AgentConnection(
            from_agent=from_agent,
            to_agent=to_agent,
            connection_type=connection_type,
            strength=strength,
            created_at=datetime.utcnow().isoformat(),
            duration_ms=duration_ms
        )
        
        self.connections.append(connection)
        
        # Broadcast connection creation
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_agent_connection",
            timestamp=datetime.utcnow(),
            data={
                "connection": asdict(connection),
                "from_position": {
                    "x": self.agents[from_agent].x,
                    "y": self.agents[from_agent].y,
                    "z": self.agents[from_agent].z
                },
                "to_position": {
                    "x": self.agents[to_agent].x,
                    "y": self.agents[to_agent].y,
                    "z": self.agents[to_agent].z
                }
            }
        ))
        
        # Schedule connection cleanup
        asyncio.create_task(self._cleanup_connection_after_delay(connection, duration_ms))
        
        logger.debug(f"Created {connection_type} connection: {from_agent} -> {to_agent}")
    
    async def add_incident_visualization(self, incident_id: str, title: str,
                                       severity: str, affected_agents: List[str]) -> None:
        """Add incident visualization to 3D scene."""
        # Calculate center position based on affected agents
        if affected_agents and all(agent_id in self.agents for agent_id in affected_agents):
            positions = [self.agents[agent_id] for agent_id in affected_agents]
            center_x = sum(pos.x for pos in positions) / len(positions)
            center_y = sum(pos.y for pos in positions) / len(positions) + 2.0  # Elevated
            center_z = sum(pos.z for pos in positions) / len(positions)
        else:
            center_x, center_y, center_z = 0, 3, 0  # Default center position
        
        # Radius based on severity
        radius_map = {"low": 1.0, "medium": 1.5, "high": 2.0, "critical": 2.5}
        radius = radius_map.get(severity, 1.5)
        
        incident_viz = IncidentVisualization(
            incident_id=incident_id,
            title=title,
            severity=severity,
            position=(center_x, center_y, center_z),
            radius=radius,
            affected_agents=affected_agents,
            created_at=datetime.utcnow().isoformat()
        )
        
        self.incidents[incident_id] = incident_viz
        
        # Broadcast incident visualization
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_incident_added",
            timestamp=datetime.utcnow(),
            data={
                "incident": asdict(incident_viz),
                "affected_agent_positions": [
                    {
                        "agent_id": agent_id,
                        "position": {
                            "x": self.agents[agent_id].x,
                            "y": self.agents[agent_id].y,
                            "z": self.agents[agent_id].z
                        }
                    }
                    for agent_id in affected_agents
                    if agent_id in self.agents
                ]
            }
        ))
        
        logger.info(f"Added incident visualization: {incident_id} ({severity}) at ({center_x:.1f}, {center_y:.1f}, {center_z:.1f})")
    
    async def update_incident_status(self, incident_id: str, status: str) -> None:
        """Update incident visualization status."""
        if incident_id not in self.incidents:
            return
        
        self.incidents[incident_id].status = status
        
        # Broadcast incident status update
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_incident_updated",
            timestamp=datetime.utcnow(),
            data={
                "incident_id": incident_id,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        # Remove resolved incidents after delay
        if status == "resolved":
            asyncio.create_task(self._cleanup_incident_after_delay(incident_id, 3000))
        
        logger.debug(f"Updated incident {incident_id} status to {status}")
    
    async def get_scene_state(self) -> Dict[str, Any]:
        """Get current 3D scene state."""
        # Update FPS calculation
        current_time = time.time()
        if current_time - self.last_fps_check >= 1.0:
            self.current_fps = self.frame_count / (current_time - self.last_fps_check)
            self.frame_count = 0
            self.last_fps_check = current_time
        
        return {
            "scene_config": asdict(self.scene_config),
            "agents": {agent_id: asdict(agent) for agent_id, agent in self.agents.items()},
            "connections": [asdict(conn) for conn in self.connections],
            "incidents": {inc_id: asdict(inc) for inc_id, inc in self.incidents.items()},
            "performance": {
                "current_fps": round(self.current_fps, 1),
                "frame_count": self.frame_count,
                "target_fps": 60,
                "agents_count": len(self.agents),
                "connections_count": len(self.connections),
                "incidents_count": len(self.incidents)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def update_scene_config(self, config_updates: Dict[str, Any]) -> None:
        """Update 3D scene configuration."""
        for key, value in config_updates.items():
            if hasattr(self.scene_config, key):
                setattr(self.scene_config, key, value)
        
        # Broadcast configuration update
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_scene_config_updated",
            timestamp=datetime.utcnow(),
            data={
                "config": asdict(self.scene_config),
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        logger.info(f"Updated 3D scene configuration: {config_updates}")
    
    async def clear_scene(self) -> None:
        """Clear all agents, connections, and incidents from scene."""
        self.agents.clear()
        self.connections.clear()
        self.incidents.clear()
        
        # Broadcast scene clear
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="3d_scene_cleared",
            timestamp=datetime.utcnow(),
            data={"timestamp": datetime.utcnow().isoformat()}
        ))
        
        logger.info("Cleared 3D scene")
    
    def increment_frame_count(self) -> None:
        """Increment frame count for FPS calculation."""
        self.frame_count += 1
    
    async def _cleanup_connection_after_delay(self, connection: AgentConnection, delay_ms: int) -> None:
        """Remove connection after specified delay."""
        await asyncio.sleep(delay_ms / 1000.0)
        
        if connection in self.connections:
            self.connections.remove(connection)
            
            # Broadcast connection removal
            await self.websocket_manager.broadcast(WebSocketMessage(
                type="3d_connection_removed",
                timestamp=datetime.utcnow(),
                data={
                    "from_agent": connection.from_agent,
                    "to_agent": connection.to_agent,
                    "connection_type": connection.connection_type
                }
            ))
    
    async def _cleanup_incident_after_delay(self, incident_id: str, delay_ms: int) -> None:
        """Remove incident visualization after specified delay."""
        await asyncio.sleep(delay_ms / 1000.0)
        
        if incident_id in self.incidents:
            del self.incidents[incident_id]
            
            # Broadcast incident removal
            await self.websocket_manager.broadcast(WebSocketMessage(
                type="3d_incident_removed",
                timestamp=datetime.utcnow(),
                data={"incident_id": incident_id}
            ))


# Global visual dashboard instance
_visual_dashboard: Optional[VisualDashboard] = None


def get_visual_dashboard() -> VisualDashboard:
    """Get the global visual dashboard instance."""
    global _visual_dashboard
    if _visual_dashboard is None:
        _visual_dashboard = VisualDashboard()
    return _visual_dashboard