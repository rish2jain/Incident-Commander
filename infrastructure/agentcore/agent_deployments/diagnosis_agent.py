"""AgentCore packaging spec for the diagnosis agent."""

from __future__ import annotations

from .base import AgentCorePackageSpec


DIAGNOSIS_AGENT_SPEC = AgentCorePackageSpec(
    name="incident-diagnosis",
    entrypoint="src.langgraph_orchestrator.agents.diagnosis_node:DiagnosisNode",
    description="Performs root-cause analysis using LangGraph diagnosis node",
    requirements=[
        "pydantic>=2.5.0",
        "langgraph>=1.0.0",
    ],
    memory_mb=896,
    timeout_seconds=180,
    environment={
        "AGENT_ROLE": "diagnosis",
        "RUNTIME_MODE": "agentcore",
    },
    tags={"phase": "1", "workstream": "AgentCoreRuntime"},
)

__all__ = ["DIAGNOSIS_AGENT_SPEC"]

