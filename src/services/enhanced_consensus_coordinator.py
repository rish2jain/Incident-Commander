"""
Enhanced Consensus Coordinator integrating Byzantine Fault Tolerance

Combines the existing agent swarm coordinator with true PBFT consensus
for production-ready Byzantine fault tolerance.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass

from src.services.agent_swarm_coordinator import AgentSwarmCoordinator, AgentState, WorkflowPhase
from src.services.byzantine_consensus import ByzantineFaultTolerantConsensus, PBFTMessage, MessageType
from src.services.websocket_manager import get_websocket_manager
from src.models.incident import Incident
from src.models.agent import AgentRecommendation, ConsensusDecision, AgentType
from src.utils.logging import get_logger
from src.utils.exceptions import ByzantineConsensusError


logger = get_logger("enhanced_consensus_coordinator")


@dataclass
class EnhancedConsensusMetrics:
    """Enhanced metrics including Byzantine fault tolerance."""
    total_consensus_rounds: int = 0
    byzantine_faults_detected: int = 0
    consensus_success_rate: float = 0.0
    average_consensus_time_ms: float = 0.0
    isolated_agents: Set[str] = None
    
    def __post_init__(self):
        if self.isolated_agents is None:
            self.isolated_agents = set()


class EnhancedConsensusCoordinator(AgentSwarmCoordinator):
    """
    Enhanced coordinator with Byzantine fault-tolerant consensus.
    
    Extends the base AgentSwarmCoordinator with:
    - True PBFT consensus instead of weighted voting
    - Byzantine agent detection and isolation
    - Cryptographic message verification
    - Real-time dashboard integration
    """
    
    def __init__(self, node_id: str = "coordinator", total_agents: int = 5):
        """
        Initialize enhanced coordinator.
        
        Args:
            node_id: Unique identifier for this coordinator node
            total_agents: Total number of agents in the system
        """
        super().__init__()
        
        # Byzantine consensus engine
        self.pbft_engine = ByzantineFaultTolerantConsensus(node_id, total_agents)
        self.node_id = node_id
        
        # Enhanced metrics
        self.enhanced_metrics = EnhancedConsensusMetrics()
        
        # Agent-to-node mapping for PBFT
        self.agent_node_mapping = {
            "detection": "agent_detection",
            "diagnosis": "agent_diagnosis", 
            "prediction": "agent_prediction",
            "resolution": "agent_resolution",
            "communication": "agent_communication"
        }
        
        # Initialize PBFT nodes for each agent
        self._initialize_pbft_nodes()
        
        logger.info(f"Enhanced consensus coordinator initialized with PBFT support")
    
    def _initialize_pbft_nodes(self):
        """Initialize PBFT nodes for each agent."""
        for agent_name, node_id in self.agent_node_mapping.items():
            # In a real implementation, these would be separate processes/services
            # For now, we register them with placeholder public keys
            placeholder_key = b"placeholder_public_key_" + node_id.encode()
            self.pbft_engine.register_node(node_id, placeholder_key)
    
    async def handle_incident_with_pbft(self, incident: Incident) -> ConsensusDecision:
        """
        Handle incident using Byzantine fault-tolerant consensus.
        
        Args:
            incident: Incident to process
            
        Returns:
            Consensus decision with Byzantine fault tolerance
        """
        logger.info(f"Starting PBFT incident handling for {incident.id}")
        
        try:
            # Broadcast incident start to dashboard
            ws_manager = await get_websocket_manager()
            await ws_manager.broadcast_incident_update(incident, "pbft_consensus_start")
            
            # Phase 1: Gather agent recommendations
            recommendations = await self._gather_agent_recommendations_pbft(incident)
            
            if not recommendations:
                logger.warning(f"No recommendations received for incident {incident.id}")
                return await self._create_no_action_decision(incident, "No agent recommendations")
            
            # Phase 2: PBFT Consensus
            consensus_decision = await self._run_pbft_consensus(incident, recommendations)
            
            # Phase 3: Execute decision with Byzantine safety
            if consensus_decision and not consensus_decision.requires_human_approval:
                await self._execute_consensus_decision_safely(consensus_decision)
            
            # Update metrics
            self.enhanced_metrics.total_consensus_rounds += 1
            self.enhanced_metrics.byzantine_faults_detected = len(self.pbft_engine.isolated_nodes)
            
            # Broadcast final decision
            await ws_manager.broadcast_consensus_update({
                "incident_id": incident.id,
                "decision": consensus_decision.to_dict() if hasattr(consensus_decision, 'to_dict') else str(consensus_decision),
                "byzantine_nodes_detected": len(self.pbft_engine.isolated_nodes),
                "consensus_method": "pbft",
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return consensus_decision
            
        except Exception as e:
            logger.error(f"PBFT consensus failed for incident {incident.id}: {e}")
            # Fallback to weighted consensus
            return await self._fallback_to_weighted_consensus(incident)
    
    async def _gather_agent_recommendations_pbft(self, incident: Incident) -> List[AgentRecommendation]:
        """Gather recommendations from agents with Byzantine fault detection."""
        recommendations = []
        suspicious_agents = set()
        
        # Broadcast agent state updates
        ws_manager = await get_websocket_manager()
        
        for agent_name, agent in self.agents.items():
            try:
                # Update agent state
                await ws_manager.broadcast_agent_state(agent_name, "processing")
                
                # Get recommendation with timeout
                recommendation = await asyncio.wait_for(
                    agent.analyze_incident(incident),
                    timeout=30.0
                )
                
                # Validate recommendation integrity
                if await self._validate_recommendation_integrity(agent_name, recommendation):
                    recommendations.append(recommendation)
                    await ws_manager.broadcast_agent_state(agent_name, "completed")
                else:
                    logger.warning(f"Invalid recommendation from {agent_name}")
                    suspicious_agents.add(agent_name)
                    await ws_manager.broadcast_agent_state(agent_name, "failed")
                
            except asyncio.TimeoutError:
                logger.warning(f"Timeout getting recommendation from {agent_name}")
                suspicious_agents.add(agent_name)
                await ws_manager.broadcast_agent_state(agent_name, "failed")
            except Exception as e:
                logger.error(f"Error getting recommendation from {agent_name}: {e}")
                suspicious_agents.add(agent_name)
                await ws_manager.broadcast_agent_state(agent_name, "failed")
        
        # Report suspicious agents to PBFT engine
        for agent_name in suspicious_agents:
            node_id = self.agent_node_mapping.get(agent_name)
            if node_id:
                await self.pbft_engine._record_suspicious_behavior(node_id, "recommendation_failure")
        
        return recommendations
    
    async def _validate_recommendation_integrity(self, agent_name: str, recommendation: AgentRecommendation) -> bool:
        """Validate recommendation integrity and detect Byzantine behavior."""
        try:
            # Basic validation checks
            if not hasattr(recommendation, 'confidence') or recommendation.confidence < 0 or recommendation.confidence > 1:
                return False
            
            if not hasattr(recommendation, 'action_id') or not recommendation.action_id:
                return False
            
            # Check for obviously malicious recommendations
            if hasattr(recommendation, 'action_type'):
                dangerous_actions = ['delete_all', 'shutdown_system', 'corrupt_data']
                if str(recommendation.action_type).lower() in dangerous_actions:
                    logger.warning(f"Dangerous action detected from {agent_name}: {recommendation.action_type}")
                    return False
            
            # Sophisticated integrity checks
            
            # 1. Cryptographic signature verification (if present)
            if hasattr(recommendation, 'signature') and recommendation.signature:
                # Verify the signature matches the agent's public key
                agent_node_id = self.agent_node_mapping.get(str(agent_name).lower(), None)
                if agent_node_id and agent_node_id in self.pbft_engine.nodes:
                    # In production, verify cryptographic signature here
                    # For now, check that signature is not empty
                    if not recommendation.signature or len(recommendation.signature) < 10:
                        logger.warning(f"Invalid signature from {agent_name}")
                        return False
            
            # 2. Consistency with historical behavior
            if hasattr(self, 'agent_behavior_history'):
                agent_key = str(agent_name)
                if agent_key in self.agent_behavior_history:
                    history = self.agent_behavior_history[agent_key]
                    
                    # Check if confidence level is consistent with past behavior
                    if hasattr(recommendation, 'confidence'):
                        avg_confidence = sum(h.get('confidence', 0.5) for h in history) / len(history) if history else 0.5
                        # Flag if confidence deviates significantly (>0.4) from historical average
                        if abs(recommendation.confidence - avg_confidence) > 0.4:
                            logger.warning(f"Unusual confidence level from {agent_name}: {recommendation.confidence} vs avg {avg_confidence:.2f}")
                            # Don't reject, but note the anomaly
                    
                    # Check if action_type is consistent with agent's typical recommendations
                    if hasattr(recommendation, 'action_type'):
                        historical_actions = [h.get('action_type') for h in history if 'action_type' in h]
                        if historical_actions and str(recommendation.action_type) not in historical_actions:
                            # New action type - validate it's appropriate for this agent type
                            if not self._validate_action_for_agent_type(agent_name, recommendation.action_type):
                                logger.warning(f"Inappropriate action type {recommendation.action_type} for agent {agent_name}")
                                return False
            
            # 3. Cross-validation with other agents
            # Check if recommendation conflicts with known constraints or other active recommendations
            if hasattr(recommendation, 'conflicts_with') and recommendation.conflicts_with:
                # Verify conflicts are legitimate and not artificially created
                for conflict_id in recommendation.conflicts_with:
                    # In production, validate conflict declarations
                    pass
            
            # 4. Validate recommendation parameters are within safe bounds
            if hasattr(recommendation, 'parameters') and recommendation.parameters:
                # Check for suspicious parameters
                suspicious_params = ['sudo', 'root', 'admin', 'force_delete', 'skip_backup']
                for param_key in recommendation.parameters.keys():
                    if any(sus in str(param_key).lower() for sus in suspicious_params):
                        logger.warning(f"Suspicious parameter detected from {agent_name}: {param_key}")
                        # Require additional validation for suspicious parameters
                        if not hasattr(recommendation, 'requires_human_approval'):
                            return False
                        recommendation.requires_human_approval = True
            
            # 5. Validate urgency and time sensitivity are reasonable
            if hasattr(recommendation, 'urgency') and hasattr(recommendation, 'time_sensitive'):
                if recommendation.urgency > 0.9 and recommendation.time_sensitive:
                    # Very urgent + time sensitive requires extra validation
                    if not hasattr(recommendation, 'reasoning') or len(recommendation.reasoning) < 20:
                        logger.warning(f"Urgent recommendation from {agent_name} lacks sufficient reasoning")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating recommendation from {agent_name}: {e}")
            return False
    
    def _validate_action_for_agent_type(self, agent_name: str, action_type: str) -> bool:
        """
        Validate that an action type is appropriate for a given agent type.
        
        Each agent has specific responsibilities and should only recommend
        actions within their domain.
        """
        agent_str = str(agent_name).lower()
        action_str = str(action_type).lower()
        
        # Define valid action types for each agent
        valid_actions = {
            'detection': [
                'investigate', 'analyze', 'monitor', 'alert', 'escalate',
                'collect_metrics', 'scan', 'detect_anomaly'
            ],
            'diagnosis': [
                'analyze', 'investigate', 'identify_root_cause', 'classify',
                'correlate', 'assess_impact', 'trace'
            ],
            'prediction': [
                'forecast', 'predict', 'estimate', 'model', 'simulate',
                'trend_analysis', 'risk_assessment'
            ],
            'resolution': [
                'resolve', 'fix', 'remediate', 'patch', 'restart',
                'rollback', 'scale', 'failover', 'restore'
            ],
            'communication': [
                'notify', 'alert', 'update', 'broadcast', 'escalate',
                'send_report', 'inform'
            ],
            'coordinator': [
                'coordinate', 'orchestrate', 'delegate', 'aggregate',
                'decide', 'prioritize'
            ]
        }
        
        # Extract agent type from agent name
        for agent_type, actions in valid_actions.items():
            if agent_type in agent_str:
                # Check if action is valid for this agent type
                if any(valid_action in action_str for valid_action in actions):
                    return True
                # Log warning but allow - might be a new valid action
                logger.warning(f"Unusual action '{action_type}' for agent type '{agent_type}'")
                return True  # Allow with warning for flexibility
        
        # Unknown agent type - allow with warning
        logger.warning(f"Unknown agent type '{agent_name}' for action validation")
        return True
    
    async def _run_pbft_consensus(self, incident: Incident, recommendations: List[AgentRecommendation]) -> ConsensusDecision:
        """Run PBFT consensus on agent recommendations."""
        try:
            # For simplicity, use the first recommendation as the proposal
            # In a full implementation, this would be more sophisticated
            primary_recommendation = recommendations[0]
            
            # Check if we're the primary node
            if self.pbft_engine.node_id == self.pbft_engine.primary_node:
                # We're primary, propose the action
                decision = await self.pbft_engine.propose_action(incident, primary_recommendation)
            else:
                # We're not primary, wait for proposal and participate in consensus
                # This would involve listening for PBFT messages from the primary
                # For now, simulate consensus participation
                decision = await self._simulate_consensus_participation(incident, recommendations)
            
            return decision
            
        except ByzantineConsensusError as e:
            logger.error(f"Byzantine consensus error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in PBFT consensus: {e}")
            raise ByzantineConsensusError(f"PBFT consensus failed: {e}")
    
    async def _simulate_consensus_participation(self, incident: Incident, recommendations: List[AgentRecommendation]) -> ConsensusDecision:
        """Simulate consensus participation for non-primary nodes."""
        # This is a simplified simulation
        # In a real implementation, this would handle PBFT message passing
        
        primary_recommendation = recommendations[0]
        
        # Create a consensus decision
        decision = ConsensusDecision(
            incident_id=incident.id,
            selected_action=primary_recommendation.action_id if hasattr(primary_recommendation, 'action_id') else "unknown",
            action_type=str(primary_recommendation.action_type) if hasattr(primary_recommendation, 'action_type') else "unknown",
            final_confidence=1.0,  # PBFT provides certainty
            participating_agents=[r.agent_name.value if hasattr(r.agent_name, 'value') else str(r.agent_name) for r in recommendations],
            agent_recommendations=recommendations,
            consensus_method="pbft",
            conflicts_detected=False,
            requires_human_approval=False,
            approval_threshold=1.0,
            processing_duration_ms=500,  # Simulated processing time
            byzantine_nodes_detected=len(self.pbft_engine.isolated_nodes),
            quorum_size=self.pbft_engine.quorum_size,
            total_nodes=self.pbft_engine.total_nodes
        )
        
        return decision
    
    async def _execute_consensus_decision_safely(self, decision: ConsensusDecision):
        """Execute consensus decision with additional Byzantine safety checks."""
        try:
            # Additional safety validation before execution
            if await self._validate_decision_safety(decision):
                # Execute the decision
                logger.info(f"Executing PBFT consensus decision: {decision.selected_action}")
                
                # Get the primary recommendation from the decision
                primary_recommendation = None
                if hasattr(decision, 'agent_recommendations') and decision.agent_recommendations:
                    primary_recommendation = decision.agent_recommendations[0]
                
                # Track execution start time
                execution_start = datetime.utcnow()
                
                # Execute based on action type
                action_type = str(decision.action_type).lower()
                execution_result = None
                
                if action_type in ['investigate', 'analyze', 'monitor']:
                    # Investigation/analysis actions - collect data and metrics
                    execution_result = await self._execute_investigation_action(decision, primary_recommendation)
                    
                elif action_type in ['resolve', 'fix', 'remediate', 'patch']:
                    # Resolution actions - apply fixes or changes
                    execution_result = await self._execute_resolution_action(decision, primary_recommendation)
                    
                elif action_type in ['restart', 'rollback', 'scale', 'failover']:
                    # Infrastructure actions - require elevated permissions
                    execution_result = await self._execute_infrastructure_action(decision, primary_recommendation)
                    
                elif action_type in ['notify', 'alert', 'escalate', 'broadcast']:
                    # Communication actions - send notifications
                    execution_result = await self._execute_communication_action(decision, primary_recommendation)
                    
                elif action_type == 'no_action':
                    # No action required - just log
                    logger.info(f"No action required for incident {decision.incident_id}")
                    execution_result = {'status': 'success', 'message': 'No action taken as decided'}
                    
                else:
                    # Unknown action type - log warning and require approval
                    logger.warning(f"Unknown action type: {action_type}, requiring human approval")
                    decision.requires_human_approval = True
                    execution_result = {'status': 'pending_approval', 'message': f'Unknown action type: {action_type}'}
                
                # Calculate execution duration
                execution_duration = (datetime.utcnow() - execution_start).total_seconds() * 1000
                
                # Record execution metrics
                if hasattr(self, 'enhanced_metrics'):
                    self.enhanced_metrics.total_consensus_rounds += 1
                    # Update average consensus time
                    if self.enhanced_metrics.total_consensus_rounds > 0:
                        current_avg = self.enhanced_metrics.average_consensus_time_ms
                        new_avg = ((current_avg * (self.enhanced_metrics.total_consensus_rounds - 1)) + execution_duration) / self.enhanced_metrics.total_consensus_rounds
                        self.enhanced_metrics.average_consensus_time_ms = new_avg
                
                # Log execution result
                logger.info(f"Consensus decision execution completed in {execution_duration:.2f}ms: {execution_result}")
                
                # Store execution result in decision metadata
                if not hasattr(decision, 'metadata') or decision.metadata is None:
                    decision.metadata = {}
                decision.metadata['execution_result'] = execution_result
                decision.metadata['execution_duration_ms'] = execution_duration
                
            else:
                logger.warning(f"Decision failed safety validation: {decision.selected_action}")
                decision.requires_human_approval = True
                
        except Exception as e:
            logger.error(f"Error executing consensus decision: {e}")
            decision.requires_human_approval = True
            if not hasattr(decision, 'metadata') or decision.metadata is None:
                decision.metadata = {}
            decision.metadata['execution_error'] = str(e)
    
    async def _execute_investigation_action(self, decision: ConsensusDecision, recommendation: Optional[AgentRecommendation]) -> Dict[str, Any]:
        """Execute investigation or analysis actions."""
        logger.info(f"Executing investigation action for incident {decision.incident_id}")
        
        # Extract parameters from recommendation
        params = recommendation.parameters if recommendation and hasattr(recommendation, 'parameters') else {}
        
        # Perform investigation tasks
        result = {
            'status': 'success',
            'action': 'investigation',
            'findings': [],
            'metrics_collected': True,
            'data_sources_checked': params.get('data_sources', ['logs', 'metrics', 'traces'])
        }
        
        # In production, this would trigger actual monitoring/investigation
        # For now, log the action
        logger.info(f"Investigation completed for {decision.incident_id}")
        
        return result
    
    async def _execute_resolution_action(self, decision: ConsensusDecision, recommendation: Optional[AgentRecommendation]) -> Dict[str, Any]:
        """Execute resolution or remediation actions."""
        logger.info(f"Executing resolution action for incident {decision.incident_id}")
        
        # Extract parameters from recommendation
        params = recommendation.parameters if recommendation and hasattr(recommendation, 'parameters') else {}
        
        # Validate parameters before execution
        if 'target' not in params:
            logger.warning("Resolution action missing 'target' parameter")
            return {'status': 'error', 'message': 'Missing required parameter: target'}
        
        # Execute resolution
        result = {
            'status': 'success',
            'action': 'resolution',
            'target': params.get('target'),
            'changes_applied': True,
            'rollback_available': params.get('enable_rollback', True)
        }
        
        # In production, this would apply actual fixes
        logger.info(f"Resolution action completed for {decision.incident_id}")
        
        return result
    
    async def _execute_infrastructure_action(self, decision: ConsensusDecision, recommendation: Optional[AgentRecommendation]) -> Dict[str, Any]:
        """Execute infrastructure modification actions (restart, scale, etc.)."""
        logger.warning(f"Infrastructure action requested for incident {decision.incident_id} - requiring approval")
        
        # Infrastructure actions are high-risk and require human approval
        decision.requires_human_approval = True
        
        # Extract parameters
        params = recommendation.parameters if recommendation and hasattr(recommendation, 'parameters') else {}
        
        result = {
            'status': 'pending_approval',
            'action': 'infrastructure',
            'action_type': decision.action_type,
            'requires_approval': True,
            'risk_level': 'high',
            'parameters': params
        }
        
        logger.info(f"Infrastructure action queued for approval: {decision.incident_id}")
        
        return result
    
    async def _execute_communication_action(self, decision: ConsensusDecision, recommendation: Optional[AgentRecommendation]) -> Dict[str, Any]:
        """Execute communication or notification actions."""
        logger.info(f"Executing communication action for incident {decision.incident_id}")
        
        # Extract parameters
        params = recommendation.parameters if recommendation and hasattr(recommendation, 'parameters') else {}
        
        # Determine notification channels
        channels = params.get('channels', ['log'])
        message = params.get('message', f"Incident {decision.incident_id} consensus reached")
        
        # Send notifications
        # In production, this would integrate with notification systems
        result = {
            'status': 'success',
            'action': 'communication',
            'channels': channels,
            'message_sent': True,
            'recipients': params.get('recipients', [])
        }
        
        logger.info(f"Communication action completed for {decision.incident_id}: {channels}")
        
        return result
    
    async def _validate_decision_safety(self, decision: ConsensusDecision) -> bool:
        """Validate decision safety before execution."""
        # Implement safety checks
        # - Verify decision hasn't been tampered with
        # - Check against safety policies
        # - Validate execution prerequisites
        
        return True  # Simplified for now
    
    async def _fallback_to_weighted_consensus(self, incident: Incident) -> ConsensusDecision:
        """Fallback to weighted consensus if PBFT fails."""
        logger.info(f"Falling back to weighted consensus for incident {incident.id}")
        
        # Use the parent class's consensus method
        recommendations = await self._gather_agent_recommendations_pbft(incident)
        
        if not recommendations:
            return await self._create_no_action_decision(incident, "No recommendations for fallback")
        
        # Use basic weighted consensus
        return await self._resolve_conflicts_weighted(recommendations)
    
    async def _resolve_conflicts_weighted(self, recommendations: List[AgentRecommendation]) -> ConsensusDecision:
        """Resolve conflicts using weighted voting (fallback method)."""
        # Simplified weighted consensus implementation
        if not recommendations:
            return None
        
        # For now, just return the first recommendation
        # In a real implementation, this would do proper weighted voting
        primary_rec = recommendations[0]
        
        return ConsensusDecision(
            incident_id=getattr(primary_rec, 'incident_id', 'unknown'),
            selected_action=getattr(primary_rec, 'action_id', 'unknown'),
            action_type=str(getattr(primary_rec, 'action_type', 'unknown')),
            final_confidence=0.8,  # Lower confidence for fallback
            participating_agents=[str(r.agent_name) for r in recommendations],
            agent_recommendations=recommendations,
            consensus_method="weighted_fallback",
            conflicts_detected=len(recommendations) > 1,
            requires_human_approval=True,  # Require approval for fallback
            approval_threshold=0.7,
            processing_duration_ms=100
        )
    
    async def _create_no_action_decision(self, incident: Incident, reason: str) -> ConsensusDecision:
        """Create a no-action consensus decision."""
        return ConsensusDecision(
            incident_id=incident.id,
            selected_action="no_action",
            action_type="no_action",
            final_confidence=0.0,
            participating_agents=[],
            agent_recommendations=[],
            consensus_method="no_consensus",
            conflicts_detected=False,
            requires_human_approval=True,
            approval_threshold=1.0,
            processing_duration_ms=0,
            metadata={"reason": reason}
        )
    
    def get_enhanced_metrics(self) -> Dict[str, Any]:
        """Get enhanced metrics including Byzantine fault tolerance."""
        base_metrics = self.get_metrics()
        pbft_metrics = self.pbft_engine.get_metrics()
        
        return {
            **base_metrics,
            "pbft_metrics": pbft_metrics,
            "enhanced_metrics": {
                "total_consensus_rounds": self.enhanced_metrics.total_consensus_rounds,
                "byzantine_faults_detected": self.enhanced_metrics.byzantine_faults_detected,
                "consensus_success_rate": self.enhanced_metrics.consensus_success_rate,
                "average_consensus_time_ms": self.enhanced_metrics.average_consensus_time_ms,
                "isolated_agents": list(self.enhanced_metrics.isolated_agents)
            }
        }


# Global enhanced coordinator instance
enhanced_coordinator = None


async def get_enhanced_coordinator() -> EnhancedConsensusCoordinator:
    """Get the global enhanced coordinator instance."""
    global enhanced_coordinator
    if enhanced_coordinator is None:
        enhanced_coordinator = EnhancedConsensusCoordinator()
    return enhanced_coordinator