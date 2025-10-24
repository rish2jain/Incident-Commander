"""
Consensus engine interface for multi-agent decision making.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.models.agent import AgentRecommendation, ConsensusDecision, HumanEscalation
from src.models.incident import Incident


class ConsensusEngine(ABC):
    """Abstract consensus engine interface."""
    
    @abstractmethod
    async def reach_consensus(self, incident: Incident, 
                            recommendations: List[AgentRecommendation]) -> ConsensusDecision:
        """
        Reach consensus on the best action for an incident.
        
        Args:
            incident: The incident requiring action
            recommendations: List of agent recommendations
            
        Returns:
            Consensus decision
            
        Raises:
            ConsensusTimeoutError: If consensus cannot be reached within timeout
            InsufficientConfidenceError: If confidence is below threshold
        """
        pass
    
    @abstractmethod
    async def detect_byzantine_faults(self, recommendations: List[AgentRecommendation]) -> List[str]:
        """
        Detect potentially compromised agents based on recommendations.
        
        Args:
            recommendations: List of agent recommendations to analyze
            
        Returns:
            List of agent names that may be compromised
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass


class WeightedConsensusEngine(ConsensusEngine):
    """Consensus engine using weighted voting."""
    
    @abstractmethod
    async def calculate_weighted_confidence(self, recommendations: List[AgentRecommendation]) -> Dict[str, float]:
        """
        Calculate weighted confidence scores for each unique action.
        
        Args:
            recommendations: List of agent recommendations
            
        Returns:
            Dictionary mapping action_id to weighted confidence
        """
        pass
    
    @abstractmethod
    async def resolve_conflicts(self, recommendations: List[AgentRecommendation]) -> AgentRecommendation:
        """
        Resolve conflicts between competing recommendations.
        
        Args:
            recommendations: Conflicting recommendations
            
        Returns:
            Selected recommendation after conflict resolution
        """
        pass


class ByzantineFaultTolerantConsensus(ConsensusEngine):
    """Byzantine fault tolerant consensus implementation."""
    
    @abstractmethod
    async def verify_agent_signatures(self, recommendations: List[AgentRecommendation]) -> bool:
        """
        Verify cryptographic signatures on agent recommendations.
        
        Args:
            recommendations: Recommendations to verify
            
        Returns:
            True if all signatures are valid
        """
        pass
    
    @abstractmethod
    async def quarantine_suspicious_agent(self, agent_name: str, reason: str) -> None:
        """
        Quarantine a potentially compromised agent.
        
        Args:
            agent_name: Name of agent to quarantine
            reason: Reason for quarantine
        """
        pass
    
    @abstractmethod
    async def get_minimum_trusted_agents(self) -> int:
        """
        Get minimum number of trusted agents required for consensus.
        
        Returns:
            Minimum number of trusted agents (typically 3)
        """
        pass


class DistributedConsensusOrchestrator(ConsensusEngine):
    """Distributed consensus using AWS Step Functions."""
    
    @abstractmethod
    async def start_consensus_workflow(self, incident_id: str, 
                                     recommendations: List[AgentRecommendation]) -> str:
        """
        Start distributed consensus workflow.
        
        Args:
            incident_id: ID of the incident
            recommendations: Agent recommendations
            
        Returns:
            Workflow execution ARN
        """
        pass
    
    @abstractmethod
    async def get_workflow_status(self, execution_arn: str) -> Dict[str, Any]:
        """
        Get status of consensus workflow.
        
        Args:
            execution_arn: Workflow execution ARN
            
        Returns:
            Workflow status and results
        """
        pass
    
    @abstractmethod
    async def handle_workflow_timeout(self, execution_arn: str) -> ConsensusDecision:
        """
        Handle consensus workflow timeout.
        
        Args:
            execution_arn: Timed out workflow execution ARN
            
        Returns:
            Fallback consensus decision
        """
        pass