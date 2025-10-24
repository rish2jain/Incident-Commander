"""Shared Pydantic schemas for incident explainability."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field


class TimelineEventSchema(BaseModel):
    timestamp: datetime
    event: str
    description: str
    phase: Optional[str] = None
    agent: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimelineSummarySchema(BaseModel):
    total_events: int
    events_by_type: Dict[str, int]
    phase_transitions: List[Dict[str, Any]] = Field(default_factory=list)


class IncidentTimelineResponse(BaseModel):
    incident_id: str
    timeline: List[TimelineEventSchema]
    summary: TimelineSummarySchema
    processing_duration_seconds: float
    current_phase: Optional[str] = None
    filters: Dict[str, Optional[str]] = Field(default_factory=dict)


class RationaleSummary(BaseModel):
    headline: str
    confidence: float
    requires_human_approval: bool
    rationale_points: List[str] = Field(default_factory=list)
    risk_assessment: str = ""
    fallback_plan: List[str] = Field(default_factory=list)


class ConfidenceProfile(BaseModel):
    status: str
    selected_action: Optional[str] = None
    final_confidence: Optional[float] = None
    confidence_range: Dict[str, float] = Field(default_factory=dict)
    participating_agents: List[str] = Field(default_factory=list)
    requires_escalation: bool = False


class CounterfactualOption(BaseModel):
    alternative_action: str
    supporting_agents: List[str]
    average_confidence: float
    confidence_gap: float
    risk_level: str
    recommended_usage: str
    key_considerations: List[str] = Field(default_factory=list)


class ExplainabilityPackageSchema(BaseModel):
    incident_id: str
    rationale_summary: RationaleSummary
    confidence_profile: ConfidenceProfile
    counterfactuals: List[CounterfactualOption]
    timeline: List[TimelineEventSchema]
    ledger_summary: TimelineSummarySchema
    last_updated: datetime
    consensus_ready: bool = False
