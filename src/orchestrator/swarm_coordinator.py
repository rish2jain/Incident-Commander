"""
Agent swarm coordinator for orchestrating multi-agent incident processing.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass, field

from src.models.incident import Incident, IncidentStatus
from src.models.agent import AgentRecommendation, AgentMessage, AgentType, ConsensusDecision
from src.interfaces.agent import BaseAgent
from src.services.consensus import get_consensus_engine
from src.services.circuit_breaker import circuit_breaker_manager
from src.services.message_bus import get_message_bus, MessagePriority
from src.services.aws import AWSServiceFactory
from src.utils.constants import AGENT_DEPENDENCY_ORDER, PERFORMANCE_TARGETS
from src.utils.logging import get_logger
from src.utils.exceptions import AgentTimeoutError, ConsensusTimeoutError
from src.services.operator_controls import get_operator_control_service


logger = get_logger("swarm_coordinator")


class ProcessingPhase(Enum):
    """Incident processing phases."""
    DETECTION = "detection"
    DIAGNOSIS = "diagnosis"
    PREDICTION = "prediction"
    RESOLUTION = "resolution"
    COMMUNICATION = "communication"
    CONSENSUS = "consensus"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TimelineEvent:
    """Structured timeline event for explainability."""

    timestamp: datetime
    event_type: str
    description: str
    phase: Optional[str] = None
    agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event for API responses."""
        payload = {
            "timestamp": self.timestamp.isoformat(),
            "event": self.event_type,
            "description": self.description
        }
        if self.phase:
            payload["phase"] = self.phase
        if self.agent:
            payload["agent"] = self.agent
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload

    def matches_filters(
        self,
        event_type: Optional[str] = None,
        phase: Optional[str] = None,
        agent: Optional[str] = None,
        search: Optional[str] = None
    ) -> bool:
        """Check if event matches provided filters."""
        if event_type and self.event_type != event_type:
            return False
        if phase and (self.phase or "").lower() != phase.lower():
            return False
        if agent and (self.agent or "").lower() != agent.lower():
            return False
        if search:
            haystack = " ".join([
                self.description.lower(),
                (self.phase or "").lower(),
                (self.agent or "").lower(),
                " ".join(f"{k}:{v}" for k, v in self.metadata.items()).lower()
            ])
            if search.lower() not in haystack:
                return False
        return True


@dataclass
class AgentExecution:
    """Tracks agent execution status."""
    agent_name: str
    agent_type: AgentType
    status: str  # "pending", "running", "completed", "failed"
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    recommendations: List[AgentRecommendation] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.recommendations is None:
            self.recommendations = []
    
    @property
    def duration_seconds(self) -> float:
        """Calculate execution duration in seconds."""
        if not self.start_time:
            return 0.0
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()


@dataclass
class IncidentProcessingState:
    """Tracks the state of incident processing."""
    incident_id: str
    incident: Incident
    phase: ProcessingPhase
    agent_executions: Dict[str, AgentExecution]
    consensus_decision: Optional[ConsensusDecision] = None
    start_time: datetime = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    timeline: List[TimelineEvent] = field(default_factory=list)
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = datetime.utcnow()
    
    @property
    def total_duration_seconds(self) -> float:
        """Calculate total processing duration."""
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds()
    
    def get_completed_agents(self) -> List[str]:
        """Get list of agents that have completed successfully."""
        return [name for name, exec in self.agent_executions.items() 
                if exec.status == "completed"]
    
    def get_failed_agents(self) -> List[str]:
        """Get list of agents that have failed."""
        return [name for name, exec in self.agent_executions.items() 
                if exec.status == "failed"]
    
    def get_all_recommendations(self) -> List[AgentRecommendation]:
        """Get all recommendations from completed agents."""
        recommendations = []
        for execution in self.agent_executions.values():
            if execution.status == "completed" and execution.recommendations:
                recommendations.extend(execution.recommendations)
        return recommendations

    def record_event(
        self,
        event_type: str,
        description: str,
        *,
        phase: Optional[str] = None,
        agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Append an explainability event to the timeline."""
        event = TimelineEvent(
            timestamp=datetime.utcnow(),
            event_type=event_type,
            description=description,
            phase=phase,
            agent=agent,
            metadata=metadata or {}
        )
        self.timeline.append(event)

    def get_timeline(
        self,
        *,
        event_type: Optional[str] = None,
        phase: Optional[str] = None,
        agent: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Return serialized timeline events with optional filtering."""
        events = [
            e for e in self.timeline
            if e.matches_filters(event_type, phase, agent, search)
        ]
        events.sort(key=lambda e: e.timestamp)
        return [e.to_dict() for e in events]

    def summarize_timeline(self) -> Dict[str, Any]:
        """Provide summary statistics for the timeline."""
        summary: Dict[str, Any] = {
            "total_events": len(self.timeline),
            "events_by_type": {},
            "phase_transitions": []
        }
        for event in self.timeline:
            summary["events_by_type"].setdefault(event.event_type, 0)
            summary["events_by_type"][event.event_type] += 1
            if event.event_type == "phase_started":
                summary["phase_transitions"].append(
                    {
                        "phase": event.phase,
                        "timestamp": event.timestamp.isoformat(),
                        "description": event.description
                    }
                )
        return summary


class AgentSwarmCoordinator:
    """Coordinates multiple agents for incident processing."""
    
    def __init__(self, service_factory: Optional[AWSServiceFactory] = None):
        """Initialize swarm coordinator."""
        self.agents: Dict[str, BaseAgent] = {}
        self.processing_states: Dict[str, IncidentProcessingState] = {}
        self.consensus_engine = get_consensus_engine()
        
        # Message bus for inter-agent communication
        self._service_factory = service_factory or AWSServiceFactory()
        self._owns_service_factory = service_factory is None
        self.message_bus = get_message_bus(self._service_factory)
        
        # Performance tracking
        self.processing_metrics = {
            "total_incidents": 0,
            "successful_incidents": 0,
            "failed_incidents": 0,
            "average_processing_time": 0.0
        }
    
    async def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the coordinator."""
        agent_name = agent.name
        self.agents[agent_name] = agent
        
        # Subscribe agent to message bus
        await self.message_bus.subscribe(agent_name, agent.handle_message)
        
        logger.info(f"Registered agent: {agent_name} ({agent.agent_type.value})")
    
    async def unregister_agent(self, agent_name: str) -> None:
        """Unregister an agent from the coordinator."""
        if agent_name in self.agents:
            # Unsubscribe from message bus
            await self.message_bus.unsubscribe(agent_name)
            del self.agents[agent_name]
            logger.info(f"Unregistered agent: {agent_name}")

    async def shutdown(self) -> None:
        """Shutdown coordinator resources."""
        try:
            await self.message_bus.shutdown()
        finally:
            if self._owns_service_factory and self._service_factory:
                await self._service_factory.cleanup()
    
    async def process_incident(self, incident: Incident) -> ConsensusDecision:
        """
        Process an incident through the agent swarm.
        
        Args:
            incident: Incident to process
            
        Returns:
            Consensus decision for the incident
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting incident processing: {incident.id}")
            
            # Initialize processing state
            processing_state = IncidentProcessingState(
                incident_id=incident.id,
                incident=incident,
                phase=ProcessingPhase.DETECTION,
                agent_executions={}
            )

            self.processing_states[incident.id] = processing_state

            processing_state.record_event(
                "incident_started",
                "Incident processing initiated",
                phase=ProcessingPhase.DETECTION.value,
                metadata={
                    "severity": incident.severity,
                    "service_tier": incident.business_impact.service_tier,
                    "detected_at": incident.detected_at.isoformat(),
                    "tags": incident.metadata.tags
                }
            )

            # Update incident status
            incident.status = IncidentStatus.INVESTIGATING
            
            # Phase 1: Detection (must complete first)
            await self._execute_detection_phase(processing_state)
            
            # Phase 2 & 3: Diagnosis and Prediction (can run in parallel)
            if processing_state.phase != ProcessingPhase.FAILED:
                await self._execute_parallel_analysis_phases(processing_state)
            
            # Phase 4: Consensus (if we have recommendations)
            if processing_state.phase != ProcessingPhase.FAILED:
                await self._execute_consensus_phase(processing_state)
            
            # Phase 5 & 6: Resolution and Communication (can run in parallel if resolution doesn't require approval)
            if processing_state.phase != ProcessingPhase.FAILED and processing_state.consensus_decision:
                await self._execute_parallel_action_phases(processing_state)
            
            # Update metrics
            self.processing_metrics["total_incidents"] += 1
            
            if processing_state.phase == ProcessingPhase.COMPLETED:
                self.processing_metrics["successful_incidents"] += 1
                incident.status = IncidentStatus.RESOLVED
                processing_state.record_event(
                    "incident_completed",
                    "Incident fully resolved",
                    phase=processing_state.phase.value,
                    metadata={
                        "duration_seconds": processing_state.total_duration_seconds,
                        "final_action": processing_state.consensus_decision.selected_action if processing_state.consensus_decision else None,
                        "confidence": processing_state.consensus_decision.final_confidence if processing_state.consensus_decision else None
                    }
                )
                logger.info(f"Incident {incident.id} processed successfully in {processing_state.total_duration_seconds:.2f}s")
            else:
                self.processing_metrics["failed_incidents"] += 1
                processing_state.record_event(
                    "incident_failed",
                    processing_state.error or "Incident processing failed",
                    phase=processing_state.phase.value,
                    metadata={"error": processing_state.error}
                )
                logger.error(f"Incident {incident.id} processing failed: {processing_state.error}")
            
            # Update average processing time
            total_time = self.processing_metrics.get("total_processing_time", 0.0)
            count = self.processing_metrics["total_incidents"]
            duration = time.time() - start_time
            
            self.processing_metrics["total_processing_time"] = total_time + duration
            self.processing_metrics["average_processing_time"] = self.processing_metrics["total_processing_time"] / count
            
            return processing_state.consensus_decision
            
        except Exception as e:
            logger.error(f"Incident processing failed for {incident.id}: {e}")
            
            # Create error consensus decision
            error_decision = ConsensusDecision(
                incident_id=incident.id,
                selected_action="error",
                action_type="error",
                final_confidence=0.0,
                participating_agents=[],
                agent_recommendations=[],
                consensus_method="error",
                conflicts_detected=True,
                requires_human_approval=True,
                decision_rationale=f"Processing error: {str(e)}",
                risk_assessment="System error during incident processing"
            )
            
            if incident.id in self.processing_states:
                self.processing_states[incident.id].consensus_decision = error_decision
                self.processing_states[incident.id].phase = ProcessingPhase.FAILED
                self.processing_states[incident.id].error = str(e)
                self.processing_states[incident.id].record_event(
                    "incident_failed",
                    f"Processing error: {str(e)}",
                    phase=self.processing_states[incident.id].phase.value,
                    metadata={"error": str(e)}
                )

            return error_decision
    
    async def _execute_detection_phase(self, state: IncidentProcessingState) -> None:
        """Execute the detection phase."""
        logger.info(f"Starting detection phase for incident {state.incident_id}")
        state.phase = ProcessingPhase.DETECTION
        state.record_event(
            "phase_started",
            "Detection phase started",
            phase=ProcessingPhase.DETECTION.value
        )

        # Find detection agents
        detection_agents = [agent for agent in self.agents.values() 
                          if agent.agent_type == AgentType.DETECTION]

        if not detection_agents:
            state.phase = ProcessingPhase.FAILED
            state.error = "No detection agents available"
            state.record_event(
                "phase_failed",
                "No detection agents available",
                phase=ProcessingPhase.DETECTION.value
            )
            return

        # Execute detection agents in parallel
        detection_tasks = []
        for agent in detection_agents:
            task = self._execute_agent_with_circuit_breaker(
                agent,
                state.incident,
                state,
                phase=ProcessingPhase.DETECTION
            )
            detection_tasks.append(task)

        # Wait for all detection agents to complete
        await asyncio.gather(*detection_tasks, return_exceptions=True)

        # Check if any detection agents succeeded
        completed_agents = state.get_completed_agents()
        if not completed_agents:
            state.phase = ProcessingPhase.FAILED
            state.error = "All detection agents failed"
            state.record_event(
                "phase_failed",
                "All detection agents failed",
                phase=ProcessingPhase.DETECTION.value
            )
            return

        logger.info(f"Detection phase completed for incident {state.incident_id}: "
                   f"{len(completed_agents)} agents succeeded")
        state.record_event(
            "phase_completed",
            "Detection phase completed",
            phase=ProcessingPhase.DETECTION.value,
            metadata={"completed_agents": completed_agents}
        )
    
    async def _execute_diagnosis_phase(self, state: IncidentProcessingState) -> None:
        """Execute the diagnosis phase."""
        logger.info(f"Starting diagnosis phase for incident {state.incident_id}")
        state.phase = ProcessingPhase.DIAGNOSIS
        state.record_event(
            "phase_started",
            "Diagnosis phase started",
            phase=ProcessingPhase.DIAGNOSIS.value
        )

        # Find diagnosis agents
        diagnosis_agents = [agent for agent in self.agents.values() 
                          if agent.agent_type == AgentType.DIAGNOSIS]

        if not diagnosis_agents:
            logger.warning(f"No diagnosis agents available for incident {state.incident_id}")
            state.record_event(
                "phase_skipped",
                "No diagnosis agents available",
                phase=ProcessingPhase.DIAGNOSIS.value
            )
            return  # Continue without diagnosis

        # Execute diagnosis agents in parallel
        diagnosis_tasks = []
        for agent in diagnosis_agents:
            task = self._execute_agent_with_circuit_breaker(
                agent,
                state.incident,
                state,
                phase=ProcessingPhase.DIAGNOSIS
            )
            diagnosis_tasks.append(task)

        # Wait for all diagnosis agents to complete
        await asyncio.gather(*diagnosis_tasks, return_exceptions=True)

        completed_agents = state.get_completed_agents()
        logger.info(f"Diagnosis phase completed for incident {state.incident_id}: "
                   f"{len([a for a in completed_agents if 'diagnosis' in a.lower()])} diagnosis agents succeeded")
        state.record_event(
            "phase_completed",
            "Diagnosis phase completed",
            phase=ProcessingPhase.DIAGNOSIS.value,
            metadata={
                "completed_agents": [
                    a for a in completed_agents if "diagnosis" in a.lower()
                ]
            }
        )
    
    async def _execute_prediction_phase(self, state: IncidentProcessingState) -> None:
        """Execute the prediction phase."""
        logger.info(f"Starting prediction phase for incident {state.incident_id}")
        state.phase = ProcessingPhase.PREDICTION
        state.record_event(
            "phase_started",
            "Prediction phase started",
            phase=ProcessingPhase.PREDICTION.value
        )

        # Find prediction agents
        prediction_agents = [agent for agent in self.agents.values() 
                           if agent.agent_type == AgentType.PREDICTION]

        if not prediction_agents:
            logger.warning(f"No prediction agents available for incident {state.incident_id}")
            state.record_event(
                "phase_skipped",
                "No prediction agents available",
                phase=ProcessingPhase.PREDICTION.value
            )
            return  # Continue without prediction

        # Execute prediction agents in parallel
        prediction_tasks = []
        for agent in prediction_agents:
            task = self._execute_agent_with_circuit_breaker(
                agent,
                state.incident,
                state,
                phase=ProcessingPhase.PREDICTION
            )
            prediction_tasks.append(task)

        # Wait for all prediction agents to complete
        await asyncio.gather(*prediction_tasks, return_exceptions=True)

        completed_agents = state.get_completed_agents()
        logger.info(f"Prediction phase completed for incident {state.incident_id}: "
                   f"{len([a for a in completed_agents if 'prediction' in a.lower()])} prediction agents succeeded")
        state.record_event(
            "phase_completed",
            "Prediction phase completed",
            phase=ProcessingPhase.PREDICTION.value,
            metadata={
                "completed_agents": [
                    a for a in completed_agents if "prediction" in a.lower()
                ]
            }
        )
    
    async def _execute_resolution_phase(self, state: IncidentProcessingState) -> None:
        """Execute the resolution phase."""
        logger.info(f"Starting resolution phase for incident {state.incident_id}")
        state.phase = ProcessingPhase.RESOLUTION
        state.record_event(
            "phase_started",
            "Resolution phase started",
            phase=ProcessingPhase.RESOLUTION.value
        )

        # Find resolution agents
        resolution_agents = [agent for agent in self.agents.values() 
                           if agent.agent_type == AgentType.RESOLUTION]

        if not resolution_agents:
            logger.warning(f"No resolution agents available for incident {state.incident_id}")
            state.record_event(
                "phase_skipped",
                "No resolution agents available",
                phase=ProcessingPhase.RESOLUTION.value
            )
            return  # Continue without resolution

        # Check if consensus decision requires human approval
        if state.consensus_decision and state.consensus_decision.requires_human_approval:
            logger.info(f"Incident {state.incident_id} requires human approval, skipping automated resolution")
            state.record_event(
                "phase_skipped",
                "Resolution skipped due to human approval requirement",
                phase=ProcessingPhase.RESOLUTION.value,
                metadata={"requires_human_approval": True}
            )
            return

        # Execute resolution agents in parallel
        resolution_tasks = []
        for agent in resolution_agents:
            task = self._execute_agent_with_circuit_breaker(
                agent,
                state.incident,
                state,
                phase=ProcessingPhase.RESOLUTION
            )
            resolution_tasks.append(task)

        # Wait for all resolution agents to complete
        await asyncio.gather(*resolution_tasks, return_exceptions=True)

        completed_agents = state.get_completed_agents()
        logger.info(f"Resolution phase completed for incident {state.incident_id}: "
                   f"{len([a for a in completed_agents if 'resolution' in a.lower()])} resolution agents succeeded")
        state.record_event(
            "phase_completed",
            "Resolution phase completed",
            phase=ProcessingPhase.RESOLUTION.value,
            metadata={
                "completed_agents": [
                    a for a in completed_agents if "resolution" in a.lower()
                ]
            }
        )
    
    async def _execute_communication_phase(self, state: IncidentProcessingState) -> None:
        """Execute the communication phase."""
        logger.info(f"Starting communication phase for incident {state.incident_id}")
        state.phase = ProcessingPhase.COMMUNICATION
        state.record_event(
            "phase_started",
            "Communication phase started",
            phase=ProcessingPhase.COMMUNICATION.value
        )

        # Find communication agents
        communication_agents = [agent for agent in self.agents.values() 
                              if agent.agent_type == AgentType.COMMUNICATION]

        if not communication_agents:
            logger.warning(f"No communication agents available for incident {state.incident_id}")
            state.record_event(
                "phase_skipped",
                "No communication agents available",
                phase=ProcessingPhase.COMMUNICATION.value
            )
            return  # Continue without communication

        # Execute communication agents in parallel
        communication_tasks = []
        for agent in communication_agents:
            task = self._execute_agent_with_circuit_breaker(
                agent,
                state.incident,
                state,
                phase=ProcessingPhase.COMMUNICATION
            )
            communication_tasks.append(task)

        # Wait for all communication agents to complete
        await asyncio.gather(*communication_tasks, return_exceptions=True)

        completed_agents = state.get_completed_agents()
        logger.info(f"Communication phase completed for incident {state.incident_id}: "
                   f"{len([a for a in completed_agents if 'communication' in a.lower()])} communication agents succeeded")
        state.record_event(
            "phase_completed",
            "Communication phase completed",
            phase=ProcessingPhase.COMMUNICATION.value,
            metadata={
                "completed_agents": [
                    a for a in completed_agents if "communication" in a.lower()
                ]
            }
        )
    
    async def _execute_parallel_analysis_phases(self, state: IncidentProcessingState) -> None:
        """Execute diagnosis and prediction phases in parallel using TaskGroup."""
        logger.info(f"Starting parallel analysis phases (diagnosis + prediction) for incident {state.incident_id}")
        
        try:
            # Use TaskGroup for structured concurrency (Python 3.11+)
            async with asyncio.TaskGroup() as tg:
                # Start diagnosis and prediction tasks in parallel
                diagnosis_task = tg.create_task(self._execute_diagnosis_phase(state))
                prediction_task = tg.create_task(self._execute_prediction_phase(state))
            
            logger.info(f"Parallel analysis phases completed for incident {state.incident_id}")
            
        except* Exception as eg:
            # Handle exception group from TaskGroup
            logger.error(f"Parallel analysis phases failed for incident {state.incident_id}: {eg}")
            # Continue processing even if some phases fail
    
    async def _execute_parallel_action_phases(self, state: IncidentProcessingState) -> None:
        """Execute resolution and communication phases in parallel if possible."""
        logger.info(f"Starting action phases for incident {state.incident_id}")

        operator_controls = get_operator_control_service()
        evaluation = None
        if state.consensus_decision:
            evaluation = operator_controls.evaluate_decision(state.incident_id, state.consensus_decision)
            if not operator_controls.can_execute_actions(state.incident_id, state.consensus_decision):
                state.record_event(
                    "operator_hold",
                    "Automated actions paused by operator controls",
                    phase=ProcessingPhase.RESOLUTION.value,
                    metadata=evaluation
                )
                if evaluation and evaluation.get("dry_run"):
                    state.record_event(
                        "dry_run_simulation",
                        "Executed dry-run playbook instead of live actions",
                        phase=ProcessingPhase.RESOLUTION.value,
                        metadata={
                            "selected_action": state.consensus_decision.selected_action,
                            "confidence": state.consensus_decision.final_confidence
                        }
                    )
                # Even if automated actions are paused, send communications if possible
                await self._execute_communication_phase(state)
                return

        # Check if consensus decision requires human approval
        requires_approval = (state.consensus_decision and 
                           state.consensus_decision.requires_human_approval)

        if requires_approval:
            # Sequential execution when human approval is required
            logger.info(f"Human approval required for incident {state.incident_id}, executing sequentially")
            await self._execute_resolution_phase(state)
            if state.phase != ProcessingPhase.FAILED:
                await self._execute_communication_phase(state)
        else:
            # Parallel execution when no approval needed
            try:
                async with asyncio.TaskGroup() as tg:
                    # Start resolution and communication in parallel
                    resolution_task = tg.create_task(self._execute_resolution_phase(state))
                    communication_task = tg.create_task(self._execute_communication_phase(state))
                
                logger.info(f"Parallel action phases completed for incident {state.incident_id}")
                
            except* Exception as eg:
                # Handle exception group from TaskGroup
                logger.error(f"Parallel action phases failed for incident {state.incident_id}: {eg}")
                # Continue processing even if some phases fail
    
    async def _execute_consensus_phase(self, state: IncidentProcessingState) -> None:
        """Execute the consensus phase."""
        logger.info(f"Starting consensus phase for incident {state.incident_id}")
        state.phase = ProcessingPhase.CONSENSUS
        state.record_event(
            "phase_started",
            "Consensus phase started",
            phase=ProcessingPhase.CONSENSUS.value
        )

        # Get all recommendations
        all_recommendations = state.get_all_recommendations()

        if not all_recommendations:
            state.phase = ProcessingPhase.FAILED
            state.error = "No recommendations available for consensus"
            state.record_event(
                "phase_failed",
                "No recommendations available for consensus",
                phase=ProcessingPhase.CONSENSUS.value
            )
            return

        try:
            # Reach consensus
            consensus_decision = await self.consensus_engine.reach_consensus(
                state.incident, all_recommendations
            )

            state.consensus_decision = consensus_decision
            operator_controls = get_operator_control_service()
            operator_evaluation = operator_controls.evaluate_decision(
                state.incident_id, consensus_decision
            )
            if operator_evaluation["requires_manual"]:
                consensus_decision.requires_human_approval = True
            state.phase = ProcessingPhase.COMPLETED
            state.end_time = datetime.utcnow()
            state.record_event(
                "operator_review",
                "Operator controls evaluated consensus decision",
                phase=ProcessingPhase.CONSENSUS.value,
                metadata=operator_evaluation
            )
            state.record_event(
                "consensus_reached",
                f"Consensus selected action {consensus_decision.selected_action}",
                phase=ProcessingPhase.CONSENSUS.value,
                metadata={
                    "selected_action": consensus_decision.selected_action,
                    "confidence": consensus_decision.final_confidence,
                    "requires_human_approval": consensus_decision.requires_human_approval,
                    "participating_agents": consensus_decision.participating_agents
                }
            )
            state.record_event(
                "phase_completed",
                "Consensus phase completed",
                phase=ProcessingPhase.CONSENSUS.value
            )

            logger.info(f"Consensus reached for incident {state.incident_id}: "
                       f"action={consensus_decision.selected_action}, "
                       f"confidence={consensus_decision.final_confidence:.2f}")

        except Exception as e:
            state.phase = ProcessingPhase.FAILED
            state.error = f"Consensus failed: {str(e)}"
            state.record_event(
                "consensus_failed",
                f"Consensus failed: {str(e)}",
                phase=ProcessingPhase.CONSENSUS.value,
                metadata={"error": str(e)}
            )
            logger.error(f"Consensus failed for incident {state.incident_id}: {e}")
    
    async def _execute_agent_with_circuit_breaker(self, agent: BaseAgent,
                                                 incident: Incident,
                                                 state: IncidentProcessingState,
                                                 *,
                                                 phase: Optional[ProcessingPhase] = None) -> None:
        """Execute an agent with circuit breaker protection."""
        agent_name = agent.name
        phase_label = (phase or state.phase).value if (phase or state.phase) else None
        
        # Initialize agent execution tracking
        execution = AgentExecution(
            agent_name=agent_name,
            agent_type=agent.agent_type,
            status="pending"
        )
        state.agent_executions[agent_name] = execution

        try:
            # Get circuit breaker for this agent
            circuit_breaker = circuit_breaker_manager.get_agent_circuit_breaker(agent_name)

            # Check if agent is healthy
            if not circuit_breaker.can_execute():
                execution.status = "failed"
                execution.error = "Circuit breaker open"
                logger.warning(f"Agent {agent_name} circuit breaker is open")
                state.record_event(
                    "agent_blocked",
                    f"Agent {agent_name} blocked by circuit breaker",
                    phase=phase_label,
                    agent=agent_name,
                    metadata={
                        "agent_type": agent.agent_type.value,
                        "circuit_breaker_state": circuit_breaker.state.value
                    }
                )
                return

            # Execute agent with timeout
            execution.status = "running"
            execution.start_time = datetime.utcnow()
            state.record_event(
                "agent_started",
                f"Agent {agent_name} started",
                phase=phase_label,
                agent=agent_name,
                metadata={
                    "agent_type": agent.agent_type.value,
                    "phase": phase_label
                }
            )

            timeout = PERFORMANCE_TARGETS.get(agent.agent_type.value, {}).get("max", 300)

            recommendation = await asyncio.wait_for(
                agent.process_incident(incident),
                timeout=timeout
            )
            
            execution.end_time = datetime.utcnow()
            # Handle both single recommendation and list of recommendations
            if isinstance(recommendation, list):
                execution.recommendations = recommendation
            else:
                execution.recommendations = [recommendation] if recommendation else []
            execution.status = "completed"

            # Record success in circuit breaker
            circuit_breaker.record_success()

            logger.info(f"Agent {agent_name} completed successfully: "
                       f"{len(execution.recommendations)} recommendations in "
                       f"{execution.duration_seconds:.2f}s")
            state.record_event(
                "agent_completed",
                f"Agent {agent_name} completed",
                phase=phase_label,
                agent=agent_name,
                metadata={
                    "agent_type": agent.agent_type.value,
                    "duration_seconds": execution.duration_seconds,
                    "recommendations": [
                        {
                            "action_id": rec.action_id,
                            "confidence": rec.confidence,
                            "risk_level": rec.risk_level
                        }
                        for rec in execution.recommendations
                    ]
                }
            )

        except asyncio.TimeoutError:
            execution.end_time = datetime.utcnow()
            execution.status = "failed"
            execution.error = f"Timeout after {timeout}s"

            # Record failure in circuit breaker
            circuit_breaker = circuit_breaker_manager.get_agent_circuit_breaker(agent_name)
            circuit_breaker.record_failure()

            logger.error(f"Agent {agent_name} timed out after {timeout}s")
            state.record_event(
                "agent_failed",
                f"Agent {agent_name} timed out",
                phase=phase_label,
                agent=agent_name,
                metadata={
                    "agent_type": agent.agent_type.value,
                    "timeout_seconds": timeout
                }
            )

        except Exception as e:
            execution.end_time = datetime.utcnow()
            execution.status = "failed"
            execution.error = str(e)

            # Record failure in circuit breaker
            circuit_breaker = circuit_breaker_manager.get_agent_circuit_breaker(agent_name)
            circuit_breaker.record_failure()

            logger.error(f"Agent {agent_name} failed: {e}")
            state.record_event(
                "agent_failed",
                f"Agent {agent_name} failed",
                phase=phase_label,
                agent=agent_name,
                metadata={
                    "agent_type": agent.agent_type.value,
                    "error": str(e)
                }
            )
    
    def get_incident_status(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of incident processing."""
        if incident_id not in self.processing_states:
            return None
        
        state = self.processing_states[incident_id]
        
        return {
            "incident_id": incident_id,
            "phase": state.phase.value,
            "start_time": state.start_time.isoformat(),
            "end_time": state.end_time.isoformat() if state.end_time else None,
            "duration_seconds": state.total_duration_seconds,
            "agent_executions": {
                name: {
                    "agent_type": exec.agent_type.value,
                    "status": exec.status,
                    "duration_seconds": exec.duration_seconds,
                    "recommendations_count": len(exec.recommendations),
                    "error": exec.error
                }
                for name, exec in state.agent_executions.items()
            },
            "consensus_decision": {
                "selected_action": state.consensus_decision.selected_action,
                "final_confidence": state.consensus_decision.final_confidence,
                "requires_human_approval": state.consensus_decision.requires_human_approval
            } if state.consensus_decision else None,
            "error": state.error,
            "timeline_summary": state.summarize_timeline()
        }
    
    def get_agent_health_status(self) -> Dict[str, Any]:
        """Get health status of all registered agents."""
        agent_status = {}
        
        for agent_name, agent in self.agents.items():
            circuit_breaker = circuit_breaker_manager.get_agent_circuit_breaker(agent_name)
            
            agent_status[agent_name] = {
                "agent_type": agent.agent_type.value,
                "is_healthy": agent.is_healthy,
                "last_heartbeat": agent.last_heartbeat.isoformat(),
                "processing_count": agent.processing_count,
                "error_count": agent.error_count,
                "circuit_breaker_state": circuit_breaker.state.value,
                "circuit_breaker_healthy": circuit_breaker.state.value != "open"
            }
        
        return agent_status
    
    def get_processing_metrics(self) -> Dict[str, Any]:
        """Get overall processing metrics."""
        return {
            **self.processing_metrics,
            "success_rate": (
                self.processing_metrics["successful_incidents"] / 
                max(1, self.processing_metrics["total_incidents"])
            ),
            "active_incidents": len([
                state for state in self.processing_states.values()
                if state.phase not in [ProcessingPhase.COMPLETED, ProcessingPhase.FAILED]
            ]),
            "registered_agents": len(self.agents),
            "consensus_stats": self.consensus_engine.get_consensus_statistics()
        }

    def get_processing_state(self, incident_id: str) -> Optional[IncidentProcessingState]:
        """Expose processing state for explainability and analytics."""
        return self.processing_states.get(incident_id)

    def get_incident_timeline(
        self,
        incident_id: str,
        *,
        event_type: Optional[str] = None,
        phase: Optional[str] = None,
        agent: Optional[str] = None,
        search: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve serialized incident timeline with filtering support."""
        state = self.processing_states.get(incident_id)
        if not state:
            return None

        timeline = state.get_timeline(
            event_type=event_type,
            phase=phase,
            agent=agent,
            search=search
        )

        return {
            "incident_id": incident_id,
            "timeline": timeline,
            "summary": state.summarize_timeline(),
            "processing_duration_seconds": state.total_duration_seconds,
            "current_phase": state.phase.value if state.phase else None
        }

    async def health_check(self) -> bool:
        """Perform health check for the coordinator."""
        try:
            # Check if we have minimum required agents
            detection_agents = [a for a in self.agents.values() if a.agent_type == AgentType.DETECTION]
            if not detection_agents:
                logger.warning("No detection agents registered")
                return False
            
            # Check agent health
            unhealthy_agents = []
            for agent_name, agent in self.agents.items():
                try:
                    is_healthy = await asyncio.wait_for(agent.health_check(), timeout=5)
                    if not is_healthy:
                        unhealthy_agents.append(agent_name)
                except Exception as e:
                    logger.warning(f"Health check failed for agent {agent_name}: {e}")
                    unhealthy_agents.append(agent_name)
            
            # System is healthy if at least one detection agent is healthy
            healthy_detection_agents = [
                a for a in detection_agents 
                if a.name not in unhealthy_agents
            ]
            
            return len(healthy_detection_agents) > 0
            
        except Exception as e:
            logger.error(f"Coordinator health check failed: {e}")
            return False


# Global coordinator instance
swarm_coordinator: Optional[AgentSwarmCoordinator] = None


def get_swarm_coordinator(service_factory: Optional[AWSServiceFactory] = None) -> AgentSwarmCoordinator:
    """Get or create global swarm coordinator instance."""
    global swarm_coordinator
    if swarm_coordinator is None:
        swarm_coordinator = AgentSwarmCoordinator(service_factory)
    elif service_factory is not None:
        swarm_coordinator._service_factory = service_factory
        swarm_coordinator._owns_service_factory = False
        swarm_coordinator.message_bus.update_service_factory(service_factory)
    return swarm_coordinator
