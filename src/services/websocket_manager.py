"""
WebSocket Manager for Real-time Dashboard Updates

Handles WebSocket connections, agent state broadcasting, and incident flow visualization.
Supports batching and backpressure for 1,000+ concurrent viewers.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import weakref

from fastapi import WebSocket, WebSocketDisconnect
from src.utils.logging import get_logger
from src.models.incident import Incident
from src.models.agent import AgentMessage, AgentType


logger = get_logger("websocket_manager")


@dataclass
class WebSocketMessage:
    """Structured WebSocket message."""
    type: str
    timestamp: datetime
    data: Dict[str, Any]
    priority: int = 1  # 1=low, 2=medium, 3=high


@dataclass
class ConnectionMetrics:
    """Connection performance metrics."""
    connected_at: datetime
    messages_sent: int = 0
    messages_received: int = 0
    last_ping: Optional[datetime] = None
    latency_ms: Optional[float] = None


class WebSocketManager:
    """
    Production-ready WebSocket manager with batching and backpressure.
    
    Features:
    - Connection pooling and management
    - Message batching for performance
    - Backpressure handling for slow clients
    - Agent state broadcasting
    - Incident flow visualization
    - Performance monitoring
    """
    
    def __init__(self, max_connections: int = 1000, batch_size: int = 10, batch_interval: float = 0.1):
        self.max_connections = max_connections
        self.batch_size = batch_size
        self.batch_interval = batch_interval
        
        # Connection management
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metrics: Dict[str, ConnectionMetrics] = {}
        self.connection_queues: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        # Message batching
        self.pending_messages: Dict[str, List[WebSocketMessage]] = defaultdict(list)
        self.batch_task: Optional[asyncio.Task] = None
        
        # Agent state tracking
        self.agent_states: Dict[str, str] = {}
        self.incident_flows: Dict[str, Dict[str, Any]] = {}
        
        # Performance monitoring
        self.total_messages_sent = 0
        self.total_connections = 0
        self.start_time = datetime.utcnow()
        
    async def start(self):
        """Start the WebSocket manager and background tasks."""
        logger.info("Starting WebSocket manager")
        self.batch_task = asyncio.create_task(self._batch_processor())
        
    async def stop(self):
        """Stop the WebSocket manager and cleanup."""
        logger.info("Stopping WebSocket manager")
        if self.batch_task:
            self.batch_task.cancel()
            try:
                await self.batch_task
            except asyncio.CancelledError:
                pass
                
        # Close all connections
        for connection_id in list(self.active_connections.keys()):
            await self.disconnect(connection_id)
            
    async def connect(self, websocket: WebSocket, connection_id: str) -> bool:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: FastAPI WebSocket instance
            connection_id: Unique connection identifier
            
        Returns:
            True if connection accepted, False if rejected
        """
        if len(self.active_connections) >= self.max_connections:
            logger.warning(f"Connection limit reached, rejecting {connection_id}")
            await websocket.close(code=1013, reason="Server overloaded")
            return False
            
        try:
            await websocket.accept()
            self.active_connections[connection_id] = websocket
            self.connection_metrics[connection_id] = ConnectionMetrics(
                connected_at=datetime.utcnow()
            )
            self.total_connections += 1
            
            logger.info(f"WebSocket connected: {connection_id} ({len(self.active_connections)} total)")
            
            # Send initial state
            await self._send_initial_state(connection_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to accept connection {connection_id}: {e}")
            return False
            
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection."""
        if connection_id in self.active_connections:
            try:
                websocket = self.active_connections[connection_id]
                await websocket.close()
            except Exception as e:
                logger.warning(f"Error closing connection {connection_id}: {e}")
            finally:
                del self.active_connections[connection_id]
                del self.connection_metrics[connection_id]
                if connection_id in self.connection_queues:
                    del self.connection_queues[connection_id]
                if connection_id in self.pending_messages:
                    del self.pending_messages[connection_id]
                    
                logger.info(f"WebSocket disconnected: {connection_id} ({len(self.active_connections)} remaining)")
                
    async def broadcast_agent_state(self, agent_name: str, state: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Broadcast agent state change to all connected clients.
        
        Args:
            agent_name: Name of the agent
            state: New agent state
            metadata: Additional state metadata
        """
        self.agent_states[agent_name] = state
        
        message = WebSocketMessage(
            type="agent_state_update",
            timestamp=datetime.utcnow(),
            data={
                "agent_name": agent_name,
                "state": state,
                "metadata": metadata or {},
                "all_states": self.agent_states.copy()
            },
            priority=2
        )
        
        await self._queue_broadcast(message)
        
    async def broadcast_incident_update(self, incident: Incident, phase: str):
        """
        Broadcast incident update to all connected clients.
        
        Args:
            incident: Incident object
            phase: Current processing phase
        """
        # Get real incident data from lifecycle manager
        from src.services.incident_lifecycle_manager import get_incident_lifecycle_manager
        
        lifecycle_manager = get_incident_lifecycle_manager()
        try:
            incident_status = lifecycle_manager.get_incident_status(incident.id)
        except Exception as e:
            logger.warning(f"Failed to get incident status for {incident.id}: {e}")
            incident_status = None
        
        if incident_status and isinstance(incident_status, dict):
            # Validate required keys
            required_keys = ['current_state', 'priority', 'processing_duration_seconds', 
                           'state_transitions', 'assigned_agents', 'is_escalated', 'workflow_id']
            if all(key in incident_status for key in required_keys):
                # Use real incident data
                self.incident_flows[incident.id] = {
                    "id": incident.id,
                    "title": getattr(incident, 'title', f"Incident {incident.id}"),
                    "severity": incident.severity.value if hasattr(incident.severity, 'value') else str(incident.severity),
                    "phase": phase,
                    "current_state": incident_status["current_state"],
                    "priority": incident_status["priority"],
                    "processing_duration": incident_status["processing_duration_seconds"],
                    "state_transitions": incident_status["state_transitions"],
                    "assigned_agents": incident_status["assigned_agents"],
                    "is_escalated": incident_status["is_escalated"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "affected_services": getattr(incident, 'affected_services', []),
                    "estimated_impact": getattr(incident, 'estimated_impact', {}),
                    "workflow_id": incident_status["workflow_id"]
                }
            else:
                logger.warning(f"Incident status missing required keys for {incident.id}, using fallback")
                # Fallback to basic incident data
                self.incident_flows[incident.id] = {
                    "id": incident.id,
                    "title": getattr(incident, 'title', f"Incident {incident.id}"),
                    "severity": incident.severity.value if hasattr(incident.severity, 'value') else str(incident.severity),
                    "phase": phase,
                    "timestamp": datetime.utcnow().isoformat(),
                    "affected_services": getattr(incident, 'affected_services', []),
                    "estimated_impact": getattr(incident, 'estimated_impact', {})
                }
        else:
            # Fallback to basic incident data
            self.incident_flows[incident.id] = {
                "id": incident.id,
                "title": getattr(incident, 'title', f"Incident {incident.id}"),
                "severity": incident.severity.value if hasattr(incident.severity, 'value') else str(incident.severity),
                "phase": phase,
                "timestamp": datetime.utcnow().isoformat(),
                "affected_services": getattr(incident, 'affected_services', []),
                "estimated_impact": getattr(incident, 'estimated_impact', {})
            }
        
        message = WebSocketMessage(
            type="incident_update",
            timestamp=datetime.utcnow(),
            data={
                "incident": self.incident_flows[incident.id],
                "active_incidents": list(self.incident_flows.values()),
                "processing_metrics": lifecycle_manager.get_processing_metrics() if incident_status else {}
            },
            priority=3
        )
        
        await self._queue_broadcast(message)
        
    async def broadcast_consensus_update(self, consensus_data: Dict[str, Any]):
        """
        Broadcast consensus decision to all connected clients.
        
        Args:
            consensus_data: Consensus decision data
        """
        message = WebSocketMessage(
            type="consensus_update",
            timestamp=datetime.utcnow(),
            data=consensus_data,
            priority=3
        )
        
        await self._queue_broadcast(message)
        
    async def broadcast(self, message: WebSocketMessage):
        """
        Generic broadcast method for WebSocket messages.
        
        Args:
            message: WebSocket message to broadcast
        """
        # Ensure timestamp is set
        if not hasattr(message, 'timestamp') or message.timestamp is None:
            message.timestamp = datetime.utcnow()
            
        await self._queue_broadcast(message)
        
    async def handle_client_message(self, connection_id: str, message_data: Dict[str, Any]):
        """
        Handle incoming message from client.
        
        Args:
            connection_id: Client connection ID
            message_data: Message data from client
        """
        try:
            action = message_data.get("action")
            
            if action == "ping":
                await self._handle_ping(connection_id, message_data)
            elif action == "trigger_demo_incident":
                await self._handle_demo_trigger(connection_id)
            elif action == "reset_agents":
                await self._handle_agent_reset(connection_id)
            else:
                logger.warning(f"Unknown action from {connection_id}: {action}")
                
        except Exception as e:
            logger.error(f"Error handling message from {connection_id}: {e}")
            
    async def _send_initial_state(self, connection_id: str):
        """Send initial state to newly connected client."""
        initial_message = WebSocketMessage(
            type="initial_state",
            timestamp=datetime.utcnow(),
            data={
                "agent_states": self.agent_states.copy(),
                "active_incidents": list(self.incident_flows.values()),
                "system_status": "operational"
            },
            priority=3
        )
        
        await self._queue_message(connection_id, initial_message)
        
    async def _queue_broadcast(self, message: WebSocketMessage):
        """Queue message for broadcast to all connections."""
        for connection_id in self.active_connections.keys():
            await self._queue_message(connection_id, message)
            
    async def _queue_message(self, connection_id: str, message: WebSocketMessage):
        """Queue message for specific connection with backpressure handling."""
        if connection_id not in self.active_connections:
            return
            
        queue = self.connection_queues[connection_id]
        
        # Backpressure: drop low priority messages if queue is full
        if len(queue) >= queue.maxlen and message.priority < 3:
            logger.debug(f"Dropping low priority message for {connection_id} (queue full)")
            return
            
        queue.append(message)
        self.pending_messages[connection_id].append(message)
        
    async def _batch_processor(self):
        """Background task to process message batches."""
        while True:
            try:
                await asyncio.sleep(self.batch_interval)
                
                # Process batches for each connection
                for connection_id in list(self.pending_messages.keys()):
                    if connection_id not in self.active_connections:
                        continue
                        
                    messages = self.pending_messages[connection_id][:self.batch_size]
                    if not messages:
                        continue
                        
                    # Remove processed messages
                    self.pending_messages[connection_id] = self.pending_messages[connection_id][self.batch_size:]
                    
                    # Send batch
                    await self._send_message_batch(connection_id, messages)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                
    async def _send_message_batch(self, connection_id: str, messages: List[WebSocketMessage]):
        """Send a batch of messages to a specific connection."""
        if connection_id not in self.active_connections:
            return
            
        websocket = self.active_connections[connection_id]
        
        try:
            # Create batch message
            batch_data = {
                "type": "message_batch",
                "timestamp": datetime.utcnow().isoformat(),
                "messages": [
                    {
                        "type": msg.type,
                        "timestamp": msg.timestamp.isoformat(),
                        "data": msg.data
                    }
                    for msg in messages
                ]
            }
            
            await websocket.send_text(json.dumps(batch_data))
            
            # Update metrics
            metrics = self.connection_metrics[connection_id]
            metrics.messages_sent += len(messages)
            self.total_messages_sent += len(messages)
            
        except WebSocketDisconnect:
            await self.disconnect(connection_id)
        except Exception as e:
            logger.error(f"Error sending batch to {connection_id}: {e}")
            await self.disconnect(connection_id)
            
    async def _handle_ping(self, connection_id: str, message_data: Dict[str, Any]):
        """Handle ping message for latency measurement."""
        client_timestamp = message_data.get("timestamp")
        if client_timestamp:
            try:
                client_time = datetime.fromisoformat(client_timestamp)
                latency = (datetime.utcnow() - client_time).total_seconds() * 1000
                
                metrics = self.connection_metrics[connection_id]
                metrics.last_ping = datetime.utcnow()
                metrics.latency_ms = latency
                
                # Send pong response
                pong_message = WebSocketMessage(
                    type="pong",
                    timestamp=datetime.utcnow(),
                    data={"latency_ms": latency},
                    priority=1
                )
                await self._queue_message(connection_id, pong_message)
                
            except Exception as e:
                logger.error(f"Error handling ping from {connection_id}: {e}")
                
    async def _handle_demo_trigger(self, connection_id: str):
        """Handle demo incident trigger request."""
        logger.info(f"Demo incident triggered by {connection_id}")
        
        try:
            # Import demo controller
            from src.services.demo_controller import get_demo_controller, DemoScenarioType
            from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact
            
            # Get demo controller instance
            demo_controller = get_demo_controller()
            
            # Select a random demo scenario for variety
            import random
            scenarios = list(DemoScenarioType)
            scenario_type = random.choice(scenarios)
            
            logger.info(f"Starting demo scenario: {scenario_type.value}")
            
            # Start the demo scenario (async operation)
            # This will create an incident and execute the full workflow
            asyncio.create_task(self._execute_demo_scenario(demo_controller, scenario_type, connection_id))
            
            # Immediately broadcast demo trigger acknowledgment
            await self.broadcast(
                message_type='demo_triggered',
                data={
                    'status': 'started',
                    'scenario': scenario_type.value,
                    'timestamp': datetime.utcnow().isoformat(),
                    'triggered_by': connection_id
                },
                priority=3  # High priority for demo events
            )
            
            logger.info(f"Demo scenario {scenario_type.value} initiated successfully")
            
        except Exception as e:
            logger.error(f"Error triggering demo incident: {e}")
            # Broadcast error to clients
            await self.broadcast(
                message_type='demo_error',
                data={
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                },
                priority=2
            )
    
    async def _execute_demo_scenario(self, demo_controller, scenario_type, connection_id: str):
        """Execute demo scenario and broadcast progress updates."""
        try:
            # Start the demo scenario
            session = await demo_controller.start_demo_scenario(scenario_type)
            
            # Broadcast scenario start
            await self.broadcast(
                message_type='demo_scenario_started',
                data={
                    'session_id': session.session_id,
                    'scenario': scenario_type.value,
                    'incident_id': session.incident_id,
                    'timestamp': datetime.utcnow().isoformat()
                },
                priority=3
            )
            
            # Monitor and broadcast demo progress
            # In production, this would stream real-time updates
            logger.info(f"Demo scenario {scenario_type.value} executing with session {session.session_id}")
            
        except Exception as e:
            logger.error(f"Error executing demo scenario: {e}")
            await self.broadcast(
                message_type='demo_scenario_error',
                data={'error': str(e)},
                priority=2
            )
        
    async def _handle_agent_reset(self, connection_id: str):
        """Handle agent reset request."""
        logger.info(f"Agent reset requested by {connection_id}")
        
        try:
            # Import agent coordinators
            from src.services.agent_swarm_coordinator import AgentSwarmCoordinator
            from src.services.enhanced_consensus_coordinator import get_enhanced_coordinator
            
            # Get coordinator instances
            try:
                enhanced_coordinator = await get_enhanced_coordinator()
                coordinator = enhanced_coordinator
            except Exception:
                # Fallback to base coordinator if enhanced not available
                coordinator = AgentSwarmCoordinator()
            
            logger.info("Resetting agent states and metrics")
            
            # Reset agent states
            reset_results = {
                'agents_reset': [],
                'state_cleared': False,
                'metrics_reset': False,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Clear agent states if coordinator has agent tracking
            if hasattr(coordinator, 'agent_states'):
                for agent_name in coordinator.agent_states.keys():
                    # Reset each agent's state
                    coordinator.agent_states[agent_name] = 'idle'
                    reset_results['agents_reset'].append(agent_name)
                reset_results['state_cleared'] = True
            
            # Reset workflow tracking
            if hasattr(coordinator, 'active_workflows'):
                coordinator.active_workflows.clear()
            
            # Reset consensus metrics if using enhanced coordinator
            if hasattr(coordinator, 'enhanced_metrics'):
                coordinator.enhanced_metrics.total_consensus_rounds = 0
                coordinator.enhanced_metrics.byzantine_faults_detected = 0
                coordinator.enhanced_metrics.consensus_success_rate = 0.0
                coordinator.enhanced_metrics.average_consensus_time_ms = 0.0
                coordinator.enhanced_metrics.isolated_agents.clear()
                reset_results['metrics_reset'] = True
            
            # Reset PBFT state if available
            if hasattr(coordinator, 'pbft_engine'):
                coordinator.pbft_engine.active_rounds.clear()
                coordinator.pbft_engine.completed_rounds.clear()
                coordinator.pbft_engine.message_log.clear()
                coordinator.pbft_engine.isolated_nodes.clear()
                coordinator.pbft_engine.view_changes = 0
                coordinator.pbft_engine.byzantine_detections = 0
                reset_results['pbft_reset'] = True
            
            # Clear agent behavior history if it exists
            if hasattr(coordinator, 'agent_behavior_history'):
                coordinator.agent_behavior_history.clear()
                reset_results['history_cleared'] = True
            
            logger.info(f"Agent reset completed: {reset_results}")
            
            # Broadcast reset confirmation to all clients
            await self.broadcast(
                message_type='agent_reset_complete',
                data={
                    'status': 'success',
                    'reset_results': reset_results,
                    'requested_by': connection_id,
                    'timestamp': datetime.utcnow().isoformat()
                },
                priority=3  # High priority for system events
            )
            
            # Also broadcast updated agent states
            agent_states = {}
            if hasattr(coordinator, 'agent_states'):
                agent_states = {
                    agent: state for agent, state in coordinator.agent_states.items()
                }
            
            await self.broadcast(
                message_type='agent_states_update',
                data={
                    'agent_states': agent_states,
                    'timestamp': datetime.utcnow().isoformat()
                },
                priority=2
            )
            
            logger.info(f"Agent reset broadcast completed for request from {connection_id}")
            
        except Exception as e:
            logger.error(f"Error resetting agents: {e}")
            # Broadcast error to clients
            await self.broadcast(
                message_type='agent_reset_error',
                data={
                    'status': 'error',
                    'error': str(e),
                    'requested_by': connection_id,
                    'timestamp': datetime.utcnow().isoformat()
                },
                priority=2
            )
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get WebSocket manager performance metrics."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "active_connections": len(self.active_connections),
            "total_connections": self.total_connections,
            "total_messages_sent": self.total_messages_sent,
            "uptime_seconds": uptime,
            "messages_per_second": self.total_messages_sent / max(uptime, 1),
            "connection_metrics": {
                conn_id: {
                    "connected_at": metrics.connected_at.isoformat(),
                    "messages_sent": metrics.messages_sent,
                    "latency_ms": metrics.latency_ms
                }
                for conn_id, metrics in self.connection_metrics.items()
            }
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


def get_websocket_manager() -> WebSocketManager:
    """Get the global WebSocket manager instance."""
    return websocket_manager