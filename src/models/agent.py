"""
Agent communication and recommendation models.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, ConfigDict


class AgentType(str, Enum):
    """Types of agents in the system."""
    DETECTION = "detection"
    DIAGNOSIS = "diagnosis"
    PREDICTION = "prediction"
    RESOLUTION = "resolution"
    COMMUNICATION = "communication"


class AgentStatus(str, Enum):
    """Status of agents in the system."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ERROR = "error"
    OFFLINE = "offline"


class ActionType(str, Enum):
    """Types of actions agents can recommend."""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    RESTART_SERVICE = "restart_service"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    INCREASE_CAPACITY = "increase_capacity"
    CIRCUIT_BREAKER_OPEN = "circuit_breaker_open"
    NOTIFY_TEAM = "notify_team"
    ESCALATE_INCIDENT = "escalate_incident"
    NO_ACTION = "no_action"


class RiskLevel(str, Enum):
    """Risk levels for actions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentMessage(BaseModel):
    """Message between agents."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    sender_agent: AgentType
    recipient_agent: Optional[AgentType] = None  # None for broadcast
    message_type: str
    payload: Dict[str, Any]
    correlation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(use_enum_values=True)


class Evidence(BaseModel):
    """Evidence supporting an agent's recommendation."""
    
    source: str  # e.g., "cloudwatch_metrics", "application_logs"
    data: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    description: str


class AgentRecommendation(BaseModel):
    """Recommendation from an agent."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: AgentType
    incident_id: str
    action_type: ActionType
    action_id: str  # Unique identifier for grouping similar actions
    
    # Recommendation details
    confidence: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    estimated_impact: str
    reasoning: str
    
    # Supporting evidence
    evidence: List[Evidence] = Field(default_factory=list)
    
    # Action parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Timing and constraints
    urgency: float = Field(ge=0.0, le=1.0)  # How urgent this action is
    time_sensitive: bool = False  # Must be executed within a time window
    execution_window_minutes: Optional[int] = None
    
    # Dependencies and conflicts
    depends_on: List[str] = Field(default_factory=list)  # Other action IDs
    conflicts_with: List[str] = Field(default_factory=list)  # Conflicting actions
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def is_expired(self) -> bool:
        """Check if recommendation has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def add_evidence(self, source: str, data: Dict[str, Any], 
                    confidence: float, description: str) -> None:
        """Add supporting evidence to the recommendation."""
        evidence = Evidence(
            source=source,
            data=data,
            confidence=confidence,
            description=description
        )
        self.evidence.append(evidence)
    
    def calculate_weighted_confidence(self) -> float:
        """Calculate confidence weighted by evidence quality."""
        if not self.evidence:
            return self.confidence
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for evidence in self.evidence:
            weight = evidence.confidence
            total_weight += weight
            weighted_sum += self.confidence * weight
        
        if total_weight == 0:
            return self.confidence
        
        return min(1.0, weighted_sum / total_weight)
    
    model_config = ConfigDict(use_enum_values=True)


class ConsensusDecision(BaseModel):
    """Final decision from consensus process."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    selected_action: str
    action_type: str
    final_confidence: float = Field(ge=0.0, le=1.0)
    
    # Consensus process
    participating_agents: List[str] = Field(default_factory=list)
    agent_recommendations: List[AgentRecommendation] = Field(default_factory=list)
    consensus_method: str = "weighted_voting"
    
    # Conflict resolution
    conflicts_detected: bool = False
    conflict_resolution_method: Optional[str] = None
    minority_opinions: List[str] = Field(default_factory=list)
    
    # Decision metadata
    decision_time: datetime = Field(default_factory=datetime.utcnow)
    processing_duration_ms: Optional[int] = None
    requires_human_approval: bool = False
    approval_threshold: float = 0.7
    
    # Audit trail
    decision_rationale: str = ""
    risk_assessment: str = ""
    fallback_actions: List[str] = Field(default_factory=list)
    
    def add_recommendation(self, recommendation: AgentRecommendation) -> None:
        """Add an agent recommendation to the consensus process."""
        self.agent_recommendations.append(recommendation)
        agent_name = recommendation.agent_name if isinstance(recommendation.agent_name, str) else recommendation.agent_name.value
        if agent_name not in self.participating_agents:
            self.participating_agents.append(agent_name)
    
    def requires_escalation(self) -> bool:
        """Check if decision requires human escalation."""
        return (
            self.final_confidence < self.approval_threshold or
            self.requires_human_approval or
            self.conflicts_detected
        )
    
    model_config = ConfigDict(use_enum_values=True)


class AgentPerformanceMetrics(BaseModel):
    """Performance metrics for agent evaluation."""
    
    agent_name: str
    agent_type: AgentType
    
    # Performance counters
    total_incidents_processed: int = 0
    successful_recommendations: int = 0
    failed_recommendations: int = 0
    timeout_count: int = 0
    
    # Timing metrics
    average_processing_time_ms: float = 0.0
    min_processing_time_ms: float = 0.0
    max_processing_time_ms: float = 0.0
    
    # Quality metrics
    average_confidence: float = 0.0
    accuracy_rate: float = 0.0  # Based on post-incident validation
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0
    
    # Learning metrics
    improvement_rate: float = 0.0  # Month-over-month improvement
    knowledge_base_contributions: int = 0
    pattern_discoveries: int = 0
    
    # Resource utilization
    memory_usage_mb: float = 0.0
    cpu_utilization_percent: float = 0.0
    api_calls_per_incident: float = 0.0
    
    # Time period
    metrics_start_date: datetime = Field(default_factory=datetime.utcnow)
    metrics_end_date: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_success_rate(self) -> float:
        """Calculate overall success rate."""
        total = self.successful_recommendations + self.failed_recommendations
        if total == 0:
            return 0.0
        return self.successful_recommendations / total
    
    def update_timing_metrics(self, processing_time_ms: int) -> None:
        """Update timing metrics with new processing time."""
        if self.total_incidents_processed == 0:
            self.min_processing_time_ms = processing_time_ms
            self.max_processing_time_ms = processing_time_ms
            self.average_processing_time_ms = processing_time_ms
        else:
            self.min_processing_time_ms = min(self.min_processing_time_ms, processing_time_ms)
            self.max_processing_time_ms = max(self.max_processing_time_ms, processing_time_ms)
            
            # Update running average
            total_time = self.average_processing_time_ms * self.total_incidents_processed
            total_time += processing_time_ms
            self.average_processing_time_ms = total_time / (self.total_incidents_processed + 1)
        
        self.last_updated = datetime.utcnow()


class HumanEscalation(BaseModel):
    """Human escalation request when agents cannot reach consensus."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    incident_id: str
    
    # Escalation reason
    reason: str
    escalation_type: str = "consensus_failure"  # consensus_failure, low_confidence, high_risk
    
    # Context
    conflicting_recommendations: List[AgentRecommendation] = Field(default_factory=list)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    
    # Requirements
    required_approval_level: str  # e.g., "senior_sre", "engineering_manager"
    
    # Escalation details
    urgency: float = Field(ge=0.0, le=1.0)
    business_justification: str = ""
    risk_assessment: str = ""
    
    # Timing
    escalated_at: datetime = Field(default_factory=datetime.utcnow)
    response_required_by: Optional[datetime] = None
    
    # Response tracking
    assigned_to: Optional[str] = None
    responded_at: Optional[datetime] = None
    approved: Optional[bool] = None
    response_notes: Optional[str] = None