"""
3D Visualization WebSocket Integration Service.

Connects the 3D visual dashboard with the WebSocket system for real-time
agent state streaming and visualization updates.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import asdict

from src.utils.logging import get_logger
from src.services.websocket_manager import get_websocket_manager
from src.services.visual_dashboard import VisualDashboard, AgentState, AgentConnection

logger = get_logger("visual_3d_integration")


class Visual3DIntegrationService:
    """
    Integration service for 3D visualization and WebSocket streaming.
    
    Manages real-time data streaming between the 3D dashboard and WebSocket clients,
    providing smooth 60fps visualization updates and agent state synchronization.
    """
    
    def __init__(self):
        self.visual_dashboard = VisualDashboard()
        self.websocket_manager = get_websocket_manager()
        self.streaming_active = False
        self.stream_task: Optional[asyncio.Task] = None
        self.update_interval = 1.0 / 60.0  # 60 FPS target
        
        # Performance tracking
        self.frames_streamed = 0
        self.last_performance_check = datetime.utcnow()
        
        logger.info("3D Visualization WebSocket Integration initialized")
    
    async def start_real_time_streaming(self) -> None:
        """Start real-time 3D visualization streaming."""
        if self.streaming_active:
            logger.warning("3D streaming already active")
            return
        
        self.streaming_active = True
        self.stream_task = asyncio.create_task(self._streaming_loop())
        
        # Initialize 3D scene
        await self.visual_dashboard.initialize_3d_scene()
        
        logger.info("Started real-time 3D visualization streaming at 60 FPS")
    
    async def stop_real_time_streaming(self) -> None:
        """Stop real-time 3D visualization streaming."""
        self.streaming_active = False
        
        if self.stream_task:
            self.stream_task.cancel()
            try:
                await self.stream_task
            except asyncio.CancelledError:
                pass
            self.stream_task = None
        
        logger.info("Stopped real-time 3D visualization streaming")
    
    async def _streaming_loop(self) -> None:
        """Main streaming loop for 60 FPS updates."""
        try:
            while self.streaming_active:
                start_time = asyncio.get_event_loop().time()
                
                # Stream current scene state
                await self._stream_scene_update()
                
                # Update performance metrics
                self.frames_streamed += 1
                
                # Calculate sleep time to maintain 60 FPS
                elapsed = asyncio.get_event_loop().time() - start_time
                sleep_time = max(0, self.update_interval - elapsed)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
                # Log performance every 5 seconds
                if self.frames_streamed % 300 == 0:  # Every 5 seconds at 60 FPS
                    await self._log_performance_metrics()
                    
        except asyncio.CancelledError:
            logger.info("3D streaming loop cancelled")
        except Exception as e:
            logger.error(f"Error in 3D streaming loop: {e}")
            self.streaming_active = False
    
    async def _stream_scene_update(self) -> None:
        """Stream current 3D scene state to WebSocket clients."""
        scene_data = {
            "agents": {
                agent_id: asdict(agent) 
                for agent_id, agent in self.visual_dashboard.agents.items()
            },
            "connections": [
                asdict(conn) for conn in self.visual_dashboard.connections
                if self._is_connection_active(conn)
            ],
            "incidents": {
                inc_id: asdict(inc) 
                for inc_id, inc in self.visual_dashboard.incidents.items()
            },
            "performance": {
                "fps": self.visual_dashboard.current_fps,
                "frame_count": self.frames_streamed,
                "active_agents": len(self.visual_dashboard.agents),
                "active_connections": len(self.visual_dashboard.connections)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.websocket_manager.broadcast_3d_scene_update(scene_data)
    
    def _is_connection_active(self, connection: AgentConnection) -> bool:
        """Check if a connection should still be displayed."""
        created_time = datetime.fromisoformat(connection.created_at.replace('Z', '+00:00'))
        elapsed_ms = (datetime.utcnow() - created_time).total_seconds() * 1000
        return elapsed_ms < connection.duration_ms
    
    async def _log_performance_metrics(self) -> None:
        """Log performance metrics for monitoring."""
        current_time = datetime.utcnow()
        elapsed = (current_time - self.last_performance_check).total_seconds()
        
        if elapsed > 0:
            actual_fps = 300 / elapsed  # 300 frames in the interval
            logger.info(
                f"3D Streaming Performance: {actual_fps:.1f} FPS, "
                f"Agents: {len(self.visual_dashboard.agents)}, "
                f"Connections: {len(self.visual_dashboard.connections)}, "
                f"WebSocket clients: {len(self.websocket_manager.active_connections)}"
            )
        
        self.last_performance_check = current_time
    
    async def update_agent_state(self, agent_id: str, state: str, 
                               confidence: float = None, details: Dict[str, Any] = None) -> None:
        """Update agent state and stream to 3D visualization."""
        try:
            agent_state = AgentState(state)
        except ValueError:
            agent_state = AgentState.PROCESSING
        
        # Update in visual dashboard
        await self.visual_dashboard.update_agent_state(agent_id, agent_state, confidence)
        
        # Stream update immediately for responsive visualization
        agent_data = {
            "state": agent_state.value,
            "confidence": confidence or 1.0,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.websocket_manager.broadcast_3d_agent_update(agent_id, agent_data)
    
    async def create_agent_connection(self, from_agent: str, to_agent: str, 
                                    connection_type: str = "message", 
                                    strength: float = 1.0, duration_ms: int = 2000) -> None:
        """Create visual connection between agents."""
        connection = AgentConnection(
            from_agent=from_agent,
            to_agent=to_agent,
            connection_type=connection_type,
            strength=strength,
            created_at=datetime.utcnow().isoformat(),
            duration_ms=duration_ms
        )
        
        # Add to visual dashboard
        self.visual_dashboard.connections.append(connection)
        
        # Stream connection immediately
        await self.websocket_manager.broadcast_3d_agent_connection(
            from_agent, to_agent, connection_type, strength
        )
        
        # Clean up expired connections
        await self._cleanup_expired_connections()
    
    async def _cleanup_expired_connections(self) -> None:
        """Remove expired connections from visualization."""
        current_time = datetime.utcnow()
        active_connections = []
        
        for connection in self.visual_dashboard.connections:
            if self._is_connection_active(connection):
                active_connections.append(connection)
        
        self.visual_dashboard.connections = active_connections
    
    async def add_incident_visualization(self, incident_id: str, incident_data: Dict[str, Any]) -> None:
        """Add incident to 3D visualization."""
        from src.services.visual_dashboard import IncidentVisualization
        
        # Create incident visualization
        incident_viz = IncidentVisualization(
            incident_id=incident_id,
            title=incident_data.get("title", "Unknown Incident"),
            severity=incident_data.get("severity", "medium"),
            position=(0, 2, 0),  # Center, elevated position
            radius=incident_data.get("affected_users", 1000) / 1000.0,  # Scale by impact
            affected_agents=incident_data.get("affected_agents", []),
            created_at=datetime.utcnow().isoformat()
        )
        
        self.visual_dashboard.incidents[incident_id] = incident_viz
        
        # Stream incident visualization
        await self.websocket_manager.broadcast_3d_incident_visualization(
            incident_id, asdict(incident_viz)
        )
    
    async def update_incident_status(self, incident_id: str, status: str) -> None:
        """Update incident status in 3D visualization."""
        if incident_id in self.visual_dashboard.incidents:
            self.visual_dashboard.incidents[incident_id].status = status
            
            # Stream update
            await self.websocket_manager.broadcast_3d_incident_visualization(
                incident_id, asdict(self.visual_dashboard.incidents[incident_id])
            )
    
    async def register_agent(self, agent_id: str, agent_type: str) -> None:
        """Register agent in 3D visualization."""
        await self.visual_dashboard.add_agent(agent_id, agent_type)
    
    async def get_visualization_status(self) -> Dict[str, Any]:
        """Get current 3D visualization status."""
        return {
            "streaming_active": self.streaming_active,
            "target_fps": 60,
            "actual_fps": self.visual_dashboard.current_fps,
            "frames_streamed": self.frames_streamed,
            "agents_count": len(self.visual_dashboard.agents),
            "connections_count": len(self.visual_dashboard.connections),
            "incidents_count": len(self.visual_dashboard.incidents),
            "websocket_clients": len(self.websocket_manager.active_connections),
            "performance": {
                "update_interval_ms": self.update_interval * 1000,
                "last_performance_check": self.last_performance_check.isoformat()
            }
        }


# Global instance
_visual_3d_integration: Optional[Visual3DIntegrationService] = None


def get_visual_3d_integration() -> Visual3DIntegrationService:
    """Get the global 3D visualization integration service."""
    global _visual_3d_integration
    if _visual_3d_integration is None:
        _visual_3d_integration = Visual3DIntegrationService()
    return _visual_3d_integration


async def start_3d_visualization_streaming() -> None:
    """Start 3D visualization streaming."""
    integration = get_visual_3d_integration()
    await integration.start_real_time_streaming()


async def stop_3d_visualization_streaming() -> None:
    """Stop 3D visualization streaming."""
    integration = get_visual_3d_integration()
    await integration.stop_real_time_streaming()