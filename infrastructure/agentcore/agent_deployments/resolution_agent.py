"""AgentCore packaging spec for the resolution agent."""

from __future__ import annotations

from .base import AgentCorePackageSpec


RESOLUTION_AGENT_SPEC = AgentCorePackageSpec(
    name="incident-resolution",
    entrypoint="src.langgraph_orchestrator.agents.resolution_node:ResolutionNode",
    description="Transforms consensus into executable remediation actions",
    requirements=[
        "pydantic>=2.5.0",
        "langgraph>=0.0.40",
    ],
    memory_mb=1024,
    timeout_seconds=240,
    environment={
        "AGENT_ROLE": "resolution",
        "RUNTIME_MODE": "agentcore",
    },
    tags={"phase": "1", "workstream": "AgentCoreRuntime"},
)

__all__ = ["RESOLUTION_AGENT_SPEC"]

