"""EventBridge routing scaffolding for distributed architecture."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class EventDefinition:
    """Metadata for EventBridge rules."""

    name: str
    source: str
    detail_type: str
    target_service: str
    schema_ref: str
    description: str = ""


class EventRouter:
    """In-memory representation of EventBridge routing rules."""

    def __init__(self, event_bus_name: str = "incident-commander-bus") -> None:
        self._event_bus_name = event_bus_name
        self._events: Dict[str, EventDefinition] = {}

    @property
    def event_bus_name(self) -> str:
        return self._event_bus_name

    def add_event(self, definition: EventDefinition) -> None:
        self._events[definition.name] = definition

    def list_events(self) -> List[EventDefinition]:
        return sorted(self._events.values(), key=lambda event: event.name)

    def routes_for_service(self, service_name: str) -> List[EventDefinition]:
        return [event for event in self._events.values() if event.target_service == service_name]

    def to_eventbridge_rules(self) -> List[Dict[str, object]]:
        """Serialize router into EventBridge-compatible rule specs."""
        rules: List[Dict[str, object]] = []
        for event in self.list_events():
            rules.append(
                {
                    "Name": event.name,
                    "EventBusName": self._event_bus_name,
                    "EventPattern": {
                        "source": [event.source],
                        "detail-type": [event.detail_type],
                    },
                    "Targets": [
                        {
                            "Id": f"target-{event.target_service}",
                            "Arn": f"arn:aws:events:::target/{event.target_service}",
                            "InputPath": "$.detail",
                        }
                    ],
                    "Description": event.description,
                }
            )
        return rules

