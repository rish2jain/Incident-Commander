"""Shared helpers for AWS Bedrock AgentCore deployment packaging."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass(slots=True)
class AgentCorePackageSpec:
    """Declarative AgentCore package specification."""

    name: str
    entrypoint: str
    description: str
    requirements: List[str] = field(default_factory=list)
    memory_mb: int = 512
    timeout_seconds: int = 60
    environment: Dict[str, str] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)


class AgentCoreDeployer:
    """Utility for generating AgentCore deployment manifests."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self._output_dir = output_dir or Path("artifacts/agentcore").absolute()
        self._output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def output_dir(self) -> Path:
        return self._output_dir

    def create_manifest(self, spec: AgentCorePackageSpec) -> Dict[str, object]:
        """Produce a structured manifest dictionary for templates/IaC."""
        return {
            "name": spec.name,
            "entrypoint": spec.entrypoint,
            "description": spec.description,
            "resources": {
                "memory": spec.memory_mb,
                "timeout_seconds": spec.timeout_seconds,
            },
            "requirements": sorted(set(spec.requirements)),
            "environment": dict(spec.environment),
            "tags": dict(spec.tags),
        }

    def summarize(self, spec: AgentCorePackageSpec) -> str:
        """Return a human readable summary for the spec."""
        manifest = self.create_manifest(spec)
        return (
            f"AgentCore package '{manifest['name']}' → {manifest['entrypoint']}\n"
            f"  Memory: {manifest['resources']['memory']} MB | "
            f"Timeout: {manifest['resources']['timeout_seconds']}s | "
            f"Requirements: {', '.join(manifest['requirements']) or 'builtin'}"
        )

    def write_manifest(self, spec: AgentCorePackageSpec) -> Path:
        target = self._output_dir / f"{spec.name}_manifest.json"
        import json

        with target.open("w", encoding="utf-8") as f:
            json.dump(self.create_manifest(spec), f, indent=2, sort_keys=True)
        return target


def load_all_specs(specs: Iterable[AgentCorePackageSpec]) -> List[Dict[str, object]]:
    """Helper for scripts to convert specs into manifest dictionaries."""
    deployer = AgentCoreDeployer()
    return [deployer.create_manifest(spec) for spec in specs]

