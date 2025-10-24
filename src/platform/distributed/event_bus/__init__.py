"""Event-driven communication via AWS EventBridge."""

from src.platform.distributed.event_bus.event_bridge_client import (
    Event,
    EventBridgeClient,
    get_eventbridge_client,
)

__all__ = ["Event", "EventBridgeClient", "get_eventbridge_client"]
