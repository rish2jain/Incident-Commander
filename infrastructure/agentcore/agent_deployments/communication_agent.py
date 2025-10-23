"""AgentCore packaging spec for the communication agent."""

from __future__ import annotations

from .base import AgentCorePackageSpec


COMMUNICATION_AGENT_SPEC = AgentCorePackageSpec(
    name="incident-communication",
    entrypoint="src.langgraph_orchestrator.agents.communication_node:CommunicationNode",
    description="Generates stakeholder notifications and incident summaries",
    requirements=[
        "boto3>=1.34.0",
        "pydantic>=2.5.0",
        "langgraph>=1.0.0",
    ],
    memory_mb=512,
    timeout_seconds=90,
    environment={
        "AGENT_ROLE": "communication",
        "RUNTIME_MODE": "agentcore",
    },
    tags={"phase": "1", "workstream": "AgentCoreRuntime"},
)

__all__ = ["COMMUNICATION_AGENT_SPEC"]
