"""Validate and summarize AgentCore Memory/Identity configuration files."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except Exception:  # noqa: BLE001 - runtime optionality
    yaml = None  # type: ignore


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--memory-config",
        type=Path,
        default=Path("infrastructure/agentcore/memory_config.yaml"),
        help="Path to the memory configuration YAML",
    )
    parser.add_argument(
        "--identity-config",
        type=Path,
        default=Path("infrastructure/agentcore/identity_config.yaml"),
        help="Path to the identity configuration YAML",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a human-readable summary after validation",
    )
    return parser.parse_args()


def _load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise RuntimeError("pyyaml is required to parse configuration files")

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)  # type: ignore[arg-type]


def _validate_memory(config: Dict[str, Any]) -> None:
    if "collections" not in config:
        raise ValueError("memory_config missing 'collections'")
    if not isinstance(config["collections"], dict):
        raise TypeError("memory_config collections must be a mapping")


def _validate_identity(config: Dict[str, Any]) -> None:
    if "roles" not in config:
        raise ValueError("identity_config missing 'roles'")
    if not isinstance(config["roles"], dict):
        raise TypeError("identity_config roles must be a mapping")


def _print_summary(memory: Dict[str, Any], identity: Dict[str, Any]) -> None:
    print("Memory Collections:")
    for name, payload in memory.get("collections", {}).items():
        retention = payload.get("retention_days", "n/a")
        provider = payload.get("vector_store", {}).get("provider", "n/a")
        print(f"  - {name}: retention={retention} provider={provider}")

    print("\nIdentity Roles:")
    for name, payload in identity.get("roles", {}).items():
        policies = ", ".join(payload.get("policies", []))
        print(f"  - {name}: {policies}")


def main() -> None:
    args = _parse_args()
    memory = _load_yaml(args.memory_config)
    identity = _load_yaml(args.identity_config)
    _validate_memory(memory)
    _validate_identity(identity)

    if args.summary:
        _print_summary(memory, identity)


if __name__ == "__main__":
    main()

