"""AgentCore packaging spec for the resolution agent."""

from __future__ import annotations

from .base import AgentCorePackageSpec


RESOLUTION_AGENT_SPEC = AgentCorePackageSpec(
    name="incident-resolution",
    entrypoint="src.langgraph_orchestrator.agents.resolution_node:ResolutionNode",
    description="Translates consensus decisions into executable resolution actions",
    requirements=[
        "boto3>=1.34.0",
        "pydantic>=2.5.0",
        "langgraph>=1.0.0",
    ],
    memory_mb=768,
    timeout_seconds=180,
    environment={
        "AGENT_ROLE": "resolution",
        "RUNTIME_MODE": "agentcore",
    },
    tags={"phase": "1", "workstream": "AgentCoreRuntime"},
)

__all__ = ["RESOLUTION_AGENT_SPEC"]
