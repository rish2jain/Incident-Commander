"""
Enhanced 3D Dashboard for Autonomous Incident Commander

Provides 3D real-time agent visualization with WebSocket-based live updates
and professional presentation layer for judge demos.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import HTTPException
from src.utils.logging import get_logger
from src.models.incident import Incident, IncidentSeverity
from src.services.websocket_manager import get_websocket_manager

logger = get_logger("enhanced_dashboard")


class AgentVisualizationType(Enum):
    """3D visualization types for agents."""
    SPHERE = "sphere"
    CUBE = "cube"
    PYRAMID = "pyramid"
    CYLINDER = "cylinder"


class AgentState(Enum):
    """Agent states for 3D visualization."""
    IDLE = "idle"
    PROCESSING = "processing"
    COLLABORATING = "collaborating"
    ESCALATING = "escalating"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class Agent3DPosition:
    """3D position and visualization data for an agent."""
    agent_name: str
    x: float
    y: float
    z: float
    visualization_type: AgentVisualizationType
    state: AgentState
    confidence: float
    color: str
    size: float
    animation: str
    connections: List[str]  # Connected agent names
    last_updated: datetime


@dataclass
class AgentConnection:
    """3D connection between agents."""
    from_agent: str
    to_agent: str
    connection_type: str  # "data_flow", "consensus", "escalation"
    strength: float  # 0.0 to 1.0
    color: str
    animated: bool
    last_activity: datetime


@dataclass
class Dashboard3DScene:
    """Complete 3D scene data for dashboard."""
    agents: List[Agent3DPosition]
    connections: List[AgentConnection]
    incident_visualization: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    timestamp: datetime
    scene_id: str


class Enhanced3DDashboard:
    """Enhanced 3D Dashboard with real-time agent visualization."""
    
    def __init__(self):
        self.websocket_manager = get_websocket_manager()
        self.agent_positions: Dict[str, Agent3DPosition] = {}
        self.agent_connections: List[AgentConnection] = []
        self.active_incidents: Dict[str, Dict[str, Any]] = {}
        self.scene_history: List[Dashboard3DScene] = []
        
        # 3D Scene Configuration
        self.agent_layout = {
            "detection": {"x": -2.0, "y": 0.0, "z": 0.0, "type": AgentVisualizationType.SPHERE},
            "diagnosis": {"x": 0.0, "y": 2.0, "z": 0.0, "type": AgentVisualizationType.CUBE},
            "prediction": {"x": 2.0, "y": 0.0, "z": 0.0, "type": AgentVisualizationType.PYRAMID},
            "resolution": {"x": 0.0, "y": -2.0, "z": 0.0, "type": AgentVisualizationType.CYLINDER},
            "communication": {"x": 0.0, "y": 0.0, "z": 2.0, "type": AgentVisualizationType.SPHERE}
        }
        
        self.state_colors = {
            AgentState.IDLE: "#4A90E2",
            AgentState.PROCESSING: "#F5A623",
            AgentState.COLLABORATING: "#7ED321",
            AgentState.ESCALATING: "#D0021B",
            AgentState.COMPLETED: "#50E3C2",
            AgentState.ERROR: "#B91C1C"
        }
        
        self.connection_colors = {
            "data_flow": "#4A90E2",
            "consensus": "#F5A623",
            "escalation": "#D0021B"
        }
        
        # Initialize agent positions
        self._initialize_agent_positions()
        
        logger.info("Enhanced 3D Dashboard initialized with agent visualization")
    
    def _initialize_agent_positions(self):
        """Initialize 3D positions for all agents."""
        for agent_name, layout in self.agent_layout.items():
            self.agent_positions[agent_name] = Agent3DPosition(
                agent_name=agent_name,
                x=layout["x"],
                y=layout["y"],
                z=layout["z"],
                visualization_type=layout["type"],
                state=AgentState.IDLE,
                confidence=0.0,
                color=self.state_colors[AgentState.IDLE],
                size=1.0,
                animation="idle",
                connections=[],
                last_updated=datetime.utcnow()
            )
    
    async def update_agent_state(self, agent_name: str, state: AgentState, 
                               confidence: float = 0.0, connections: List[str] = None):
        """Update agent state and trigger 3D visualization update."""
        if agent_name not in self.agent_positions:
            logger.warning(f"Unknown agent: {agent_name}")
            return
        
        agent = self.agent_positions[agent_name]
        agent.state = state
        agent.confidence = confidence
        agent.color = self.state_colors[state]
        agent.connections = connections or []
        agent.last_updated = datetime.utcnow()
        
        # Update size and animation based on state
        if state == AgentState.PROCESSING:
            agent.size = 1.2
            agent.animation = "pulse"
        elif state == AgentState.COLLABORATING:
            agent.size = 1.1
            agent.animation = "rotate"
        elif state == AgentState.ESCALATING:
            agent.size = 1.3
            agent.animation = "flash"
        else:
            agent.size = 1.0
            agent.animation = "idle"
        
        # Update connections
        await self._update_agent_connections(agent_name, connections or [])
        
        # Broadcast update via WebSocket
        await self._broadcast_agent_update(agent_name)
        
        logger.info(f"Updated agent {agent_name} state to {state.value} with confidence {confidence}")
    
    async def _update_agent_connections(self, agent_name: str, connected_agents: List[str]):
        """Update 3D connections between agents."""
        # Remove old connections from this agent
        self.agent_connections = [
            conn for conn in self.agent_connections 
            if conn.from_agent != agent_name
        ]
        
        # Add new connections
        for connected_agent in connected_agents:
            if connected_agent in self.agent_positions:
                connection_type = self._determine_connection_type(agent_name, connected_agent)
                
                self.agent_connections.append(AgentConnection(
                    from_agent=agent_name,
                    to_agent=connected_agent,
                    connection_type=connection_type,
                    strength=0.8,
                    color=self.connection_colors[connection_type],
                    animated=True,
                    last_activity=datetime.utcnow()
                ))
    
    def _determine_connection_type(self, from_agent: str, to_agent: str) -> str:
        """Determine the type of connection between agents."""
        # Define connection types based on agent relationships
        data_flow_patterns = [
            ("detection", "diagnosis"),
            ("diagnosis", "prediction"),
            ("prediction", "resolution"),
            ("resolution", "communication")
        ]
        
        consensus_patterns = [
            ("detection", "prediction"),
            ("diagnosis", "resolution"),
            ("prediction", "communication")
        ]
        
        if (from_agent, to_agent) in data_flow_patterns:
            return "data_flow"
        elif (from_agent, to_agent) in consensus_patterns:
            return "consensus"
        else:
            return "escalation"
    
    async def update_incident_visualization(self, incident: Incident, phase: str, 
                                          metrics: Dict[str, Any]):
        """Update incident visualization in 3D space."""
        incident_viz = {
            "incident_id": incident.id,
            "title": incident.title,
            "severity": incident.severity,  # Already a string due to use_enum_values=True
            "phase": phase,
            "position": {"x": 0.0, "y": 0.0, "z": -1.0},
            "size": self._calculate_incident_size(incident.severity),
            "color": self._get_severity_color(incident.severity),
            "animation": "orbit",
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.active_incidents[incident.id] = incident_viz
        
        # Broadcast incident update
        await self._broadcast_incident_update(incident.id)
    
    def _calculate_incident_size(self, severity) -> float:
        """Calculate 3D size based on incident severity."""
        # Handle both enum and string values
        if hasattr(severity, 'value'):
            severity_str = severity.value
        else:
            severity_str = severity
            
        size_map = {
            "low": 0.5,
            "medium": 0.7,
            "high": 1.0,
            "critical": 1.5
        }
        return size_map.get(severity_str, 0.7)
    
    def _get_severity_color(self, severity) -> str:
        """Get color for incident severity."""
        # Handle both enum and string values
        if hasattr(severity, 'value'):
            severity_str = severity.value
        else:
            severity_str = severity
            
        color_map = {
            "low": "#4A90E2",
            "medium": "#F5A623",
            "high": "#D0021B",
            "critical": "#8B0000"
        }
        return color_map.get(severity_str, "#4A90E2")
    
    async def get_current_3d_scene(self) -> Dashboard3DScene:
        """Get current complete 3D scene data."""
        # Calculate performance metrics
        performance_metrics = await self._calculate_performance_metrics()
        
        # Create scene
        scene = Dashboard3DScene(
            agents=list(self.agent_positions.values()),
            connections=self.agent_connections,
            incident_visualization=dict(self.active_incidents),
            performance_metrics=performance_metrics,
            timestamp=datetime.utcnow(),
            scene_id=f"scene_{int(datetime.utcnow().timestamp())}"
        )
        
        # Store in history (keep last 100 scenes)
        self.scene_history.append(scene)
        if len(self.scene_history) > 100:
            self.scene_history.pop(0)
        
        return scene
    
    async def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate real-time performance metrics for visualization."""
        active_agents = sum(1 for agent in self.agent_positions.values() 
                          if agent.state != AgentState.IDLE)
        
        avg_confidence = sum(agent.confidence for agent in self.agent_positions.values()) / len(self.agent_positions)
        
        active_connections = len([conn for conn in self.agent_connections 
                                if conn.last_activity > datetime.utcnow() - timedelta(minutes=5)])
        
        return {
            "active_agents": active_agents,
            "total_agents": len(self.agent_positions),
            "average_confidence": avg_confidence,
            "active_connections": active_connections,
            "active_incidents": len(self.active_incidents),
            "system_health": "healthy" if avg_confidence > 0.7 else "degraded"
        }
    
    async def _broadcast_agent_update(self, agent_name: str):
        """Broadcast agent update via WebSocket."""
        if agent_name in self.agent_positions:
            agent = self.agent_positions[agent_name]
            update_data = {
                "type": "agent_update",
                "data": asdict(agent),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.websocket_manager.broadcast(update_data)
    
    async def _broadcast_incident_update(self, incident_id: str):
        """Broadcast incident update via WebSocket."""
        if incident_id in self.active_incidents:
            incident_viz = self.active_incidents[incident_id]
            update_data = {
                "type": "incident_update",
                "data": incident_viz,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self.websocket_manager.broadcast(update_data)
    
    async def broadcast_full_scene(self):
        """Broadcast complete 3D scene to all connected clients."""
        scene = await self.get_current_3d_scene()
        scene_data = {
            "type": "full_scene_update",
            "data": asdict(scene),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.websocket_manager.broadcast(scene_data)
    
    async def get_scene_history(self, minutes: int = 30) -> List[Dashboard3DScene]:
        """Get scene history for the last N minutes."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [scene for scene in self.scene_history if scene.timestamp > cutoff_time]
    
    async def simulate_agent_activity(self, incident_id: str):
        """Simulate realistic agent activity for demo purposes."""
        # Detection phase
        await self.update_agent_state("detection", AgentState.PROCESSING, 0.8, [])
        await asyncio.sleep(1)
        
        # Diagnosis phase
        await self.update_agent_state("detection", AgentState.COMPLETED, 0.9, ["diagnosis"])
        await self.update_agent_state("diagnosis", AgentState.PROCESSING, 0.7, ["detection"])
        await asyncio.sleep(2)
        
        # Prediction and consensus
        await self.update_agent_state("diagnosis", AgentState.COLLABORATING, 0.8, ["prediction"])
        await self.update_agent_state("prediction", AgentState.PROCESSING, 0.75, ["diagnosis"])
        await asyncio.sleep(1)
        
        # Resolution phase
        await self.update_agent_state("prediction", AgentState.COMPLETED, 0.85, ["resolution"])
        await self.update_agent_state("resolution", AgentState.PROCESSING, 0.9, ["prediction"])
        await asyncio.sleep(2)
        
        # Communication phase
        await self.update_agent_state("resolution", AgentState.COMPLETED, 0.95, ["communication"])
        await self.update_agent_state("communication", AgentState.PROCESSING, 0.9, ["resolution"])
        await asyncio.sleep(1)
        
        # Complete
        await self.update_agent_state("communication", AgentState.COMPLETED, 0.95, [])
        
        # Reset to idle after 5 seconds
        await asyncio.sleep(5)
        for agent_name in self.agent_positions.keys():
            await self.update_agent_state(agent_name, AgentState.IDLE, 0.0, [])


# Global instance
_enhanced_dashboard: Optional[Enhanced3DDashboard] = None


def get_enhanced_dashboard() -> Enhanced3DDashboard:
    """Get the global enhanced dashboard instance."""
    global _enhanced_dashboard
    if _enhanced_dashboard is None:
        _enhanced_dashboard = Enhanced3DDashboard()
    return _enhanced_dashboard


def add_enhanced_dashboard_routes(app):
    """Add enhanced dashboard routes to FastAPI app."""
    dashboard = get_enhanced_dashboard()
    
    @app.get("/dashboard/enhanced")
    async def get_enhanced_dashboard_data():
        """Get current 3D dashboard scene data."""
        scene = await dashboard.get_current_3d_scene()
        return {
            "dashboard_3d": asdict(scene),
            "features": {
                "real_time_updates": True,
                "3d_visualization": True,
                "agent_coordination_display": True,
                "interactive_controls": True,
                "performance_metrics": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @app.get("/dashboard/enhanced/history")
    async def get_dashboard_history(minutes: int = 30):
        """Get dashboard scene history."""
        # Input validation
        if minutes < 1 or minutes > 1440:  # Max 24 hours
            raise HTTPException(status_code=400, detail="minutes must be between 1 and 1440")
        
        history = await dashboard.get_scene_history(minutes)
        return {
            "scene_history": [asdict(scene) for scene in history],
            "total_scenes": len(history),
            "time_range_minutes": minutes,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @app.post("/dashboard/enhanced/simulate/{incident_id}")
    async def simulate_dashboard_activity(incident_id: str):
        """Simulate agent activity for demo purposes."""
        await dashboard.simulate_agent_activity(incident_id)
        return {
            "simulation_started": True,
            "incident_id": incident_id,
            "message": "Agent activity simulation started",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @app.get("/dashboard/enhanced/agents/{agent_name}")
    async def get_agent_3d_data(agent_name: str):
        """Get specific agent 3D visualization data."""
        if agent_name not in dashboard.agent_positions:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent = dashboard.agent_positions[agent_name]
        return {
            "agent_3d_data": asdict(agent),
            "connections": [
                asdict(conn) for conn in dashboard.agent_connections 
                if conn.from_agent == agent_name or conn.to_agent == agent_name
            ],
            "timestamp": datetime.utcnow().isoformat()
        }