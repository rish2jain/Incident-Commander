"""
Complete Incident Lifecycle Management

Provides end-to-end incident processing, state machine management,
concurrent incident processing, and incident prioritization.

Task 13.2: Build complete incident lifecycle management
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import heapq
from collections import defaultdict

from src.utils.logging import get_logger
from src.models.incident import Incident, IncidentSeverity, ServiceTier
from src.services.agent_swarm_coordinator import get_agent_swarm_coordinator


logger = get_logger("incident_lifecycle_manager")


class IncidentState(Enum):
    """Incident lifecycle states."""
    CREATED = "created"
    DETECTED = "detected"
    TRIAGED = "triaged"
    INVESTIGATING = "investigating"
    DIAGNOSED = "diagnosed"
    PREDICTING = "predicting"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    COMMUNICATING = "communicating"
    CLOSED = "closed"
    ESCALATED = "escalated"
    FAILED = "failed"


class IncidentPriority(Enum):
    """Incident priority levels for processing order."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class IncidentTransition:
    """Incident state transition record."""
    from_state: IncidentState
    to_state: IncidentState
    timestamp: datetime
    trigger: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PrioritizedIncident:
    """Prioritized incident for processing queue."""
    priority: int
    created_time: datetime
    incident: Incident
    
    def __lt__(self, other):
        # Higher priority (lower number) comes first
        # If same priority, older incidents come first
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_time < other.created_time


@dataclass
class IncidentProcessingContext:
    """Context for incident processing."""
    incident_id: str
    current_state: IncidentState
    priority: IncidentPriority
    start_time: datetime
    state_transitions: List[IncidentTransition] = field(default_factory=list)
    processing_metrics: Dict[str, Any] = field(default_factory=dict)
    workflow_id: Optional[str] = None
    assigned_agents: Set[str] = field(default_factory=set)
    escalation_context: Optional[Dict[str, Any]] = None


class IncidentLifecycleManager:
    """
    Complete incident lifecycle management system.
    
    Provides end-to-end incident processing with state machine management,
    concurrent processing, and business impact-based prioritization.
    """
    
    def __init__(self):
        self.swarm_coordinator = get_agent_swarm_coordinator()
        self.active_incidents: Dict[str, IncidentProcessingContext] = {}
        self.processing_queue: List[PrioritizedIncident] = []
        self.state_machine = self._initialize_state_machine()
        self.concurrent_processing_limit = 10  # Linear scaling limit
        self.processing_semaphore = asyncio.Semaphore(self.concurrent_processing_limit)
        self.lifecycle_metrics = defaultdict(int)
        
    def _initialize_state_machine(self) -> Dict[IncidentState, List[IncidentState]]:
        """Initialize incident state machine with valid transitions."""
        return {
            IncidentState.CREATED: [IncidentState.DETECTED, IncidentState.FAILED],
            IncidentState.DETECTED: [IncidentState.TRIAGED, IncidentState.ESCALATED, IncidentState.FAILED],
            IncidentState.TRIAGED: [IncidentState.INVESTIGATING, IncidentState.ESCALATED],
            IncidentState.INVESTIGATING: [IncidentState.DIAGNOSED, IncidentState.PREDICTING, IncidentState.ESCALATED, IncidentState.FAILED],
            IncidentState.DIAGNOSED: [IncidentState.RESOLVING, IncidentState.ESCALATED],
            IncidentState.PREDICTING: [IncidentState.RESOLVING, IncidentState.ESCALATED],
            IncidentState.RESOLVING: [IncidentState.RESOLVED, IncidentState.ESCALATED, IncidentState.FAILED],
            IncidentState.RESOLVED: [IncidentState.COMMUNICATING, IncidentState.CLOSED],
            IncidentState.COMMUNICATING: [IncidentState.CLOSED],
            IncidentState.CLOSED: [],  # Terminal state
            IncidentState.ESCALATED: [IncidentState.INVESTIGATING, IncidentState.CLOSED],  # Human intervention
            IncidentState.FAILED: [IncidentState.INVESTIGATING, IncidentState.ESCALATED, IncidentState.CLOSED]
        }
    
    async def submit_incident(self, incident: Incident) -> str:
        """
        Submit incident for processing with automatic prioritization.
        
        Returns incident processing ID for tracking.
        """
        # Calculate incident priority based on business impact and severity
        priority = self._calculate_incident_priority(incident)
        
        # Create prioritized incident for queue
        prioritized_incident = PrioritizedIncident(
            priority=priority.value,
            created_time=datetime.utcnow(),
            incident=incident
        )
        
        # Add to processing queue
        heapq.heappush(self.processing_queue, prioritized_incident)
        
        # Create processing context
        context = IncidentProcessingContext(
            incident_id=incident.id,
            current_state=IncidentState.CREATED,
            priority=priority,
            start_time=datetime.utcnow()
        )
        
        self.active_incidents[incident.id] = context
        
        # Record initial state transition
        await self._transition_incident_state(
            incident.id, 
            IncidentState.CREATED, 
            "incident_submitted"
        )
        
        # Start processing if capacity available
        asyncio.create_task(self._process_incident_queue())
        
        logger.info(f"Incident {incident.id} submitted with priority {priority.name}")
        return incident.id
    
    def _calculate_incident_priority(self, incident: Incident) -> IncidentPriority:
        """Calculate incident priority based on business impact and severity."""
        # Base priority from severity
        severity_priority = {
            IncidentSeverity.CRITICAL: IncidentPriority.CRITICAL,
            IncidentSeverity.HIGH: IncidentPriority.HIGH,
            IncidentSeverity.MEDIUM: IncidentPriority.MEDIUM,
            IncidentSeverity.LOW: IncidentPriority.LOW
        }
        
        base_priority = severity_priority[incident.severity]
        
        # Adjust based on business impact
        business_impact = incident.business_impact
        
        # Service tier adjustment
        if business_impact.service_tier == ServiceTier.TIER_1:
            # Tier 1 services get priority boost
            if base_priority.value > 1:
                base_priority = IncidentPriority(base_priority.value - 1)
        
        # Revenue impact adjustment
        if business_impact.revenue_impact_per_minute > 1000:
            # High revenue impact gets priority boost
            if base_priority.value > 1:
                base_priority = IncidentPriority(base_priority.value - 1)
        
        # Affected users adjustment
        if business_impact.affected_users > 10000:
            # Large user impact gets priority boost
            if base_priority.value > 1:
                base_priority = IncidentPriority(base_priority.value - 1)
        
        return base_priority
    
    async def _process_incident_queue(self):
        """Process incidents from queue with concurrent processing."""
        while self.processing_queue:
            # Check if we have processing capacity
            if self.processing_semaphore.locked():
                await asyncio.sleep(1)
                continue
            
            # Get highest priority incident
            try:
                prioritized_incident = heapq.heappop(self.processing_queue)
            except IndexError:
                break
            
            # Start processing with semaphore
            asyncio.create_task(
                self._process_single_incident(prioritized_incident.incident)
            )
    
    async def _process_single_incident(self, incident: Incident):
        """Process single incident through complete lifecycle."""
        async with self.processing_semaphore:
            incident_id = incident.id
            
            try:
                logger.info(f"Starting incident processing: {incident_id}")
                
                # Transition to detected state
                await self._transition_incident_state(
                    incident_id, 
                    IncidentState.DETECTED, 
                    "processing_started"
                )
                
                # Execute incident workflow through swarm coordinator
                workflow_result = await self.swarm_coordinator.process_incident_workflow(incident)
                
                # Update context with workflow information
                context = self.active_incidents[incident_id]
                context.workflow_id = workflow_result["workflow_id"]
                
                # Process workflow results and transition states
                await self._process_workflow_results(incident_id, workflow_result)
                
                # Complete incident lifecycle
                await self._complete_incident_lifecycle(incident_id)
                
                logger.info(f"Incident processing completed: {incident_id}")
                
            except Exception as e:
                logger.error(f"Incident processing failed: {incident_id}: {e}")
                await self._handle_incident_failure(incident_id, e)
    
    async def _process_workflow_results(self, incident_id: str, workflow_result: Dict[str, Any]):
        """Process workflow results and update incident state."""
        context = self.active_incidents[incident_id]
        
        # Transition through workflow phases
        if "agent_results" in workflow_result:
            agent_results = workflow_result["agent_results"]
            
            # Detection phase
            if "detection" in agent_results:
                await self._transition_incident_state(
                    incident_id, 
                    IncidentState.TRIAGED, 
                    "detection_completed"
                )
            
            # Investigation phase (diagnosis + prediction)
            if "diagnosis" in agent_results or "prediction" in agent_results:
                await self._transition_incident_state(
                    incident_id, 
                    IncidentState.INVESTIGATING, 
                    "investigation_started"
                )
                
                if "diagnosis" in agent_results:
                    await self._transition_incident_state(
                        incident_id, 
                        IncidentState.DIAGNOSED, 
                        "diagnosis_completed"
                    )
            
            # Resolution phase
            if "resolution" in agent_results:
                await self._transition_incident_state(
                    incident_id, 
                    IncidentState.RESOLVING, 
                    "resolution_started"
                )
                
                # Check if resolution was successful
                resolution_result = agent_results["resolution"]
                if resolution_result.get("status") == "success":
                    await self._transition_incident_state(
                        incident_id, 
                        IncidentState.RESOLVED, 
                        "resolution_completed"
                    )
                else:
                    await self._transition_incident_state(
                        incident_id, 
                        IncidentState.ESCALATED, 
                        "resolution_failed"
                    )
            
            # Communication phase
            if "communication" in agent_results:
                await self._transition_incident_state(
                    incident_id, 
                    IncidentState.COMMUNICATING, 
                    "communication_started"
                )
        
        # Handle escalation if required
        if workflow_result.get("requires_human_intervention"):
            await self._escalate_incident(incident_id, workflow_result.get("human_escalation"))
    
    async def _complete_incident_lifecycle(self, incident_id: str):
        """Complete incident lifecycle and close incident."""
        context = self.active_incidents[incident_id]
        
        # Final transition to closed state
        await self._transition_incident_state(
            incident_id, 
            IncidentState.CLOSED, 
            "lifecycle_completed"
        )
        
        # Calculate final metrics
        end_time = datetime.utcnow()
        total_duration = (end_time - context.start_time).total_seconds()
        
        context.processing_metrics.update({
            "total_duration_seconds": total_duration,
            "end_time": end_time.isoformat(),
            "state_transitions_count": len(context.state_transitions),
            "final_state": context.current_state.value
        })
        
        # Update lifecycle metrics
        self.lifecycle_metrics["incidents_completed"] += 1
        self.lifecycle_metrics["total_processing_time"] += total_duration
        
        logger.info(f"Incident lifecycle completed: {incident_id} in {total_duration:.1f}s")
    
    async def _escalate_incident(self, incident_id: str, escalation_context: Optional[Dict[str, Any]]):
        """Escalate incident for human intervention."""
        context = self.active_incidents[incident_id]
        context.escalation_context = escalation_context
        
        await self._transition_incident_state(
            incident_id, 
            IncidentState.ESCALATED, 
            "human_escalation_triggered"
        )
        
        logger.critical(f"Incident escalated for human intervention: {incident_id}")
        
        # Update metrics
        self.lifecycle_metrics["incidents_escalated"] += 1
    
    async def _handle_incident_failure(self, incident_id: str, error: Exception):
        """Handle incident processing failure."""
        await self._transition_incident_state(
            incident_id, 
            IncidentState.FAILED, 
            f"processing_failed: {str(error)}"
        )
        
        context = self.active_incidents[incident_id]
        context.processing_metrics["failure_reason"] = str(error)
        context.processing_metrics["failed_at"] = datetime.utcnow().isoformat()
        
        # Update metrics
        self.lifecycle_metrics["incidents_failed"] += 1
        
        logger.error(f"Incident processing failed: {incident_id}: {error}")
    
    async def _transition_incident_state(
        self, 
        incident_id: str, 
        new_state: IncidentState, 
        trigger: str,
        context_data: Optional[Dict[str, Any]] = None
    ):
        """Transition incident to new state with validation."""
        if incident_id not in self.active_incidents:
            raise ValueError(f"Incident {incident_id} not found")
        
        context = self.active_incidents[incident_id]
        current_state = context.current_state
        
        # Validate state transition
        valid_transitions = self.state_machine.get(current_state, [])
        if new_state not in valid_transitions:
            logger.warning(f"Invalid state transition for {incident_id}: {current_state.value} -> {new_state.value}")
            # Allow transition but log warning
        
        # Create transition record
        transition = IncidentTransition(
            from_state=current_state,
            to_state=new_state,
            timestamp=datetime.utcnow(),
            trigger=trigger,
            context=context_data or {}
        )
        
        # Update context
        context.current_state = new_state
        context.state_transitions.append(transition)
        
        logger.info(f"Incident {incident_id} transitioned: {current_state.value} -> {new_state.value} ({trigger})")
    
    def get_incident_status(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get current incident status and processing information."""
        if incident_id not in self.active_incidents:
            return None
        
        context = self.active_incidents[incident_id]
        
        return {
            "incident_id": incident_id,
            "current_state": context.current_state.value,
            "priority": context.priority.name,
            "start_time": context.start_time.isoformat(),
            "processing_duration_seconds": (datetime.utcnow() - context.start_time).total_seconds(),
            "state_transitions": [
                {
                    "from_state": t.from_state.value,
                    "to_state": t.to_state.value,
                    "timestamp": t.timestamp.isoformat(),
                    "trigger": t.trigger,
                    "context": t.context
                }
                for t in context.state_transitions
            ],
            "workflow_id": context.workflow_id,
            "assigned_agents": list(context.assigned_agents),
            "processing_metrics": context.processing_metrics,
            "escalation_context": context.escalation_context,
            "is_escalated": context.current_state == IncidentState.ESCALATED,
            "is_completed": context.current_state in [IncidentState.CLOSED, IncidentState.FAILED]
        }
    
    def get_processing_metrics(self) -> Dict[str, Any]:
        """Get overall processing metrics and performance statistics."""
        active_count = len([
            ctx for ctx in self.active_incidents.values() 
            if ctx.current_state not in [IncidentState.CLOSED, IncidentState.FAILED]
        ])
        
        completed_count = self.lifecycle_metrics["incidents_completed"]
        failed_count = self.lifecycle_metrics["incidents_failed"]
        escalated_count = self.lifecycle_metrics["incidents_escalated"]
        
        total_incidents = completed_count + failed_count
        success_rate = (completed_count / total_incidents * 100) if total_incidents > 0 else 0
        
        average_processing_time = (
            self.lifecycle_metrics["total_processing_time"] / completed_count
            if completed_count > 0 else 0
        )
        
        return {
            "active_incidents": active_count,
            "queue_length": len(self.processing_queue),
            "total_incidents_processed": total_incidents,
            "incidents_completed": completed_count,
            "incidents_failed": failed_count,
            "incidents_escalated": escalated_count,
            "success_rate_percentage": success_rate,
            "average_processing_time_seconds": average_processing_time,
            "concurrent_processing_limit": self.concurrent_processing_limit,
            "processing_capacity_used": self.concurrent_processing_limit - self.processing_semaphore._value,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_incident_queue_status(self) -> Dict[str, Any]:
        """Get incident processing queue status."""
        queue_by_priority = defaultdict(int)
        for prioritized_incident in self.processing_queue:
            priority_name = IncidentPriority(prioritized_incident.priority).name
            queue_by_priority[priority_name] += 1
        
        return {
            "total_queued": len(self.processing_queue),
            "queue_by_priority": dict(queue_by_priority),
            "next_incident": {
                "priority": IncidentPriority(self.processing_queue[0].priority).name,
                "created_time": self.processing_queue[0].created_time.isoformat(),
                "incident_id": self.processing_queue[0].incident.id
            } if self.processing_queue else None,
            "processing_capacity": {
                "limit": self.concurrent_processing_limit,
                "available": self.processing_semaphore._value,
                "used": self.concurrent_processing_limit - self.processing_semaphore._value
            }
        }
    
    async def scale_processing_capacity(self, new_limit: int):
        """Scale concurrent processing capacity for linear performance scaling."""
        if new_limit <= 0:
            raise ValueError("Processing limit must be positive")
        
        old_limit = self.concurrent_processing_limit
        self.concurrent_processing_limit = new_limit
        
        # Create new semaphore with updated limit
        current_used = old_limit - self.processing_semaphore._value
        available_capacity = max(0, new_limit - current_used)
        
        self.processing_semaphore = asyncio.Semaphore(available_capacity)
        
        logger.info(f"Processing capacity scaled from {old_limit} to {new_limit}")
        
        # Process queue if capacity increased
        if new_limit > old_limit:
            asyncio.create_task(self._process_incident_queue())


# Global incident lifecycle manager instance
_incident_lifecycle_manager = None


def get_incident_lifecycle_manager() -> IncidentLifecycleManager:
    """Get the global incident lifecycle manager instance."""
    global _incident_lifecycle_manager
    if _incident_lifecycle_manager is None:
        _incident_lifecycle_manager = IncidentLifecycleManager()
    return _incident_lifecycle_manager