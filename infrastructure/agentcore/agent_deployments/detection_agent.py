"""AgentCore packaging spec for the detection agent."""

from __future__ import annotations

from .base import AgentCorePackageSpec


DETECTION_AGENT_SPEC = AgentCorePackageSpec(
    name="incident-detection",
    entrypoint="src.langgraph_orchestrator.agents.detection_node:DetectionNode",
    description="Detects incidents and emits workflow bootstrap events via LangGraph",
    requirements=[
        "boto3>=1.34.0",
        "pydantic>=2.5.0",
        "langgraph>=1.0.0",
    ],
    memory_mb=768,
    timeout_seconds=120,
    environment={
        "AGENT_ROLE": "detection",
        "RUNTIME_MODE": "agentcore",
    },
    tags={"phase": "1", "workstream": "LangGraphMigration"},
)

__all__ = ["DETECTION_AGENT_SPEC"]

