"""Tests for AgentCore deployment scaffolding."""

from pathlib import Path

from infrastructure.agentcore.agent_deployments import (
    AgentCoreDeployer,
    DETECTION_AGENT_SPEC,
)


def test_agentcore_manifest_contains_expected_fields(tmp_path: Path):
    deployer = AgentCoreDeployer(output_dir=tmp_path)
    manifest = deployer.create_manifest(DETECTION_AGENT_SPEC)

    assert manifest["name"] == "incident-detection"
    assert manifest["entrypoint"].endswith("DetectionNode")
    assert manifest["resources"]["memory"] >= 512
    assert "AGENT_ROLE" in manifest["environment"]


def test_agentcore_configs_exist():
    memory_config = Path("infrastructure/agentcore/memory_config.yaml")
    identity_config = Path("infrastructure/agentcore/identity_config.yaml")

    assert memory_config.exists()
    assert identity_config.exists()

    memory_text = memory_config.read_text(encoding="utf-8")
    identity_text = identity_config.read_text(encoding="utf-8")

    assert "collections" in memory_text
    assert "roles" in identity_text

