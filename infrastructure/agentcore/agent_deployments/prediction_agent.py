"""AgentCore packaging spec for the prediction agent."""

from __future__ import annotations

from .base import AgentCorePackageSpec


PREDICTION_AGENT_SPEC = AgentCorePackageSpec(
    name="incident-prediction",
    entrypoint="src.langgraph_orchestrator.agents.prediction_node:PredictionNode",
    description="Forecasts cost and duration impacts for ongoing incidents",
    requirements=[
        "pydantic>=2.5.0",
        "langgraph>=0.0.40",
    ],
    memory_mb=768,
    timeout_seconds=150,
    environment={
        "AGENT_ROLE": "prediction",
        "RUNTIME_MODE": "agentcore",
    },
    tags={"phase": "1", "workstream": "LangGraphMigration"},
)

__all__ = ["PREDICTION_AGENT_SPEC"]

