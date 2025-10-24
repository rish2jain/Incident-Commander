"""
Basic consensus engine implementation for agent coordination.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

from src.interfaces.consensus import WeightedConsensusEngine, ConsensusEngine
from src.models.incident import Incident
from src.models.agent import AgentRecommendation, ConsensusDecision, HumanEscalation, AgentType
from src.utils.constants import CONSENSUS_CONFIG
from src.utils.logging import get_logger
from src.utils.exceptions import ConsensusTimeoutError, InsufficientConfidenceError


logger = get_logger("consensus")


class BasicWeightedConsensusEngine(WeightedConsensusEngine):
    """Basic weighted consensus engine for Milestone 1."""
    
    def __init__(self):
        """Initialize consensus engine with configuration."""
        self.agent_weights = CONSENSUS_CONFIG["agent_weights"]
        self.confidence_threshold = CONSENSUS_CONFIG["autonomous_confidence_threshold"]
        self.decision_timeout = CONSENSUS_CONFIG["decision_timeout"]
        
        # Track consensus history for learning
        self.consensus_history: List[ConsensusDecision] = []
        
    async def reach_consensus(self, incident: Incident, 
                            recommendations: List[AgentRecommendation]) -> ConsensusDecision:
        """
        Reach consensus on the best action for an incident.
        
        Args:
            incident: The incident requiring action
            recommendations: List of agent recommendations
            
        Returns:
            Consensus decision
        """
        start_time = time.time()
        
        try:
            logger.info(f"Starting consensus for incident {incident.id} with {len(recommendations)} recommendations")
            
            # Validate input recommendations
            if not recommendations:
                return await self._create_no_action_decision(incident, "No recommendations provided")
            
            # Check for Byzantine faults
            suspicious_agents = await self.detect_byzantine_faults(recommendations)
            if suspicious_agents:
                logger.warning(f"Detected suspicious agents: {suspicious_agents}")
                # Filter out suspicious recommendations
                recommendations = [r for r in recommendations 
                                 if (r.agent_name.value if hasattr(r.agent_name, 'value') else str(r.agent_name)) not in suspicious_agents]
            
            # Calculate weighted confidence for each unique action
            action_confidences = await self.calculate_weighted_confidence(recommendations)
            
            if not action_confidences:
                return await self._create_no_action_decision(incident, "No valid recommendations after filtering")
            
            # Find the action with highest confidence
            best_action_id = max(action_confidences.keys(), key=lambda k: action_confidences[k])
            best_confidence = action_confidences[best_action_id]
            
            # Get the recommendation for the best action
            selected_recommendation = next(
                (r for r in recommendations if r.action_id == best_action_id), 
                None
            )
            
            if not selected_recommendation:
                return await self._create_no_action_decision(incident, "Could not find selected recommendation")
            
            # Check if confidence meets threshold
            requires_escalation = best_confidence < self.confidence_threshold
            
            # Detect conflicts
            conflicts_detected = len(action_confidences) > 1 and len(recommendations) > 1
            
            # Create consensus decision
            decision = ConsensusDecision(
                incident_id=incident.id,
                selected_action=selected_recommendation.action_id,
                action_type=selected_recommendation.action_type.value if hasattr(selected_recommendation.action_type, 'value') else str(selected_recommendation.action_type),
                final_confidence=best_confidence,
                participating_agents=[r.agent_name.value if hasattr(r.agent_name, 'value') else str(r.agent_name) for r in recommendations],
                agent_recommendations=recommendations,
                consensus_method="weighted_voting",
                conflicts_detected=conflicts_detected,
                requires_human_approval=requires_escalation,
                approval_threshold=self.confidence_threshold,
                processing_duration_ms=int((time.time() - start_time) * 1000),
                decision_rationale=self._generate_decision_rationale(
                    selected_recommendation, best_confidence, action_confidences
                )
            )
            
            # Store in history
            self.consensus_history.append(decision)
            
            # Log decision
            logger.info(f"Consensus reached for incident {incident.id}: "
                       f"action={decision.selected_action}, confidence={decision.final_confidence:.2f}, "
                       f"escalation_required={decision.requires_human_approval}")
            
            return decision
            
        except Exception as e:
            logger.error(f"Consensus failed for incident {incident.id}: {e}")
            return await self._create_error_decision(incident, str(e))
    
    async def calculate_weighted_confidence(self, recommendations: List[AgentRecommendation]) -> Dict[str, float]:
        """
        Calculate weighted confidence scores for each unique action.
        
        Args:
            recommendations: List of agent recommendations
            
        Returns:
            Dictionary mapping action_id to weighted confidence
        """
        action_scores = defaultdict(float)
        action_counts = defaultdict(int)
        
        for recommendation in recommendations:
            agent_name = recommendation.agent_name.value if hasattr(recommendation.agent_name, 'value') else str(recommendation.agent_name)
            agent_weight = self.agent_weights.get(agent_name, 0.1)  # Default weight for unknown agents
            
            # Calculate weighted confidence
            weighted_confidence = recommendation.confidence * agent_weight
            
            # Add to action score
            action_scores[recommendation.action_id] += weighted_confidence
            action_counts[recommendation.action_id] += 1
        
        # Normalize by number of agents supporting each action
        normalized_scores = {}
        for action_id, total_score in action_scores.items():
            count = action_counts[action_id]
            normalized_scores[action_id] = total_score / count if count > 0 else 0.0
        
        return normalized_scores
    
    async def resolve_conflicts(self, recommendations: List[AgentRecommendation]) -> AgentRecommendation:
        """
        Resolve conflicts between competing recommendations.
        
        Args:
            recommendations: Conflicting recommendations
            
        Returns:
            Selected recommendation after conflict resolution
        """
        if len(recommendations) <= 1:
            return recommendations[0] if recommendations else None
        
        # Calculate weighted confidence for each recommendation
        weighted_recommendations = []
        
        for recommendation in recommendations:
            agent_name = recommendation.agent_name.value if hasattr(recommendation.agent_name, 'value') else str(recommendation.agent_name)
            agent_weight = self.agent_weights.get(agent_name, 0.1)
            weighted_confidence = recommendation.confidence * agent_weight
            
            weighted_recommendations.append((recommendation, weighted_confidence))
        
        # Sort by weighted confidence
        weighted_recommendations.sort(key=lambda x: x[1], reverse=True)
        
        # Return the highest weighted recommendation
        return weighted_recommendations[0][0]
    
    async def detect_byzantine_faults(self, recommendations: List[AgentRecommendation]) -> List[str]:
        """
        Detect potentially compromised agents based on recommendations.
        
        Args:
            recommendations: List of agent recommendations to analyze
            
        Returns:
            List of agent names that may be compromised
        """
        suspicious_agents = []
        
        for recommendation in recommendations:
            agent_name = recommendation.agent_name.value if hasattr(recommendation.agent_name, 'value') else str(recommendation.agent_name)
            
            # Check for impossible confidence scores
            if recommendation.confidence < 0.0 or recommendation.confidence > 1.0:
                logger.warning(f"Agent {agent_name} provided invalid confidence: {recommendation.confidence}")
                suspicious_agents.append(agent_name)
                continue
            
            # Check for extremely high confidence without evidence
            if recommendation.confidence > 0.95 and len(recommendation.evidence) == 0:
                logger.warning(f"Agent {agent_name} provided very high confidence without evidence")
                suspicious_agents.append(agent_name)
                continue
            
            # Check for contradictory evidence
            if recommendation.evidence:
                evidence_confidences = [e.confidence for e in recommendation.evidence]
                avg_evidence_confidence = sum(evidence_confidences) / len(evidence_confidences)
                
                # If recommendation confidence is much higher than evidence supports
                if recommendation.confidence > avg_evidence_confidence + 0.3:
                    logger.warning(f"Agent {agent_name} confidence inconsistent with evidence")
                    suspicious_agents.append(agent_name)
        
        return list(set(suspicious_agents))  # Remove duplicates
    
    async def validate_agent_integrity(self, agent_name: str, 
                                     recommendation: AgentRecommendation) -> bool:
        """
        Validate that an agent's recommendation is legitimate.
        
        Args:
            agent_name: Name of the agent
            recommendation: The recommendation to validate
            
        Returns:
            True if recommendation appears legitimate
        """
        # Basic validation checks
        rec_agent_name = recommendation.agent_name.value if hasattr(recommendation.agent_name, 'value') else str(recommendation.agent_name)
        if rec_agent_name != agent_name:
            logger.warning(f"Agent name mismatch: expected {agent_name}, got {rec_agent_name}")
            return False
        
        # Check confidence bounds
        if not (0.0 <= recommendation.confidence <= 1.0):
            logger.warning(f"Invalid confidence score from {agent_name}: {recommendation.confidence}")
            return False
        
        # Check for required fields
        if not recommendation.reasoning or not recommendation.estimated_impact:
            logger.warning(f"Missing required fields in recommendation from {agent_name}")
            return False
        
        # Check urgency bounds
        if not (0.0 <= recommendation.urgency <= 1.0):
            logger.warning(f"Invalid urgency score from {agent_name}: {recommendation.urgency}")
            return False
        
        return True
    
    async def escalate_to_human(self, incident: Incident, 
                              recommendations: List[AgentRecommendation],
                              reason: str) -> HumanEscalation:
        """
        Escalate decision to human when consensus cannot be reached.
        
        Args:
            incident: The incident requiring escalation
            recommendations: Conflicting recommendations
            reason: Reason for escalation
            
        Returns:
            Human escalation request
        """
        # Calculate confidence scores for context
        confidence_scores = {}
        for recommendation in recommendations:
            agent_name = recommendation.agent_name.value if hasattr(recommendation.agent_name, 'value') else str(recommendation.agent_name)
            confidence_scores[agent_name] = recommendation.confidence
        
        # Determine required approval level based on incident severity
        if incident.severity.value in ["critical", "high"]:
            approval_level = "senior_sre"
        else:
            approval_level = "sre_engineer"
        
        # Calculate urgency based on business impact
        cost_per_minute = incident.business_impact.calculate_cost_per_minute()
        urgency = min(1.0, cost_per_minute / 1000.0)  # Normalize to 0-1 scale
        
        escalation = HumanEscalation(
            incident_id=incident.id,
            reason=reason,
            escalation_type="consensus_failure",
            conflicting_recommendations=recommendations,
            confidence_scores=confidence_scores,
            required_approval_level=approval_level,
            urgency=urgency,
            business_justification=f"Incident cost: ${cost_per_minute:.2f}/minute, "
                                 f"affected users: {incident.business_impact.affected_users}",
            risk_assessment=f"Service tier: {incident.business_impact.service_tier.value}, "
                          f"SLA breach risk: {incident.business_impact.sla_breach_risk:.2f}",
            response_required_by=datetime.utcnow() + timedelta(minutes=15)  # 15 minute SLA
        )
        
        logger.warning(f"Escalating incident {incident.id} to human: {reason}")
        return escalation
    
    def _generate_decision_rationale(self, selected_recommendation: AgentRecommendation,
                                   final_confidence: float, 
                                   action_confidences: Dict[str, float]) -> str:
        """Generate human-readable decision rationale."""
        agent_name = selected_recommendation.agent_name.value if hasattr(selected_recommendation.agent_name, 'value') else str(selected_recommendation.agent_name)
        action_id = selected_recommendation.action_id
        
        rationale_parts = [
            f"Selected action '{action_id}' from {agent_name} agent",
            f"Final weighted confidence: {final_confidence:.2f}",
            f"Agent reasoning: {selected_recommendation.reasoning}"
        ]
        
        if len(action_confidences) > 1:
            other_actions = {k: v for k, v in action_confidences.items() if k != action_id}
            rationale_parts.append(f"Alternative actions considered: {other_actions}")
        
        return ". ".join(rationale_parts)
    
    async def _create_no_action_decision(self, incident: Incident, reason: str) -> ConsensusDecision:
        """Create a no-action consensus decision."""
        return ConsensusDecision(
            incident_id=incident.id,
            selected_action="no_action",
            action_type="no_action",
            final_confidence=0.0,
            participating_agents=[],
            agent_recommendations=[],
            consensus_method="no_recommendations",
            conflicts_detected=False,
            requires_human_approval=True,
            approval_threshold=self.confidence_threshold,
            decision_rationale=f"No action taken: {reason}",
            risk_assessment="Unable to determine appropriate action"
        )
    
    async def _create_error_decision(self, incident: Incident, error_msg: str) -> ConsensusDecision:
        """Create an error consensus decision."""
        return ConsensusDecision(
            incident_id=incident.id,
            selected_action="error",
            action_type="error",
            final_confidence=0.0,
            participating_agents=[],
            agent_recommendations=[],
            consensus_method="error",
            conflicts_detected=True,
            requires_human_approval=True,
            approval_threshold=self.confidence_threshold,
            decision_rationale=f"Consensus error: {error_msg}",
            risk_assessment="System error during consensus process"
        )
    
    def get_consensus_statistics(self) -> Dict[str, Any]:
        """Get consensus engine statistics."""
        if not self.consensus_history:
            return {
                "total_decisions": 0,
                "average_confidence": 0.0,
                "escalation_rate": 0.0,
                "conflict_rate": 0.0
            }
        
        total_decisions = len(self.consensus_history)
        escalations = sum(1 for d in self.consensus_history if d.requires_human_approval)
        conflicts = sum(1 for d in self.consensus_history if d.conflicts_detected)
        avg_confidence = sum(d.final_confidence for d in self.consensus_history) / total_decisions
        
        return {
            "total_decisions": total_decisions,
            "average_confidence": avg_confidence,
            "escalation_rate": escalations / total_decisions,
            "conflict_rate": conflicts / total_decisions,
            "average_processing_time_ms": sum(d.processing_duration_ms or 0 for d in self.consensus_history) / total_decisions
        }


# Global consensus engine instance
consensus_engine: Optional[BasicWeightedConsensusEngine] = None


def get_consensus_engine() -> BasicWeightedConsensusEngine:
    """Get or create global consensus engine instance."""
    global consensus_engine
    if consensus_engine is None:
        consensus_engine = BasicWeightedConsensusEngine()
    return consensus_engine