"""
Byzantine Fault Tolerant Consensus Engine with AWS Step Functions integration.

This module implements a Byzantine fault tolerant consensus mechanism that can handle
compromised agents and ensure system integrity even when some agents provide
malicious or incorrect recommendations.
"""

import asyncio
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict

import boto3
from botocore.exceptions import ClientError

from src.interfaces.consensus import ConsensusEngine
from src.models.incident import Incident
from src.models.agent import AgentRecommendation, ConsensusDecision, HumanEscalation, AgentType
from src.services.aws import AWSServiceFactory
from src.utils.constants import CONSENSUS_CONFIG
from src.utils.logging import get_logger
from src.utils.exceptions import ConsensusTimeoutError, ByzantineAttackDetectedError


logger = get_logger("byzantine_consensus")


@dataclass
class AgentValidationResult:
    """Result of agent validation check."""
    agent_name: str
    is_valid: bool
    confidence_score: float
    validation_errors: List[str]
    integrity_hash: str
    timestamp: datetime


@dataclass
class ConsensusRound:
    """Represents a single round of Byzantine consensus."""
    round_id: str
    incident_id: str
    participating_agents: List[str]
    recommendations: List[AgentRecommendation]
    validation_results: List[AgentValidationResult]
    byzantine_agents: Set[str]
    consensus_reached: bool
    selected_action: Optional[str]
    final_confidence: float
    round_duration_ms: int


class ByzantineFaultTolerantConsensus(ConsensusEngine):
    """
    Byzantine Fault Tolerant Consensus Engine using AWS Step Functions.
    
    Implements a modified PBFT (Practical Byzantine Fault Tolerance) algorithm
    adapted for incident response agent coordination.
    """
    
    def __init__(self, aws_factory: AWSServiceFactory):
        """Initialize Byzantine consensus engine."""
        self.aws_factory = aws_factory
        self.agent_weights = CONSENSUS_CONFIG["agent_weights"]
        self.confidence_threshold = CONSENSUS_CONFIG["autonomous_confidence_threshold"]
        self.byzantine_threshold = 0.33  # Can tolerate up to 1/3 Byzantine agents
        
        # Step Functions configuration
        self.step_functions_arn = None  # Will be set from environment
        self.consensus_timeout = timedelta(minutes=5)
        
        # Byzantine detection parameters
        self.min_agreement_threshold = 0.67  # 2/3 agreement required
        self.max_confidence_deviation = 0.3  # Max allowed confidence deviation
        self.integrity_check_enabled = True
        
        # Consensus history and learning
        self.consensus_rounds: List[ConsensusRound] = []
        self.agent_reputation: Dict[str, float] = defaultdict(lambda: 1.0)
        self.byzantine_detection_history: Dict[str, List[datetime]] = defaultdict(list)
        
        logger.info("Initialized Byzantine Fault Tolerant Consensus Engine")
    
    async def reach_consensus(self, incident: Incident, 
                            recommendations: List[AgentRecommendation]) -> ConsensusDecision:
        """
        Reach Byzantine fault tolerant consensus on incident response.
        
        Args:
            incident: The incident requiring consensus
            recommendations: Agent recommendations to consider
            
        Returns:
            Consensus decision with Byzantine fault tolerance
        """
        start_time = time.time()
        round_id = f"consensus_{incident.id}_{int(start_time)}"
        
        try:
            logger.info(f"Starting Byzantine consensus round {round_id} for incident {incident.id}")
            
            # Validate input
            if not recommendations:
                return await self._create_no_action_decision(incident, "No recommendations provided")
            
            # Phase 1: Agent Validation and Integrity Checking
            validation_results = await self._validate_all_agents(recommendations)
            
            # Phase 2: Byzantine Fault Detection
            byzantine_agents = await self._detect_byzantine_agents(recommendations, validation_results)
            
            # Phase 3: Filter out Byzantine agents
            valid_recommendations = await self._filter_byzantine_recommendations(
                recommendations, byzantine_agents
            )
            
            if not valid_recommendations:
                return await self._create_no_action_decision(
                    incident, f"All agents flagged as Byzantine: {list(byzantine_agents)}"
                )
            
            # Phase 4: Multi-round consensus with Step Functions
            consensus_result = await self._execute_step_functions_consensus(
                incident, valid_recommendations, round_id
            )
            
            # Phase 5: Final validation and decision creation
            final_decision = await self._create_consensus_decision(
                incident, consensus_result, byzantine_agents, start_time
            )
            
            # Update agent reputation based on consensus outcome
            await self._update_agent_reputation(recommendations, final_decision, byzantine_agents)
            
            # Store consensus round for analysis
            consensus_round = ConsensusRound(
                round_id=round_id,
                incident_id=incident.id,
                participating_agents=[r.agent_name.value if hasattr(r.agent_name, 'value') else str(r.agent_name) for r in recommendations],
                recommendations=recommendations,
                validation_results=validation_results,
                byzantine_agents=byzantine_agents,
                consensus_reached=final_decision.final_confidence >= self.confidence_threshold,
                selected_action=final_decision.selected_action,
                final_confidence=final_decision.final_confidence,
                round_duration_ms=int((time.time() - start_time) * 1000)
            )
            self.consensus_rounds.append(consensus_round)
            
            logger.info(f"Byzantine consensus completed for {incident.id}: "
                       f"action={final_decision.selected_action}, "
                       f"confidence={final_decision.final_confidence:.2f}, "
                       f"byzantine_agents={list(byzantine_agents)}")
            
            return final_decision
            
        except Exception as e:
            logger.error(f"Byzantine consensus failed for incident {incident.id}: {e}")
            return await self._create_error_decision(incident, str(e))
    
    async def _validate_all_agents(self, recommendations: List[AgentRecommendation]) -> List[AgentValidationResult]:
        """Validate all agent recommendations for integrity and consistency."""
        validation_results = []
        
        for recommendation in recommendations:
            agent_name = recommendation.agent_name.value if hasattr(recommendation.agent_name, 'value') else str(recommendation.agent_name)
            
            # Perform comprehensive validation
            validation_result = await self._validate_single_agent(agent_name, recommendation)
            validation_results.append(validation_result)
        
        return validation_results
    
    async def _validate_single_agent(self, agent_name: str, 
                                   recommendation: AgentRecommendation) -> AgentValidationResult:
        """Validate a single agent's recommendation."""
        validation_errors = []
        confidence_score = 1.0
        
        # Check 1: Basic field validation
        if not recommendation.reasoning or len(recommendation.reasoning) < 10:
            validation_errors.append("Insufficient reasoning provided")
            confidence_score -= 0.2
        
        # Check 2: Confidence bounds validation
        if not (0.0 <= recommendation.confidence <= 1.0):
            validation_errors.append(f"Invalid confidence: {recommendation.confidence}")
            confidence_score -= 0.3
        
        # Check 3: Urgency bounds validation
        if not (0.0 <= recommendation.urgency <= 1.0):
            validation_errors.append(f"Invalid urgency: {recommendation.urgency}")
            confidence_score -= 0.2
        
        # Check 4: Agent reputation check
        agent_reputation = self.agent_reputation.get(agent_name, 1.0)
        if agent_reputation < 0.5:
            validation_errors.append(f"Low agent reputation: {agent_reputation:.2f}")
            confidence_score -= 0.3
        
        # Check 5: Historical consistency check
        if await self._check_historical_inconsistency(agent_name, recommendation):
            validation_errors.append("Recommendation inconsistent with agent history")
            confidence_score -= 0.2
        
        # Check 6: Evidence validation
        if hasattr(recommendation, 'evidence') and recommendation.evidence:
            evidence_confidence = await self._validate_evidence(recommendation.evidence)
            if evidence_confidence < 0.5:
                validation_errors.append("Weak or inconsistent evidence")
                confidence_score -= 0.2
        
        # Generate integrity hash
        integrity_hash = self._generate_integrity_hash(recommendation)
        
        # Ensure confidence score is within bounds
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        return AgentValidationResult(
            agent_name=agent_name,
            is_valid=len(validation_errors) == 0,
            confidence_score=confidence_score,
            validation_errors=validation_errors,
            integrity_hash=integrity_hash,
            timestamp=datetime.utcnow()
        )
    
    async def _detect_byzantine_agents(self, recommendations: List[AgentRecommendation],
                                     validation_results: List[AgentValidationResult]) -> Set[str]:
        """Detect potentially Byzantine (compromised) agents."""
        byzantine_agents = set()
        
        # Method 1: Validation-based detection
        for validation_result in validation_results:
            if not validation_result.is_valid or validation_result.confidence_score < 0.3:
                byzantine_agents.add(validation_result.agent_name)
                logger.warning(f"Agent {validation_result.agent_name} flagged as Byzantine: "
                             f"errors={validation_result.validation_errors}")
        
        # Method 2: Outlier detection based on confidence scores
        confidences = [r.confidence for r in recommendations]
        if len(confidences) >= 3:
            median_confidence = sorted(confidences)[len(confidences) // 2]
            
            for recommendation in recommendations:
                agent_name = recommendation.agent_name.value if hasattr(recommendation.agent_name, 'value') else str(recommendation.agent_name)
                confidence_deviation = abs(recommendation.confidence - median_confidence)
                
                if confidence_deviation > self.max_confidence_deviation:
                    byzantine_agents.add(agent_name)
                    logger.warning(f"Agent {agent_name} flagged as Byzantine: "
                                 f"confidence deviation {confidence_deviation:.2f}")
        
        # Method 3: Consensus disagreement detection
        action_votes = Counter(r.action_id for r in recommendations)
        if len(action_votes) > 1:
            # Find agents voting for minority actions
            majority_action = action_votes.most_common(1)[0][0]
            majority_count = action_votes[majority_action]
            
            # If less than 2/3 agree on majority action, check for Byzantine behavior
            if majority_count / len(recommendations) < self.min_agreement_threshold:
                for recommendation in recommendations:
                    agent_name = recommendation.agent_name.value if hasattr(recommendation.agent_name, 'value') else str(recommendation.agent_name)
                    if recommendation.action_id != majority_action and recommendation.confidence > 0.8:
                        # High confidence in minority action could indicate Byzantine behavior
                        byzantine_agents.add(agent_name)
                        logger.warning(f"Agent {agent_name} flagged as Byzantine: "
                                     f"high confidence in minority action")
        
        # Method 4: Historical pattern analysis
        for recommendation in recommendations:
            agent_name = recommendation.agent_name.value if hasattr(recommendation.agent_name, 'value') else str(recommendation.agent_name)
            if await self._check_byzantine_pattern(agent_name):
                byzantine_agents.add(agent_name)
        
        # Ensure we don't flag more than 1/3 of agents as Byzantine
        max_byzantine = max(1, int(len(recommendations) * self.byzantine_threshold))  # At least 1 can be Byzantine
        if len(byzantine_agents) > max_byzantine:
            # Keep only the most suspicious agents
            agent_suspicion_scores = {}
            for agent in byzantine_agents:
                validation_result = next((v for v in validation_results if v.agent_name == agent), None)
                if validation_result:
                    agent_suspicion_scores[agent] = 1.0 - validation_result.confidence_score
                else:
                    agent_suspicion_scores[agent] = 0.5
            
            # Sort by suspicion score and keep top offenders
            sorted_agents = sorted(agent_suspicion_scores.items(), key=lambda x: x[1], reverse=True)
            byzantine_agents = set(agent for agent, _ in sorted_agents[:max_byzantine])
        
        return byzantine_agents
    
    async def _filter_byzantine_recommendations(self, recommendations: List[AgentRecommendation],
                                              byzantine_agents: Set[str]) -> List[AgentRecommendation]:
        """Filter out recommendations from Byzantine agents."""
        valid_recommendations = []
        
        for recommendation in recommendations:
            agent_name = recommendation.agent_name.value if hasattr(recommendation.agent_name, 'value') else str(recommendation.agent_name)
            if agent_name not in byzantine_agents:
                valid_recommendations.append(recommendation)
        
        logger.info(f"Filtered {len(recommendations) - len(valid_recommendations)} Byzantine recommendations")
        return valid_recommendations
    
    async def _execute_step_functions_consensus(self, incident: Incident,
                                              recommendations: List[AgentRecommendation],
                                              round_id: str) -> Dict[str, Any]:
        """Execute consensus using AWS Step Functions for distributed coordination."""
        try:
            # For now, implement local consensus logic
            # In production, this would trigger a Step Functions state machine
            
            # Calculate weighted confidence for each action
            action_confidences = await self._calculate_weighted_confidence_byzantine(recommendations)
            
            if not action_confidences:
                return {
                    "consensus_reached": False,
                    "selected_action": "no_action",
                    "final_confidence": 0.0,
                    "reason": "No valid actions after Byzantine filtering"
                }
            
            # Find the action with highest weighted confidence
            best_action_id = max(action_confidences.keys(), key=lambda k: action_confidences[k])
            best_confidence = action_confidences[best_action_id]
            
            # Check if we have sufficient agreement (2/3 threshold)
            total_agents = len(recommendations)
            supporting_agents = sum(1 for r in recommendations if r.action_id == best_action_id)
            agreement_ratio = supporting_agents / total_agents
            
            consensus_reached = (
                best_confidence >= self.confidence_threshold and 
                agreement_ratio >= self.min_agreement_threshold
            )
            
            return {
                "consensus_reached": consensus_reached,
                "selected_action": best_action_id,
                "final_confidence": best_confidence,
                "agreement_ratio": agreement_ratio,
                "supporting_agents": supporting_agents,
                "total_agents": total_agents,
                "action_confidences": action_confidences
            }
            
        except Exception as e:
            logger.error(f"Step Functions consensus execution failed: {e}")
            return {
                "consensus_reached": False,
                "selected_action": "error",
                "final_confidence": 0.0,
                "error": str(e)
            }
    
    async def _calculate_weighted_confidence_byzantine(self, 
                                                    recommendations: List[AgentRecommendation]) -> Dict[str, float]:
        """Calculate weighted confidence with Byzantine fault tolerance."""
        action_scores = defaultdict(float)
        action_weights = defaultdict(float)
        
        for recommendation in recommendations:
            agent_name = recommendation.agent_name.value if hasattr(recommendation.agent_name, 'value') else str(recommendation.agent_name)
            
            # Get base agent weight
            base_weight = self.agent_weights.get(agent_name, 0.1)
            
            # Apply reputation multiplier
            reputation = self.agent_reputation.get(agent_name, 1.0)
            adjusted_weight = base_weight * reputation
            
            # Calculate weighted confidence
            weighted_confidence = recommendation.confidence * adjusted_weight
            
            # Accumulate scores
            action_scores[recommendation.action_id] += weighted_confidence
            action_weights[recommendation.action_id] += adjusted_weight
        
        # Normalize by total weight for each action
        normalized_scores = {}
        for action_id, total_score in action_scores.items():
            total_weight = action_weights[action_id]
            normalized_scores[action_id] = total_score / total_weight if total_weight > 0 else 0.0
        
        return normalized_scores
    
    async def _create_consensus_decision(self, incident: Incident,
                                       consensus_result: Dict[str, Any],
                                       byzantine_agents: Set[str],
                                       start_time: float) -> ConsensusDecision:
        """Create the final consensus decision."""
        processing_duration = int((time.time() - start_time) * 1000)
        
        # Determine if human approval is required
        requires_approval = (
            not consensus_result["consensus_reached"] or
            consensus_result["final_confidence"] < self.confidence_threshold or
            len(byzantine_agents) > 0
        )
        
        # Generate decision rationale
        rationale_parts = [
            f"Byzantine consensus completed with {consensus_result['final_confidence']:.2f} confidence",
            f"Agreement ratio: {consensus_result.get('agreement_ratio', 0):.2f}"
        ]
        
        if byzantine_agents:
            rationale_parts.append(f"Byzantine agents detected: {list(byzantine_agents)}")
        
        if consensus_result.get("error"):
            rationale_parts.append(f"Error: {consensus_result['error']}")
        
        # Ensure confidence is within valid bounds
        final_confidence = max(0.0, min(1.0, consensus_result["final_confidence"]))
        
        decision = ConsensusDecision(
            incident_id=incident.id,
            selected_action=consensus_result["selected_action"],
            action_type=consensus_result["selected_action"],
            final_confidence=final_confidence,
            participating_agents=[],  # Will be filled by caller
            agent_recommendations=[],  # Will be filled by caller
            consensus_method="byzantine_fault_tolerant",
            conflicts_detected=len(byzantine_agents) > 0,
            requires_human_approval=requires_approval,
            approval_threshold=self.confidence_threshold,
            processing_duration_ms=processing_duration,
            decision_rationale=". ".join(rationale_parts),
            risk_assessment=f"Byzantine agents detected: {len(byzantine_agents)}, "
                          f"Consensus confidence: {consensus_result['final_confidence']:.2f}"
        )
        
        return decision
    
    async def _update_agent_reputation(self, recommendations: List[AgentRecommendation],
                                     decision: ConsensusDecision,
                                     byzantine_agents: Set[str]):
        """Update agent reputation based on consensus outcome."""
        for recommendation in recommendations:
            agent_name = recommendation.agent_name.value if hasattr(recommendation.agent_name, 'value') else str(recommendation.agent_name)
            
            if agent_name in byzantine_agents:
                # Decrease reputation for Byzantine agents
                self.agent_reputation[agent_name] *= 0.8
                self.byzantine_detection_history[agent_name].append(datetime.utcnow())
                logger.info(f"Decreased reputation for Byzantine agent {agent_name}: "
                           f"{self.agent_reputation[agent_name]:.2f}")
            else:
                # Increase reputation for honest agents
                self.agent_reputation[agent_name] = min(1.0, self.agent_reputation[agent_name] * 1.05)
        
        # Clean up old Byzantine detection history (keep last 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        for agent_name in self.byzantine_detection_history:
            self.byzantine_detection_history[agent_name] = [
                dt for dt in self.byzantine_detection_history[agent_name] if dt > cutoff_date
            ]
    
    async def _check_historical_inconsistency(self, agent_name: str, 
                                            recommendation: AgentRecommendation) -> bool:
        """Check if recommendation is inconsistent with agent's historical behavior."""
        # Simple implementation - in production would use more sophisticated analysis
        recent_detections = self.byzantine_detection_history.get(agent_name, [])
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_byzantine_count = sum(1 for dt in recent_detections if dt > recent_cutoff)
        
        return recent_byzantine_count >= 3  # 3 or more Byzantine detections in 24 hours
    
    async def _validate_evidence(self, evidence: List[Any]) -> float:
        """Validate evidence provided with recommendation."""
        if not evidence:
            return 0.0
        
        # Simple evidence validation - in production would be more sophisticated
        valid_evidence_count = 0
        for item in evidence:
            if hasattr(item, 'confidence') and 0.0 <= item.confidence <= 1.0:
                valid_evidence_count += 1
        
        return valid_evidence_count / len(evidence) if evidence else 0.0
    
    def _generate_integrity_hash(self, recommendation: AgentRecommendation) -> str:
        """Generate integrity hash for recommendation."""
        # Create a deterministic hash of key recommendation fields
        hash_data = {
            "agent_name": recommendation.agent_name.value if hasattr(recommendation.agent_name, 'value') else str(recommendation.agent_name),
            "action_id": recommendation.action_id,
            "confidence": recommendation.confidence,
            "reasoning": recommendation.reasoning,
            "urgency": recommendation.urgency
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()[:16]
    
    async def _check_byzantine_pattern(self, agent_name: str) -> bool:
        """Check if agent shows Byzantine behavior patterns."""
        recent_detections = self.byzantine_detection_history.get(agent_name, [])
        
        # Check for frequent Byzantine detections
        if len(recent_detections) >= 5:
            return True
        
        # Check for recent Byzantine behavior
        recent_cutoff = datetime.utcnow() - timedelta(hours=6)
        recent_count = sum(1 for dt in recent_detections if dt > recent_cutoff)
        
        return recent_count >= 2
    
    async def _create_no_action_decision(self, incident: Incident, reason: str) -> ConsensusDecision:
        """Create a no-action consensus decision."""
        return ConsensusDecision(
            incident_id=incident.id,
            selected_action="no_action",
            action_type="no_action",
            final_confidence=0.0,
            participating_agents=[],
            agent_recommendations=[],
            consensus_method="byzantine_no_action",
            conflicts_detected=False,
            requires_human_approval=True,
            approval_threshold=self.confidence_threshold,
            decision_rationale=f"No action taken: {reason}",
            risk_assessment="Unable to reach Byzantine fault tolerant consensus"
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
            consensus_method="byzantine_error",
            conflicts_detected=True,
            requires_human_approval=True,
            approval_threshold=self.confidence_threshold,
            decision_rationale=f"Byzantine consensus error: {error_msg}",
            risk_assessment="System error during Byzantine consensus process"
        )
    
    async def detect_byzantine_faults(self, recommendations: List[AgentRecommendation]) -> List[str]:
        """Detect potentially compromised agents based on recommendations."""
        validation_results = await self._validate_all_agents(recommendations)
        byzantine_agents = await self._detect_byzantine_agents(recommendations, validation_results)
        return list(byzantine_agents)
    
    async def validate_agent_integrity(self, agent_name: str, 
                                     recommendation: AgentRecommendation) -> bool:
        """Validate that an agent's recommendation is legitimate."""
        validation_result = await self._validate_single_agent(agent_name, recommendation)
        return validation_result.is_valid
    
    async def escalate_to_human(self, incident: Incident, 
                              recommendations: List[AgentRecommendation],
                              reason: str) -> HumanEscalation:
        """Escalate decision to human when consensus cannot be reached."""
        return HumanEscalation(
            incident_id=incident.id,
            reason=reason,
            recommendations=recommendations,
            escalation_level="senior_sre",
            required_approval_level="senior_sre",
            escalated_at=datetime.utcnow(),
            timeout_minutes=30
        )
    
    def get_byzantine_statistics(self) -> Dict[str, Any]:
        """Get Byzantine consensus statistics."""
        if not self.consensus_rounds:
            return {
                "total_rounds": 0,
                "byzantine_detection_rate": 0.0,
                "consensus_success_rate": 0.0,
                "average_confidence": 0.0,
                "agent_reputation_scores": dict(self.agent_reputation)
            }
        
        total_rounds = len(self.consensus_rounds)
        byzantine_rounds = sum(1 for r in self.consensus_rounds if r.byzantine_agents)
        successful_rounds = sum(1 for r in self.consensus_rounds if r.consensus_reached)
        avg_confidence = sum(r.final_confidence for r in self.consensus_rounds) / total_rounds
        
        return {
            "total_rounds": total_rounds,
            "byzantine_detection_rate": byzantine_rounds / total_rounds,
            "consensus_success_rate": successful_rounds / total_rounds,
            "average_confidence": avg_confidence,
            "agent_reputation_scores": dict(self.agent_reputation),
            "total_byzantine_detections": sum(len(detections) for detections in self.byzantine_detection_history.values())
        }


# Global Byzantine consensus engine instance
byzantine_consensus_engine: Optional[ByzantineFaultTolerantConsensus] = None


def get_byzantine_consensus_engine(aws_factory: AWSServiceFactory) -> ByzantineFaultTolerantConsensus:
    """Get or create global Byzantine consensus engine instance."""
    global byzantine_consensus_engine
    if byzantine_consensus_engine is None:
        byzantine_consensus_engine = ByzantineFaultTolerantConsensus(aws_factory)
    return byzantine_consensus_engine