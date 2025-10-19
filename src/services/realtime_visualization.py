"""
Real-time visualization integration service.

Connects the 3D visual dashboard with agent coordination system
for live agent state updates and visual connection rendering.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from src.utils.logging import get_logger
from src.services.visual_dashboard import get_visual_dashboard, AgentState
from src.services.websocket_manager import get_websocket_manager, WebSocketMessage

logger = get_logger("realtime_visualization")


@dataclass
class AgentVisualizationUpdate:
    """Agent visualization update data."""
    agent_id: str
    agent_type: str
    action: str
    state: str
    confidence: float
    details: Dict[str, Any]
    timestamp: str


class RealtimeVisualizationIntegrator:
    """
    Integrates 3D visualization with real-time agent coordination.
    
    Provides live agent state updates, visual connection rendering,
    and synchronized visualization with system events.
    """
    
    def __init__(self):
        self.visual_dashboard = get_visual_dashboard()
        self.websocket_manager = get_websocket_manager()
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_interactions: List[Dict[str, Any]] = []
        self.visualization_enabled = True
        
        # Agent state mapping
        self.state_mapping = {
            "idle": AgentState.IDLE,
            "processing": AgentState.PROCESSING,
            "analyzing": AgentState.PROCESSING,
            "executing": AgentState.PROCESSING,
            "collaborating": AgentState.COLLABORATING,
            "consensus": AgentState.COLLABORATING,
            "completed": AgentState.COMPLETED,
            "success": AgentState.COMPLETED,
            "error": AgentState.ERROR,
            "failed": AgentState.ERROR
        }
        
        logger.info("Real-time visualization integrator initialized")
    
    async def initialize_agent_visualization(self, agents: Dict[str, Any]) -> None:
        """Initialize visualization for all registered agents."""
        if not self.visualization_enabled:
            return
        
        # Clear existing scene
        await self.visual_dashboard.clear_scene()
        
        # Add all agents to 3D scene
        for agent_id, agent_info in agents.items():
            agent_type = agent_info.get("type", "unknown")
            await self.visual_dashboard.add_agent(agent_id, agent_type)
            
            # Track agent in active list
            self.active_agents[agent_id] = {
                "type": agent_type,
                "state": "idle",
                "last_action": None,
                "confidence": 1.0,
                "last_updated": datetime.utcnow().isoformat()
            }
        
        # Initialize 3D scene
        scene_state = await self.visual_dashboard.initialize_3d_scene()
        
        logger.info(f"Initialized visualization for {len(agents)} agents")
        return scene_state
    
    async def update_agent_visualization(self, agent_id: str, action: str,
                                       state: str = "processing",
                                       confidence: float = None,
                                       details: Dict[str, Any] = None) -> None:
        """Update agent visualization with new action and state."""
        if not self.visualization_enabled or agent_id not in self.active_agents:
            return
        
        # Map state to visualization state
        viz_state = self.state_mapping.get(state.lower(), AgentState.PROCESSING)
        
        # Update agent state in visual dashboard
        await self.visual_dashboard.update_agent_state(
            agent_id=agent_id,
            state=viz_state,
            confidence=confidence
        )
        
        # Update tracking data
        self.active_agents[agent_id].update({
            "state": state,
            "last_action": action,
            "confidence": confidence or self.active_agents[agent_id]["confidence"],
            "last_updated": datetime.utcnow().isoformat()
        })
        
        # Create visualization update
        update = AgentVisualizationUpdate(
            agent_id=agent_id,
            agent_type=self.active_agents[agent_id]["type"],
            action=action,
            state=state,
            confidence=confidence or 1.0,
            details=details or {},
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Broadcast agent action visualization
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="agent_visualization_update",
            data={
                "agent_id": agent_id,
                "agent_type": update.agent_type,
                "action": action,
                "state": state,
                "confidence": update.confidence,
                "details": update.details,
                "visualization": {
                    "state_color": self._get_state_color(viz_state),
                    "animation": self._get_state_animation(viz_state),
                    "intensity": confidence or 1.0
                },
                "timestamp": update.timestamp
            }
        ))
        
        logger.debug(f"Updated visualization for agent {agent_id}: {action} ({state})")
    
    async def visualize_agent_communication(self, from_agent: str, to_agent: str,
                                          message_type: str = "message",
                                          data: Dict[str, Any] = None) -> None:
        """Visualize communication between agents."""
        if not self.visualization_enabled:
            return
        
        if from_agent not in self.active_agents or to_agent not in self.active_agents:
            logger.warning(f"Cannot visualize communication: unknown agent ({from_agent} -> {to_agent})")
            return
        
        # Determine connection strength based on message type
        strength_map = {
            "consensus": 1.0,
            "data": 0.8,
            "message": 0.6,
            "status": 0.4,
            "heartbeat": 0.2
        }
        strength = strength_map.get(message_type, 0.6)
        
        # Create visual connection
        await self.visual_dashboard.create_agent_connection(
            from_agent=from_agent,
            to_agent=to_agent,
            connection_type=message_type,
            strength=strength,
            duration_ms=2000
        )
        
        # Track interaction
        interaction = {
            "from_agent": from_agent,
            "to_agent": to_agent,
            "message_type": message_type,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat(),
            "strength": strength
        }
        
        self.agent_interactions.append(interaction)
        
        # Keep only recent interactions (last 50)
        if len(self.agent_interactions) > 50:
            self.agent_interactions = self.agent_interactions[-50:]
        
        # Broadcast communication visualization
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="agent_communication_visual",
            data={
                "communication": interaction,
                "visualization": {
                    "connection_color": self._get_connection_color(message_type),
                    "animation_speed": strength,
                    "particle_count": int(strength * 10) + 5
                }
            }
        ))
        
        logger.debug(f"Visualized communication: {from_agent} -> {to_agent} ({message_type})")
    
    async def visualize_consensus_process(self, agents: List[str], 
                                        consensus_data: Dict[str, Any]) -> None:
        """Visualize multi-agent consensus process."""
        if not self.visualization_enabled or len(agents) < 2:
            return
        
        # Create connections between all participating agents
        for i, agent1 in enumerate(agents):
            for agent2 in agents[i+1:]:
                await self.visual_dashboard.create_agent_connection(
                    from_agent=agent1,
                    to_agent=agent2,
                    connection_type="consensus",
                    strength=0.9,
                    duration_ms=3000
                )
        
        # Update all participating agents to collaborating state
        for agent_id in agents:
            if agent_id in self.active_agents:
                await self.visual_dashboard.update_agent_state(
                    agent_id=agent_id,
                    state=AgentState.COLLABORATING,
                    confidence=consensus_data.get("confidence", 0.8)
                )
        
        # Broadcast consensus visualization
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="consensus_visualization",
            data={
                "participating_agents": agents,
                "consensus_data": consensus_data,
                "visualization": {
                    "type": "consensus_ring",
                    "duration_ms": 3000,
                    "confidence": consensus_data.get("confidence", 0.8)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        logger.info(f"Visualized consensus process with {len(agents)} agents")
    
    async def visualize_incident_processing(self, incident_id: str, incident_data: Dict[str, Any],
                                          affected_agents: List[str]) -> None:
        """Visualize incident processing in 3D space."""
        if not self.visualization_enabled:
            return
        
        # Add incident visualization to scene
        await self.visual_dashboard.add_incident_visualization(
            incident_id=incident_id,
            title=incident_data.get("title", "Unknown Incident"),
            severity=incident_data.get("severity", "medium"),
            affected_agents=affected_agents
        )
        
        # Animate affected agents toward incident center
        for agent_id in affected_agents:
            if agent_id in self.active_agents:
                # Calculate position closer to incident center
                base_pos = self.visual_dashboard.agent_type_positions.get(
                    self.active_agents[agent_id]["type"], (0, 0, 0)
                )
                
                # Move 30% closer to center
                new_x = base_pos[0] * 0.7
                new_y = base_pos[1] + 1.0  # Slightly elevated
                new_z = base_pos[2] * 0.7
                
                await self.visual_dashboard.animate_agent_to_position(
                    agent_id=agent_id,
                    target_position=(new_x, new_y, new_z),
                    duration_ms=1500
                )
        
        # Broadcast incident visualization
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="incident_visualization",
            data={
                "incident_id": incident_id,
                "incident_data": incident_data,
                "affected_agents": affected_agents,
                "visualization": {
                    "type": "incident_focus",
                    "agent_convergence": True,
                    "severity_indicator": incident_data.get("severity", "medium")
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        logger.info(f"Visualized incident processing: {incident_id} with {len(affected_agents)} agents")
    
    async def update_incident_resolution(self, incident_id: str, 
                                       resolution_data: Dict[str, Any]) -> None:
        """Update incident visualization when resolved."""
        if not self.visualization_enabled:
            return
        
        # Update incident status
        await self.visual_dashboard.update_incident_status(incident_id, "resolved")
        
        # Return agents to original positions
        for agent_id, agent_info in self.active_agents.items():
            base_pos = self.visual_dashboard.agent_type_positions.get(
                agent_info["type"], (0, 0, 0)
            )
            
            await self.visual_dashboard.animate_agent_to_position(
                agent_id=agent_id,
                target_position=base_pos,
                duration_ms=2000
            )
            
            # Set agents back to idle state
            await self.visual_dashboard.update_agent_state(
                agent_id=agent_id,
                state=AgentState.COMPLETED,
                confidence=1.0
            )
        
        # Broadcast resolution visualization
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="incident_resolution_visual",
            data={
                "incident_id": incident_id,
                "resolution_data": resolution_data,
                "visualization": {
                    "type": "resolution_celebration",
                    "agent_return": True,
                    "success_indicator": True
                },
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        logger.info(f"Visualized incident resolution: {incident_id}")
    
    async def get_visualization_metrics(self) -> Dict[str, Any]:
        """Get real-time visualization performance metrics."""
        scene_state = await self.visual_dashboard.get_scene_state()
        
        return {
            "performance": scene_state["performance"],
            "active_agents": len(self.active_agents),
            "recent_interactions": len(self.agent_interactions),
            "visualization_enabled": self.visualization_enabled,
            "scene_stats": {
                "agents": len(scene_state["agents"]),
                "connections": len(scene_state["connections"]),
                "incidents": len(scene_state["incidents"])
            },
            "agent_states": {
                agent_id: info["state"] 
                for agent_id, info in self.active_agents.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def toggle_visualization(self, enabled: bool) -> None:
        """Enable or disable real-time visualization."""
        self.visualization_enabled = enabled
        
        if not enabled:
            await self.visual_dashboard.clear_scene()
        
        # Broadcast visualization toggle
        await self.websocket_manager.broadcast(WebSocketMessage(
            type="visualization_toggled",
            data={
                "enabled": enabled,
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        logger.info(f"Visualization {'enabled' if enabled else 'disabled'}")
    
    def _get_state_color(self, state: AgentState) -> str:
        """Get color for agent state visualization."""
        color_map = {
            AgentState.IDLE: "#64748b",        # Gray
            AgentState.PROCESSING: "#3b82f6",  # Blue
            AgentState.COLLABORATING: "#8b5cf6", # Purple
            AgentState.COMPLETED: "#10b981",   # Green
            AgentState.ERROR: "#ef4444"        # Red
        }
        return color_map.get(state, "#64748b")
    
    def _get_state_animation(self, state: AgentState) -> str:
        """Get animation type for agent state."""
        animation_map = {
            AgentState.IDLE: "pulse_slow",
            AgentState.PROCESSING: "spin",
            AgentState.COLLABORATING: "pulse_fast",
            AgentState.COMPLETED: "glow",
            AgentState.ERROR: "shake"
        }
        return animation_map.get(state, "pulse_slow")
    
    def _get_connection_color(self, message_type: str) -> str:
        """Get color for connection visualization."""
        color_map = {
            "consensus": "#8b5cf6",  # Purple
            "data": "#3b82f6",       # Blue
            "message": "#10b981",    # Green
            "status": "#f59e0b",     # Yellow
            "heartbeat": "#64748b"   # Gray
        }
        return color_map.get(message_type, "#10b981")


# Global realtime visualization integrator
_realtime_visualizer: Optional[RealtimeVisualizationIntegrator] = None


def get_realtime_visualizer() -> RealtimeVisualizationIntegrator:
    """Get the global realtime visualization integrator."""
    global _realtime_visualizer
    if _realtime_visualizer is None:
        _realtime_visualizer = RealtimeVisualizationIntegrator()
    return _realtime_visualizer


async def broadcast_agent_action_visual(agent_id: str, action: str, 
                                      state: str = "processing",
                                      confidence: float = None,
                                      details: Dict[str, Any] = None) -> None:
    """Convenience function to broadcast agent action visualization."""
    visualizer = get_realtime_visualizer()
    await visualizer.update_agent_visualization(
        agent_id=agent_id,
        action=action,
        state=state,
        confidence=confidence,
        details=details
    )


async def broadcast_agent_communication_visual(from_agent: str, to_agent: str,
                                             message_type: str = "message",
                                             data: Dict[str, Any] = None) -> None:
    """Convenience function to broadcast agent communication visualization."""
    visualizer = get_realtime_visualizer()
    await visualizer.visualize_agent_communication(
        from_agent=from_agent,
        to_agent=to_agent,
        message_type=message_type,
        data=data
    )