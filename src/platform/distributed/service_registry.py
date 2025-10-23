"""Service registry scaffolding for distributed Incident Commander services."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass(slots=True)
class ServiceDescriptor:
    """Describes a microservice deployed on the distributed LangGraph platform."""

    name: str
    version: str
    description: str
    owner: str
    api_endpoint: str
    dependencies: List[str] = field(default_factory=list)
    domain: str = "incident-response"


class ServiceRegistry:
    """Lightweight registry for distributed services."""

    def __init__(self) -> None:
        import threading
        self._services: Dict[str, ServiceDescriptor] = {}
        self._lock = threading.RLock()

    def register(self, descriptor: ServiceDescriptor) -> None:
        with self._lock:
            if descriptor.name in self._services:
                existing = self._services[descriptor.name]
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    "Service '%s' already registered. Overwriting existing entry.",
                    descriptor.name,
                    extra={
                        "existing_version": getattr(existing, "version", "unknown"),
                        "new_version": getattr(descriptor, "version", "unknown"),
                        "existing_endpoint": existing.api_endpoint,
                        "new_endpoint": descriptor.api_endpoint,
                    }
                )
            self._services[descriptor.name] = descriptor

    def get(self, name: str) -> Optional[ServiceDescriptor]:
        with self._lock:
            return self._services.get(name)

    def list(self) -> List[ServiceDescriptor]:
        with self._lock:
            return sorted(self._services.values(), key=lambda svc: svc.name)

    def adjacency_map(self) -> Dict[str, List[str]]:
        with self._lock:
            return {
                name: list(descriptor.dependencies)
                for name, descriptor in self._services.items()
            }

    def register_all(self, descriptors: Iterable[ServiceDescriptor]) -> None:
        for descriptor in descriptors:
            self.register(descriptor)

