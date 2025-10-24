"""Shared state schemas for LangGraph orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field, ConfigDict

from src.models.agent import AgentRecommendation, ConsensusDecision
from src.models.incident import Incident


class StateTimelineEvent(BaseModel):
    """Timeline entry captured during LangGraph execution."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    phase: str
    agent: Optional[str] = None
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def describe(self) -> str:
        """Return a human-readable summary."""
        agent_part = f" ({self.agent})" if self.agent else ""
        return f"[{self.phase}]{agent_part}: {self.message}"


class AgentNodeResultModel(BaseModel):
    """Normalized output from an individual LangGraph node."""

    agent: str
    recommendations: List[AgentRecommendation] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def primary_recommendation(self) -> Optional[AgentRecommendation]:
        """Return the highest-confidence recommendation if present."""
        if not self.recommendations:
            return None
        return max(self.recommendations, key=lambda rec: rec.confidence)


class AgentNodeExecutionResult(BaseModel):
    """Container for LangGraph node execution results."""

    output: AgentNodeResultModel
    timeline_event: Optional[StateTimelineEvent] = None
    context_delta: Dict[str, Any] = Field(default_factory=dict)
    state_overrides: Dict[str, Any] = Field(default_factory=dict)

    def to_state_update(self, key: str, base_state: "IncidentGraphState") -> "IncidentGraphState":
        """Convert execution result into a graph state update."""
        update: IncidentGraphState = {
            key: self.output.model_dump(mode="python"),
        }

        if self.timeline_event:
            timeline = list(base_state.get("timeline", []))
            timeline.append(self.timeline_event.model_dump(mode="python"))
            update["timeline"] = timeline

        if self.context_delta:
            context = dict(base_state.get("context", {}))
            context.update(self.context_delta)
            update["context"] = context

        update.update(self.state_overrides)

        return update


class IncidentStateModel(BaseModel):
    """Authoritative view of incident processing state within LangGraph."""

    incident: Incident
    context: Dict[str, Any] = Field(default_factory=dict)
    detection: Optional[AgentNodeResultModel] = None
    diagnosis: Optional[AgentNodeResultModel] = None
    prediction: Optional[AgentNodeResultModel] = None
    consensus_node: Optional[AgentNodeResultModel] = None
    resolution: Optional[AgentNodeResultModel] = None
    communication: Optional[AgentNodeResultModel] = None
    consensus: Optional[ConsensusDecision] = None
    timeline: List[StateTimelineEvent] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def from_graph_state(cls, state: "IncidentGraphState") -> "IncidentStateModel":
        """Construct model from a raw LangGraph state dictionary."""
        timeline_models = [StateTimelineEvent(**event) for event in state.get("timeline", [])]

        def _get_agent_node(key: str) -> Optional[AgentNodeResultModel]:
            if key not in state:
                return None
            raw = state[key]
            return AgentNodeResultModel(**raw)

        consensus_value: Optional[ConsensusDecision] = None
        if "consensus" in state and state["consensus"] is not None:
            consensus_value = ConsensusDecision(**state["consensus"])

        return cls(
            incident=state["incident"],
            context=state.get("context", {}),
            detection=_get_agent_node("detection"),
            diagnosis=_get_agent_node("diagnosis"),
            prediction=_get_agent_node("prediction"),
            consensus_node=_get_agent_node("consensus_node"),
            resolution=_get_agent_node("resolution"),
            communication=_get_agent_node("communication"),
            consensus=consensus_value,
            timeline=timeline_models,
        )

    def to_graph_state(self) -> "IncidentGraphState":
        """Convert model back into a graph state dictionary."""
        state: IncidentGraphState = {
            "incident": self.incident,
            "context": self.context,
            "timeline": [event.model_dump(mode="python") for event in self.timeline],
        }

        for key in ("detection", "diagnosis", "prediction", "resolution", "communication"):
            value = getattr(self, key)
            if value:
                state[key] = value.model_dump(mode="python")

        if self.consensus_node:
            state["consensus_node"] = self.consensus_node.model_dump(mode="python")

        if self.consensus:
            state["consensus"] = self.consensus.model_dump(mode="python")

        return state


class IncidentGraphState(TypedDict, total=False):
    """Typed representation of the LangGraph shared state."""

    incident: Incident
    context: Dict[str, Any]
    detection: Dict[str, Any]
    diagnosis: Dict[str, Any]
    prediction: Dict[str, Any]
    consensus_node: Dict[str, Any]
    resolution: Dict[str, Any]
    communication: Dict[str, Any]
    consensus: Dict[str, Any]
    timeline: List[Dict[str, Any]]
