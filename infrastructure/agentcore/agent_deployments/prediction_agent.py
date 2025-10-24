"""AgentCore packaging spec for the prediction agent."""

from __future__ import annotations

from .base import AgentCorePackageSpec


PREDICTION_AGENT_SPEC = AgentCorePackageSpec(
    name="incident-prediction",
    entrypoint="src.langgraph_orchestrator.agents.prediction_node:PredictionNode",
    description="Forecasts incident impact and duration using business metrics",
    requirements=[
        "boto3>=1.34.0",
        "pydantic>=2.5.0",
        "langgraph>=1.0.0",
        "numpy>=1.24.0",
    ],
    memory_mb=896,
    timeout_seconds=150,
    environment={
        "AGENT_ROLE": "prediction",
        "RUNTIME_MODE": "agentcore",
    },
    tags={"phase": "1", "workstream": "AgentCoreRuntime"},
)

__all__ = ["PREDICTION_AGENT_SPEC"]
