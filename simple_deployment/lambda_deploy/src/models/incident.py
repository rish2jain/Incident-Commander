"""
Incident data structures and models.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, ClassVar
from uuid import uuid4
import hashlib
import json

from pydantic import BaseModel, Field, field_validator, ConfigDict


class IncidentSeverity(str, Enum):
    """Incident severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentStatus(str, Enum):
    """Incident status values."""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ServiceTier(str, Enum):
    """Service tier classifications for business impact calculation."""
    TIER_1 = "tier_1"  # Critical customer-facing services
    TIER_2 = "tier_2"  # Important internal services
    TIER_3 = "tier_3"  # Non-critical services


class BusinessImpact(BaseModel):
    """Business impact assessment for incidents."""
    
    service_tier: ServiceTier
    affected_users: int = 0
    revenue_impact_per_minute: float = 0.0
    sla_breach_risk: float = 0.0  # 0.0 to 1.0
    reputation_impact: float = 0.0  # 0.0 to 1.0
    
    # Predefined cost per minute by service tier
    TIER_COSTS: ClassVar[Dict[ServiceTier, float]] = {
        ServiceTier.TIER_1: 1000.0,  # $1000/min for critical services
        ServiceTier.TIER_2: 500.0,   # $500/min for important services
        ServiceTier.TIER_3: 100.0    # $100/min for non-critical services
    }
    
    def calculate_cost_per_minute(self) -> float:
        """Calculate total cost per minute for this incident."""
        base_cost = self.TIER_COSTS[self.service_tier]
        user_multiplier = min(self.affected_users / 1000, 10.0)  # Cap at 10x
        return base_cost * (1 + user_multiplier) + self.revenue_impact_per_minute
    
    def calculate_total_cost(self, duration_minutes: float) -> float:
        """Calculate total business cost for incident duration."""
        return self.calculate_cost_per_minute() * duration_minutes


class IncidentMetadata(BaseModel):
    """Metadata associated with an incident."""
    
    source_system: str
    alert_ids: List[str] = Field(default_factory=list)
    tags: Dict[str, str] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    parent_incident_id: Optional[str] = None
    related_incident_ids: List[str] = Field(default_factory=list)


class Incident(BaseModel):
    """Core incident model."""
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus = IncidentStatus.DETECTED
    business_impact: BusinessImpact
    metadata: IncidentMetadata
    
    # Timestamps
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Agent processing
    assigned_agents: List[str] = Field(default_factory=list)
    processing_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Audit and integrity
    version: int = 1
    checksum: Optional[str] = None
    
    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v):
        """Sanitize description to prevent injection attacks."""
        import re
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', v)
        return sanitized[:1000]  # Limit length
    
    def calculate_duration_minutes(self) -> float:
        """Calculate incident duration in minutes."""
        if not self.resolved_at:
            end_time = datetime.utcnow()
        else:
            end_time = self.resolved_at
        
        start_time = self.started_at or self.detected_at
        duration = end_time - start_time
        return duration.total_seconds() / 60.0
    
    def calculate_total_cost(self) -> float:
        """Calculate total business cost of this incident."""
        duration = self.calculate_duration_minutes()
        return self.business_impact.calculate_total_cost(duration)
    
    def generate_checksum(self) -> str:
        """Generate cryptographic checksum for integrity verification."""
        # Create deterministic representation
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,  # Already a string due to use_enum_values=True
            "status": self.status,      # Already a string due to use_enum_values=True
            "version": self.version
        }
        
        json_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    def update_checksum(self) -> None:
        """Update the checksum after modifications."""
        self.checksum = self.generate_checksum()
    
    def verify_integrity(self) -> bool:
        """Verify incident data integrity."""
        if not self.checksum:
            return False
        return self.checksum == self.generate_checksum()
    
    model_config = ConfigDict(
        use_enum_values=True,
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )