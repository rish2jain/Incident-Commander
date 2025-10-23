"""CLI helper to generate Bedrock AgentCore deployment manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List

from infrastructure.agentcore.agent_deployments import (
    AgentCoreDeployer,
    AgentCorePackageSpec,
    COMMUNICATION_AGENT_SPEC,
    DETECTION_AGENT_SPEC,
    DIAGNOSIS_AGENT_SPEC,
    PREDICTION_AGENT_SPEC,
    RESOLUTION_AGENT_SPEC,
)


ALL_SPECS: List[AgentCorePackageSpec] = [
    DETECTION_AGENT_SPEC,
    DIAGNOSIS_AGENT_SPEC,
    PREDICTION_AGENT_SPEC,
    RESOLUTION_AGENT_SPEC,
    COMMUNICATION_AGENT_SPEC,
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/agentcore"),
        help="Directory where manifest files should be written (default: artifacts/agentcore)",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Print human readable summaries",
    )
    parser.add_argument(
        "--write-manifests",
        action="store_true",
        help="Write JSON manifests to disk",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit combined JSON manifest to stdout",
    )
    return parser.parse_args()


def _emit_plan(deployer: AgentCoreDeployer, specs: Iterable[AgentCorePackageSpec]) -> None:
    for spec in specs:
        print(deployer.summarize(spec))


def _write_manifests(deployer: AgentCoreDeployer, specs: Iterable[AgentCorePackageSpec]) -> None:
    for spec in specs:
        path = deployer.write_manifest(spec)
        print(f"Wrote {path}")


def _emit_json(deployer: AgentCoreDeployer, specs: Iterable[AgentCorePackageSpec]) -> None:
    manifests = [deployer.create_manifest(spec) for spec in specs]
    print(json.dumps(manifests, indent=2, sort_keys=True))


def main() -> None:
    args = _parse_args()
    deployer = AgentCoreDeployer(output_dir=args.output_dir)

    if args.plan:
        _emit_plan(deployer, ALL_SPECS)

    if args.write_manifests:
        _write_manifests(deployer, ALL_SPECS)

    if args.json:
        _emit_json(deployer, ALL_SPECS)

    if not any([args.plan, args.write_manifests, args.json]):
        _emit_plan(deployer, ALL_SPECS)


if __name__ == "__main__":
    main()

