"""Distributed platform scaffolding for Phase 2 modernization."""

from .service_registry import ServiceRegistry, ServiceDescriptor
from .event_router import EventRouter, EventDefinition

__all__ = [
    "ServiceRegistry",
    "ServiceDescriptor",
    "EventRouter",
    "EventDefinition",
]

