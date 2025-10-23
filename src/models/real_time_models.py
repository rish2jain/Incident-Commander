"""
Real-time Data Models for WebSocket Updates

Models for streaming agent states, business metrics, and system health
to Dashboard 3 (Production Operations) via WebSocket.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class AgentState(str, Enum):
    """Real-time agent processing states."""
    IDLE = "idle"
    INITIALIZING = "initializing"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"
    TIMEOUT = "timeout"


class IncidentPhase(str, Enum):
    """Incident processing phases."""
    DETECTION = "detection"
    DIAGNOSIS = "diagnosis"
    PREDICTION = "prediction"
    RESOLUTION = "resolution"
    VERIFICATION = "verification"
    COMPLETE = "complete"


class AgentUpdate(BaseModel):
    """
    Real-time agent status update for WebSocket streaming.

    Sent whenever an agent changes state or makes progress.
    """

    # Identification
    update_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str
    agent_type: str  # detection, diagnosis, prediction, resolution
    incident_id: str

    # State information
    state: AgentState
    phase: IncidentPhase
    progress: float = Field(ge=0.0, le=1.0, description="Processing progress 0-1")

    # Processing details
    current_task: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    processing_time_ms: Optional[int] = None

    # Evidence and reasoning
    evidence_count: int = 0
    key_finding: Optional[str] = None

    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"use_enum_values": True}


class BusinessMetrics(BaseModel):
    """
    Real business metrics calculated from actual system performance.

    Streamed to Dashboard 3 when incidents complete or periodically.
    """

    # Identification
    metrics_id: str = Field(default_factory=lambda: str(uuid4()))
    calculation_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Core metrics with confidence intervals
    mttr_seconds: float = Field(ge=0.0, description="Mean Time To Resolution")
    mttr_confidence_lower: float = Field(ge=0.0)
    mttr_confidence_upper: float = Field(ge=0.0)

    # Incident tracking
    incidents_handled: int = Field(ge=0)
    incidents_prevented: int = Field(ge=0)
    incidents_in_progress: int = Field(ge=0)

    # Financial impact
    cost_savings_usd: float = Field(ge=0.0)
    cost_savings_confidence_lower: float = Field(ge=0.0)
    cost_savings_confidence_upper: float = Field(ge=0.0)

    # Performance
    efficiency_score: float = Field(ge=0.0, le=1.0)
    success_rate: float = Field(ge=0.0, le=1.0)

    # Trends (vs previous period)
    mttr_trend: Optional[float] = None  # Percentage change
    efficiency_trend: Optional[float] = None

    # Data quality
    sample_size: int = Field(ge=0, description="Number of incidents in calculation")
    data_quality_score: float = Field(ge=0.0, le=1.0, default=1.0)

    # Attribution
    calculation_method: str = "real_system_data"
    confidence_level: float = Field(ge=0.0, le=1.0, default=0.95)


class SystemHealthMetrics(BaseModel):
    """
    Real-time system health indicators.

    Includes agent performance, AWS service health, and processing capacity.
    """

    # Identification
    health_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Agent health
    active_agents: int = Field(ge=0)
    healthy_agents: int = Field(ge=0)
    degraded_agents: int = Field(ge=0)
    error_agents: int = Field(ge=0)

    # Processing capacity
    current_incidents: int = Field(ge=0)
    queue_depth: int = Field(ge=0)
    processing_capacity: float = Field(ge=0.0, le=1.0, description="% of max capacity")

    # Performance
    average_latency_ms: float = Field(ge=0.0)
    p95_latency_ms: float = Field(ge=0.0)
    p99_latency_ms: float = Field(ge=0.0)

    # WebSocket health
    websocket_connections: int = Field(ge=0)
    websocket_latency_ms: float = Field(ge=0.0)
    messages_per_second: float = Field(ge=0.0)

    # AWS service health (if available)
    aws_services_healthy: Optional[int] = None
    aws_services_degraded: Optional[int] = None
    aws_service_details: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class AWSServiceMetrics(BaseModel):
    """
    AWS AI service usage and performance metrics.

    Tracks individual service usage for Dashboard 3 visualization.
    """

    # Identification
    service_name: str  # bedrock, q_business, nova, etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Usage metrics
    total_calls: int = Field(ge=0)
    successful_calls: int = Field(ge=0)
    failed_calls: int = Field(ge=0)

    # Performance
    average_latency_ms: float = Field(ge=0.0)
    p95_latency_ms: float = Field(ge=0.0)
    tokens_processed: int = Field(ge=0)

    # Cost tracking
    estimated_cost_usd: float = Field(ge=0.0)
    cost_per_call: float = Field(ge=0.0)

    # Health
    health_status: str = Field(default="healthy")  # healthy, degraded, error
    error_rate: float = Field(ge=0.0, le=1.0)

    # Model-specific (for Bedrock)
    model_id: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IncidentFlowUpdate(BaseModel):
    """
    Incident flow visualization update.

    Tracks incident progression through phases for Dashboard 3 flow chart.
    """

    # Identification
    incident_id: str
    flow_update_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Flow state
    current_phase: IncidentPhase
    completed_phases: List[IncidentPhase] = Field(default_factory=list)
    next_phase: Optional[IncidentPhase] = None

    # Progress
    overall_progress: float = Field(ge=0.0, le=1.0)
    phase_progress: float = Field(ge=0.0, le=1.0)
    estimated_completion_seconds: Optional[int] = None

    # Agent participation
    active_agents: List[str] = Field(default_factory=list)
    completed_agents: List[str] = Field(default_factory=list)

    # State changes
    state_changes: List[Dict[str, Any]] = Field(default_factory=list)

    # Summary
    incident_summary: Optional[str] = None
    severity: Optional[str] = None

    model_config = {"use_enum_values": True}


class WebSocketEvent(BaseModel):
    """
    Base model for all WebSocket events sent to Dashboard 3.

    Provides consistent structure for all real-time updates.
    """

    # Event metadata
    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str  # agent_update, business_metrics, system_health, etc.
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Target dashboard (for filtering)
    target_dashboard: str = "ops"  # Only 'ops' receives real-time updates

    # Event data (polymorphic - can be any of the above models)
    data: Dict[str, Any]

    # Priority for message batching
    priority: int = Field(ge=1, le=3, default=1)  # 1=low, 2=medium, 3=high

    # Versioning for backward compatibility
    schema_version: str = "1.0"


class ErrorNotification(BaseModel):
    """
    Error notification for real-time error reporting to Dashboard 3.
    """

    # Identification
    error_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Error details
    error_type: str
    error_message: str
    severity: str  # low, medium, high, critical

    # Context
    incident_id: Optional[str] = None
    agent_name: Optional[str] = None
    phase: Optional[IncidentPhase] = None

    # Recovery
    recovery_action: Optional[str] = None
    retry_count: int = 0
    is_recoverable: bool = True

    # Stack trace (optional, for debugging)
    stack_trace: Optional[str] = None

    model_config = {"use_enum_values": True}


# Type aliases for clarity
AgentUpdateEvent = WebSocketEvent
BusinessMetricsEvent = WebSocketEvent
SystemHealthEvent = WebSocketEvent
IncidentFlowEvent = WebSocketEvent
ErrorNotificationEvent = WebSocketEvent
