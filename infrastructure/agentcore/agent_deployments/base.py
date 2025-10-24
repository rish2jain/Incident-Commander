"""Base models and utilities for AgentCore deployments."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class AgentCorePackageSpec:
    """Specification for deploying an agent to AWS Bedrock AgentCore Runtime."""

    name: str
    entrypoint: str
    description: str
    requirements: List[str]
    memory_mb: int = 512
    timeout_seconds: int = 120
    environment: Dict[str, str] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)


class AgentCoreDeployer:
    """Utility for generating AgentCore deployment manifests."""

    def __init__(self, output_dir: Path = Path("artifacts/agentcore")) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_manifest(self, spec: AgentCorePackageSpec) -> Dict[str, Any]:
        """Create a deployment manifest from a package spec."""
        return {
            "name": spec.name,
            "runtime": "bedrock-agentcore",
            "handler": spec.entrypoint,
            "description": spec.description,
            "configuration": {
                "memory": spec.memory_mb,
                "timeout": spec.timeout_seconds,
                "environment": spec.environment,
            },
            "dependencies": spec.requirements,
            "tags": spec.tags,
        }

    def write_manifest(self, spec: AgentCorePackageSpec) -> Path:
        """Write a deployment manifest to disk."""
        manifest = self.create_manifest(spec)
        path = self.output_dir / f"{spec.name}-manifest.json"
        with open(path, "w") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
        return path

    def summarize(self, spec: AgentCorePackageSpec) -> str:
        """Generate a human-readable summary of a package spec."""
        lines = [
            f"Agent: {spec.name}",
            f"  Entrypoint: {spec.entrypoint}",
            f"  Memory: {spec.memory_mb}MB",
            f"  Timeout: {spec.timeout_seconds}s",
            f"  Description: {spec.description}",
            f"  Requirements: {', '.join(spec.requirements)}",
        ]
        if spec.environment:
            lines.append(f"  Environment: {spec.environment}")
        if spec.tags:
            lines.append(f"  Tags: {spec.tags}")
        return "\n".join(lines)


__all__ = ["AgentCorePackageSpec", "AgentCoreDeployer"]
