"""
Agent swarm coordinator for orchestrating multi-agent incident processing.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from dataclasses import dataclass

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
                logger.info(f"Incident {incident.id} processed successfully in {processing_state.total_duration_seconds:.2f}s")
            else:
                self.processing_metrics["failed_incidents"] += 1
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
            
            return error_decision
    
    async def _execute_detection_phase(self, state: IncidentProcessingState) -> None:
        """Execute the detection phase."""
        logger.info(f"Starting detection phase for incident {state.incident_id}")
        state.phase = ProcessingPhase.DETECTION
        
        # Find detection agents
        detection_agents = [agent for agent in self.agents.values() 
                          if agent.agent_type == AgentType.DETECTION]
        
        if not detection_agents:
            state.phase = ProcessingPhase.FAILED
            state.error = "No detection agents available"
            return
        
        # Execute detection agents in parallel
        detection_tasks = []
        for agent in detection_agents:
            task = self._execute_agent_with_circuit_breaker(agent, state.incident, state)
            detection_tasks.append(task)
        
        # Wait for all detection agents to complete
        await asyncio.gather(*detection_tasks, return_exceptions=True)
        
        # Check if any detection agents succeeded
        completed_agents = state.get_completed_agents()
        if not completed_agents:
            state.phase = ProcessingPhase.FAILED
            state.error = "All detection agents failed"
            return
        
        logger.info(f"Detection phase completed for incident {state.incident_id}: "
                   f"{len(completed_agents)} agents succeeded")
    
    async def _execute_diagnosis_phase(self, state: IncidentProcessingState) -> None:
        """Execute the diagnosis phase."""
        logger.info(f"Starting diagnosis phase for incident {state.incident_id}")
        state.phase = ProcessingPhase.DIAGNOSIS
        
        # Find diagnosis agents
        diagnosis_agents = [agent for agent in self.agents.values() 
                          if agent.agent_type == AgentType.DIAGNOSIS]
        
        if not diagnosis_agents:
            logger.warning(f"No diagnosis agents available for incident {state.incident_id}")
            return  # Continue without diagnosis
        
        # Execute diagnosis agents in parallel
        diagnosis_tasks = []
        for agent in diagnosis_agents:
            task = self._execute_agent_with_circuit_breaker(agent, state.incident, state)
            diagnosis_tasks.append(task)
        
        # Wait for all diagnosis agents to complete
        await asyncio.gather(*diagnosis_tasks, return_exceptions=True)
        
        completed_agents = state.get_completed_agents()
        logger.info(f"Diagnosis phase completed for incident {state.incident_id}: "
                   f"{len([a for a in completed_agents if 'diagnosis' in a.lower()])} diagnosis agents succeeded")
    
    async def _execute_prediction_phase(self, state: IncidentProcessingState) -> None:
        """Execute the prediction phase."""
        logger.info(f"Starting prediction phase for incident {state.incident_id}")
        state.phase = ProcessingPhase.PREDICTION
        
        # Find prediction agents
        prediction_agents = [agent for agent in self.agents.values() 
                           if agent.agent_type == AgentType.PREDICTION]
        
        if not prediction_agents:
            logger.warning(f"No prediction agents available for incident {state.incident_id}")
            return  # Continue without prediction
        
        # Execute prediction agents in parallel
        prediction_tasks = []
        for agent in prediction_agents:
            task = self._execute_agent_with_circuit_breaker(agent, state.incident, state)
            prediction_tasks.append(task)
        
        # Wait for all prediction agents to complete
        await asyncio.gather(*prediction_tasks, return_exceptions=True)
        
        completed_agents = state.get_completed_agents()
        logger.info(f"Prediction phase completed for incident {state.incident_id}: "
                   f"{len([a for a in completed_agents if 'prediction' in a.lower()])} prediction agents succeeded")
    
    async def _execute_resolution_phase(self, state: IncidentProcessingState) -> None:
        """Execute the resolution phase."""
        logger.info(f"Starting resolution phase for incident {state.incident_id}")
        state.phase = ProcessingPhase.RESOLUTION
        
        # Find resolution agents
        resolution_agents = [agent for agent in self.agents.values() 
                           if agent.agent_type == AgentType.RESOLUTION]
        
        if not resolution_agents:
            logger.warning(f"No resolution agents available for incident {state.incident_id}")
            return  # Continue without resolution
        
        # Check if consensus decision requires human approval
        if state.consensus_decision and state.consensus_decision.requires_human_approval:
            logger.info(f"Incident {state.incident_id} requires human approval, skipping automated resolution")
            return
        
        # Execute resolution agents in parallel
        resolution_tasks = []
        for agent in resolution_agents:
            task = self._execute_agent_with_circuit_breaker(agent, state.incident, state)
            resolution_tasks.append(task)
        
        # Wait for all resolution agents to complete
        await asyncio.gather(*resolution_tasks, return_exceptions=True)
        
        completed_agents = state.get_completed_agents()
        logger.info(f"Resolution phase completed for incident {state.incident_id}: "
                   f"{len([a for a in completed_agents if 'resolution' in a.lower()])} resolution agents succeeded")
    
    async def _execute_communication_phase(self, state: IncidentProcessingState) -> None:
        """Execute the communication phase."""
        logger.info(f"Starting communication phase for incident {state.incident_id}")
        state.phase = ProcessingPhase.COMMUNICATION
        
        # Find communication agents
        communication_agents = [agent for agent in self.agents.values() 
                              if agent.agent_type == AgentType.COMMUNICATION]
        
        if not communication_agents:
            logger.warning(f"No communication agents available for incident {state.incident_id}")
            return  # Continue without communication
        
        # Execute communication agents in parallel
        communication_tasks = []
        for agent in communication_agents:
            task = self._execute_agent_with_circuit_breaker(agent, state.incident, state)
            communication_tasks.append(task)
        
        # Wait for all communication agents to complete
        await asyncio.gather(*communication_tasks, return_exceptions=True)
        
        completed_agents = state.get_completed_agents()
        logger.info(f"Communication phase completed for incident {state.incident_id}: "
                   f"{len([a for a in completed_agents if 'communication' in a.lower()])} communication agents succeeded")
    
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
        
        # Get all recommendations
        all_recommendations = state.get_all_recommendations()
        
        if not all_recommendations:
            state.phase = ProcessingPhase.FAILED
            state.error = "No recommendations available for consensus"
            return
        
        try:
            # Reach consensus
            consensus_decision = await self.consensus_engine.reach_consensus(
                state.incident, all_recommendations
            )
            
            state.consensus_decision = consensus_decision
            state.phase = ProcessingPhase.COMPLETED
            state.end_time = datetime.utcnow()
            
            logger.info(f"Consensus reached for incident {state.incident_id}: "
                       f"action={consensus_decision.selected_action}, "
                       f"confidence={consensus_decision.final_confidence:.2f}")
            
        except Exception as e:
            state.phase = ProcessingPhase.FAILED
            state.error = f"Consensus failed: {str(e)}"
            logger.error(f"Consensus failed for incident {state.incident_id}: {e}")
    
    async def _execute_agent_with_circuit_breaker(self, agent: BaseAgent, 
                                                 incident: Incident,
                                                 state: IncidentProcessingState) -> None:
        """Execute an agent with circuit breaker protection."""
        agent_name = agent.name
        
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
                return
            
            # Execute agent with timeout
            execution.status = "running"
            execution.start_time = datetime.utcnow()
            
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
            
        except asyncio.TimeoutError:
            execution.end_time = datetime.utcnow()
            execution.status = "failed"
            execution.error = f"Timeout after {timeout}s"
            
            # Record failure in circuit breaker
            circuit_breaker = circuit_breaker_manager.get_agent_circuit_breaker(agent_name)
            circuit_breaker.record_failure()
            
            logger.error(f"Agent {agent_name} timed out after {timeout}s")
            
        except Exception as e:
            execution.end_time = datetime.utcnow()
            execution.status = "failed"
            execution.error = str(e)
            
            # Record failure in circuit breaker
            circuit_breaker = circuit_breaker_manager.get_agent_circuit_breaker(agent_name)
            circuit_breaker.record_failure()
            
            logger.error(f"Agent {agent_name} failed: {e}")
    
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
            "error": state.error
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
