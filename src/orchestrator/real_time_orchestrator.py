"""
Real-Time Agent Orchestrator with WebSocket Streaming

Extends the existing orchestrator to stream agent status updates and incident
progression to Dashboard 3 (Production) via WebSocket in real-time.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from contextlib import asynccontextmanager

from src.models.incident import Incident
from src.models.agent import AgentType, AgentRecommendation
from src.models.real_time_models import (
    AgentUpdate,
    AgentState,
    IncidentPhase,
    IncidentFlowUpdate,
    BusinessMetrics,
    SystemHealthMetrics,
    WebSocketEvent,
    ErrorNotification,
)
from src.services.websocket_manager import get_websocket_manager
from src.utils.logging import get_logger


logger = get_logger("real_time_orchestrator")


class RealTimeOrchestrator:
    """
    Real-time incident processing orchestrator with WebSocket streaming.

    Coordinates agent execution while streaming status updates to Dashboard 3
    through the WebSocket manager.

    Features:
    - Phase-by-phase incident processing
    - Real-time agent state broadcasting
    - Incident flow visualization
    - Progress tracking and estimation
    - Error handling with recovery notifications
    """

    def __init__(self):
        self.ws_manager = None
        self.active_incidents: Dict[str, Dict[str, Any]] = {}
        self.processing_times: Dict[str, List[float]] = {
            phase.value: [] for phase in IncidentPhase
        }
        self.start_time = datetime.utcnow()

    async def initialize(self):
        """Initialize the orchestrator and WebSocket manager."""
        self.ws_manager = await get_websocket_manager()
        logger.info("Real-time orchestrator initialized")

    async def _broadcast_agent_update(
        self,
        incident_id: str,
        agent_name: str,
        agent_type: str,
        state: AgentState,
        phase: IncidentPhase,
        **kwargs
    ):
        """Broadcast agent status update via WebSocket."""
        if not self.ws_manager:
            return

        update = AgentUpdate(
            agent_name=agent_name,
            agent_type=agent_type,
            incident_id=incident_id,
            state=state,
            phase=phase,
            **kwargs
        )

        event = WebSocketEvent(
            event_type="agent_update",
            target_dashboard="ops",
            data=update.model_dump(mode='json'),
            priority=2 if state == AgentState.ERROR else 1
        )

        await self.ws_manager.broadcast_agent_state(
            agent_name=agent_name,
            state=state.value,
            metadata=event.model_dump(mode='json')
        )

        logger.debug(f"Broadcast agent update: {agent_name} -> {state.value}")

    async def _broadcast_incident_flow(
        self,
        incident_id: str,
        current_phase: IncidentPhase,
        **kwargs
    ):
        """Broadcast incident flow update via WebSocket."""
        if not self.ws_manager:
            return

        incident_data = self.active_incidents.get(incident_id, {})

        # Remove any conflicting keys from kwargs
        filtered_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['incident_id', 'current_phase', 'completed_phases', 'active_agents', 'overall_progress']}
        
        flow_update = IncidentFlowUpdate(
            incident_id=incident_id,
            current_phase=current_phase,
            completed_phases=incident_data.get("completed_phases", []),
            active_agents=incident_data.get("active_agents", []),
            overall_progress=incident_data.get("progress", 0.0),
            **filtered_kwargs
        )

        event = WebSocketEvent(
            event_type="incident_flow",
            target_dashboard="ops",
            data=flow_update.model_dump(mode='json'),
            priority=2
        )

        await self.ws_manager.broadcast_incident_update(
            incident_id=incident_id,
            phase=current_phase.value,
            data=event.model_dump(mode='json')
        )

        logger.debug(f"Broadcast incident flow: {incident_id} -> {current_phase.value}")

    async def _broadcast_error(
        self,
        error_type: str,
        error_message: str,
        severity: str = "medium",
        **kwargs
    ):
        """Broadcast error notification via WebSocket."""
        if not self.ws_manager:
            return

        error_notification = ErrorNotification(
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            **kwargs
        )

        event = WebSocketEvent(
            event_type="error_notification",
            target_dashboard="ops",
            data=error_notification.model_dump(mode='json'),
            priority=3 if severity in ["high", "critical"] else 2
        )

        # Broadcast as system health update
        await self.ws_manager.broadcast_message(event.model_dump(mode='json'))

        logger.warning(f"Broadcast error: {error_type} - {error_message}")

    @asynccontextmanager
    async def _track_agent_execution(
        self,
        incident_id: str,
        agent_name: str,
        agent_type: str,
        phase: IncidentPhase
    ):
        """Context manager to track agent execution with automatic status updates."""
        start_time = time.time()

        # Broadcast starting state
        await self._broadcast_agent_update(
            incident_id=incident_id,
            agent_name=agent_name,
            agent_type=agent_type,
            state=AgentState.INITIALIZING,
            phase=phase,
            progress=0.0
        )

        try:
            # Update to processing
            await self._broadcast_agent_update(
                incident_id=incident_id,
                agent_name=agent_name,
                agent_type=agent_type,
                state=AgentState.PROCESSING,
                phase=phase,
                progress=0.5
            )

            yield

            # Success - mark completed
            processing_time = int((time.time() - start_time) * 1000)
            await self._broadcast_agent_update(
                incident_id=incident_id,
                agent_name=agent_name,
                agent_type=agent_type,
                state=AgentState.COMPLETED,
                phase=phase,
                progress=1.0,
                processing_time_ms=processing_time
            )

            # Track timing for metrics
            self.processing_times[phase.value].append(processing_time / 1000)

        except asyncio.TimeoutError:
            await self._broadcast_agent_update(
                incident_id=incident_id,
                agent_name=agent_name,
                agent_type=agent_type,
                state=AgentState.TIMEOUT,
                phase=phase,
                progress=0.5
            )
            await self._broadcast_error(
                error_type="agent_timeout",
                error_message=f"Agent {agent_name} timed out in phase {phase.value}",
                severity="high",
                incident_id=incident_id,
                agent_name=agent_name,
                phase=phase
            )
            raise

        except Exception as e:
            await self._broadcast_agent_update(
                incident_id=incident_id,
                agent_name=agent_name,
                agent_type=agent_type,
                state=AgentState.ERROR,
                phase=phase,
                progress=0.5
            )
            await self._broadcast_error(
                error_type="agent_execution_error",
                error_message=f"Agent {agent_name} failed: {str(e)}",
                severity="high",
                incident_id=incident_id,
                agent_name=agent_name,
                phase=phase,
                stack_trace=str(e)
            )
            raise

    async def process_incident_realtime(
        self,
        incident: Incident,
        agent_callbacks: Optional[Dict[str, Callable]] = None
    ) -> Dict[str, Any]:
        """
        Process an incident with real-time status streaming.

        Args:
            incident: Incident to process
            agent_callbacks: Optional dict of agent_type -> callback function

        Returns:
            Processing result with recommendations and metrics
        """
        incident_id = incident.id
        start_time = time.time()

        # Initialize incident tracking
        self.active_incidents[incident_id] = {
            "incident": incident,
            "start_time": start_time,
            "completed_phases": [],
            "active_agents": [],
            "progress": 0.0
        }

        try:
            logger.info(f"Starting real-time processing for incident {incident_id}")

            # Phase 1: Detection
            await self._process_phase(
                incident=incident,
                phase=IncidentPhase.DETECTION,
                agent_type=AgentType.DETECTION,
                callback=agent_callbacks.get("detection") if agent_callbacks else None
            )

            # Phase 2: Diagnosis
            await self._process_phase(
                incident=incident,
                phase=IncidentPhase.DIAGNOSIS,
                agent_type=AgentType.DIAGNOSIS,
                callback=agent_callbacks.get("diagnosis") if agent_callbacks else None
            )

            # Phase 3: Prediction
            await self._process_phase(
                incident=incident,
                phase=IncidentPhase.PREDICTION,
                agent_type=AgentType.PREDICTION,
                callback=agent_callbacks.get("prediction") if agent_callbacks else None
            )

            # Phase 4: Resolution
            await self._process_phase(
                incident=incident,
                phase=IncidentPhase.RESOLUTION,
                agent_type=AgentType.RESOLUTION,
                callback=agent_callbacks.get("resolution") if agent_callbacks else None
            )

            # Mark complete
            await self._broadcast_incident_flow(
                incident_id=incident_id,
                current_phase=IncidentPhase.COMPLETE,
                overall_progress=1.0,
                incident_summary=f"Incident {incident_id} resolved successfully"
            )

            processing_duration = time.time() - start_time

            logger.info(
                f"Completed real-time processing for incident {incident_id} "
                f"in {processing_duration:.2f}s"
            )

            return {
                "incident_id": incident_id,
                "status": "completed",
                "processing_duration": processing_duration,
                "phases_completed": len(self.active_incidents[incident_id]["completed_phases"])
            }

        except Exception as e:
            logger.error(f"Error processing incident {incident_id}: {e}")
            await self._broadcast_error(
                error_type="incident_processing_error",
                error_message=f"Failed to process incident {incident_id}: {str(e)}",
                severity="critical",
                incident_id=incident_id
            )
            raise

        finally:
            # Clean up
            if incident_id in self.active_incidents:
                del self.active_incidents[incident_id]

    async def _process_phase(
        self,
        incident: Incident,
        phase: IncidentPhase,
        agent_type: AgentType,
        callback: Optional[Callable] = None
    ):
        """Process a single incident phase with agent tracking."""
        incident_id = incident.id
        agent_name = f"{agent_type.value}_agent"

        # Update incident tracking
        self.active_incidents[incident_id]["active_agents"] = [agent_name]

        # Broadcast phase start
        await self._broadcast_incident_flow(
            incident_id=incident_id,
            current_phase=phase,
            phase_progress=0.0
        )

        # Execute agent with tracking
        async with self._track_agent_execution(
            incident_id=incident_id,
            agent_name=agent_name,
            agent_type=agent_type.value,
            phase=phase
        ):
            if callback:
                result = await callback(incident)
            else:
                # Simulate processing for demo
                await asyncio.sleep(1.0)
                result = {"status": "success", "phase": phase.value}

        # Update completed phases
        self.active_incidents[incident_id]["completed_phases"].append(phase)
        
        # Calculate progress dynamically based on total phases
        total_phases = len(list(IncidentPhase))
        completed_phases = len(self.active_incidents[incident_id]["completed_phases"])
        self.active_incidents[incident_id]["progress"] = completed_phases / total_phases if total_phases > 0 else 0

        # Broadcast phase completion
        await self._broadcast_incident_flow(
            incident_id=incident_id,
            current_phase=phase,
            phase_progress=1.0,
            completed_phases=self.active_incidents[incident_id]["completed_phases"]
        )

        return result

    async def get_system_health(self) -> SystemHealthMetrics:
        """Get current system health metrics."""
        active_incident_count = len(self.active_incidents)

        # Get WebSocket metrics if available
        ws_metrics = {}
        if self.ws_manager:
            ws_metrics = self.ws_manager.get_metrics()

        return SystemHealthMetrics(
            active_agents=4,  # Total agents in system
            healthy_agents=4,
            degraded_agents=0,
            error_agents=0,
            current_incidents=active_incident_count,
            queue_depth=0,
            processing_capacity=1.0 - (active_incident_count / 10.0),  # Max 10 concurrent
            average_latency_ms=sum(
                sum(times) / len(times) if times else 0
                for times in self.processing_times.values()
            ) / len(self.processing_times) * 1000 if self.processing_times else 0,
            p95_latency_ms=0.0,  # Would need proper calculation
            p99_latency_ms=0.0,
            websocket_connections=ws_metrics.get("active_connections", 0),
            websocket_latency_ms=50.0,  # Placeholder
            messages_per_second=ws_metrics.get("total_messages_sent", 0) / max(
                (datetime.utcnow() - self.start_time).total_seconds(), 1
            )
        )

    async def broadcast_system_health(self):
        """Broadcast current system health to Dashboard 3."""
        if not self.ws_manager:
            return

        health = await self.get_system_health()

        event = WebSocketEvent(
            event_type="system_health",
            target_dashboard="ops",
            data=health.model_dump(mode='json'),
            priority=1
        )

        await self.ws_manager.broadcast_message(event.model_dump(mode='json'))


# Global instance
_orchestrator_instance: Optional[RealTimeOrchestrator] = None
_orchestrator_lock = asyncio.Lock()


async def get_real_time_orchestrator() -> RealTimeOrchestrator:
    """Get or create the global real-time orchestrator instance."""
    global _orchestrator_instance

    async with _orchestrator_lock:
        if _orchestrator_instance is None:
            _orchestrator_instance = RealTimeOrchestrator()
            await _orchestrator_instance.initialize()

    return _orchestrator_instance
