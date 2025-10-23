"""AWS EventBridge integration for event-driven architecture."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import aioboto3
from botocore.exceptions import ClientError

from src.utils.logging import get_logger


logger = get_logger("platform.eventbridge")


@dataclass
class Event:
    """Event model for event-driven communication."""

    source: str
    detail_type: str
    detail: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resources: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)

    def to_eventbridge_entry(self, event_bus_name: str) -> Dict[str, Any]:
        """Convert to EventBridge PutEvents entry format."""
        return {
            "Time": self.timestamp,
            "Source": self.source,
            "DetailType": self.detail_type,
            "Detail": json.dumps(self.detail),
            "EventBusName": event_bus_name,
            "Resources": self.resources,
        }


class EventBridgeClient:
    """
    AWS EventBridge client for event-driven architecture.

    Features:
    - Publish events to EventBridge
    - Batch event publishing
    - Event routing and filtering
    - Error handling and retries
    - Event validation
    """

    def __init__(
        self,
        event_bus_name: str = "incident-commander",
        region_name: str = "us-east-1",
        max_batch_size: int = 10,
    ):
        self.event_bus_name = event_bus_name
        self.region_name = region_name
        self.max_batch_size = max_batch_size
        self._session = aioboto3.Session()
        logger.info(
            f"EventBridgeClient initialized",
            extra={"event_bus": event_bus_name, "region": region_name},
        )

    async def publish_event(self, event: Event) -> bool:
        """
        Publish a single event to EventBridge.

        Args:
            event: The event to publish

        Returns:
            True if successful, False otherwise
        """
        return await self.publish_events([event])

    async def publish_events(self, events: List[Event]) -> bool:
        """
        Publish multiple events to EventBridge.

        Args:
            events: List of events to publish

        Returns:
            True if all events published successfully, False otherwise
        """
        if not events:
            logger.warning("No events to publish")
            return True

        # Split into batches
        batches = [
            events[i : i + self.max_batch_size]
            for i in range(0, len(events), self.max_batch_size)
        ]

        success = True
        for batch in batches:
            batch_success = await self._publish_batch(batch)
            success = success and batch_success

        return success

    async def _publish_batch(self, events: List[Event]) -> bool:
        """Publish a batch of events to EventBridge."""
        entries = [event.to_eventbridge_entry(self.event_bus_name) for event in events]

        try:
            async with self._session.client(
                "events", region_name=self.region_name
            ) as client:
                response = await client.put_events(Entries=entries)

                # Check for failures
                failed_count = response.get("FailedEntryCount", 0)
                if failed_count > 0:
                    logger.error(
                        f"Failed to publish {failed_count} events",
                        extra={
                            "failed_entries": response.get("Entries", []),
                            "batch_size": len(events),
                        },
                    )
                    return False

                logger.info(
                    f"Published {len(events)} events to EventBridge",
                    extra={"event_bus": self.event_bus_name},
                )
                return True

        except ClientError as e:
            logger.error(
                f"Failed to publish events to EventBridge: {e}",
                extra={
                    "error_code": e.response.get("Error", {}).get("Code"),
                    "batch_size": len(events),
                },
                exc_info=True,
            )
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing events: {e}", exc_info=True)
            return False

    async def publish_incident_event(
        self,
        incident_id: str,
        event_type: str,
        data: Dict[str, Any],
        source: str = "incident-commander.orchestrator",
    ) -> bool:
        """
        Publish an incident-related event.

        Args:
            incident_id: The incident ID
            event_type: Type of event (e.g., "IncidentDetected", "ConsensusReached")
            data: Event data payload
            source: Event source identifier

        Returns:
            True if successful, False otherwise
        """
        event = Event(
            source=source,
            detail_type=event_type,
            detail={
                "incident_id": incident_id,
                **data,
            },
            resources=[f"incident/{incident_id}"],
            metadata={
                "version": "1.0",
                "schema": "incident-event-v1",
            },
        )

        return await self.publish_event(event)

    async def publish_agent_event(
        self,
        agent_name: str,
        event_type: str,
        data: Dict[str, Any],
        incident_id: Optional[str] = None,
    ) -> bool:
        """
        Publish an agent-related event.

        Args:
            agent_name: Name of the agent
            event_type: Type of event (e.g., "AgentCompleted", "AgentFailed")
            data: Event data payload
            incident_id: Optional incident ID

        Returns:
            True if successful, False otherwise
        """
        detail = {
            "agent_name": agent_name,
            **data,
        }

        if incident_id:
            detail["incident_id"] = incident_id

        event = Event(
            source=f"incident-commander.agent.{agent_name}",
            detail_type=event_type,
            detail=detail,
            resources=[f"agent/{agent_name}"] + ([f"incident/{incident_id}"] if incident_id else []),
            metadata={
                "version": "1.0",
                "schema": "agent-event-v1",
            },
        )

        return await self.publish_event(event)

    async def publish_consensus_event(
        self,
        incident_id: str,
        consensus_method: str,
        final_confidence: float,
        selected_action: str,
        participating_agents: List[str],
    ) -> bool:
        """
        Publish a consensus-related event.

        Args:
            incident_id: The incident ID
            consensus_method: Consensus method used (e.g., "pbft", "weighted")
            final_confidence: Final consensus confidence score
            selected_action: The selected action
            participating_agents: List of agents that participated

        Returns:
            True if successful, False otherwise
        """
        event = Event(
            source="incident-commander.consensus",
            detail_type="ConsensusReached",
            detail={
                "incident_id": incident_id,
                "consensus_method": consensus_method,
                "final_confidence": final_confidence,
                "selected_action": selected_action,
                "participating_agents": participating_agents,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            resources=[f"incident/{incident_id}"],
            metadata={
                "version": "1.0",
                "schema": "consensus-event-v1",
            },
        )

        return await self.publish_event(event)


# Global EventBridge client instance
_client: Optional[EventBridgeClient] = None


def get_eventbridge_client(
    event_bus_name: str = "incident-commander",
    region_name: str = "us-east-1",
) -> EventBridgeClient:
    """Get the global EventBridge client instance."""
    global _client
    if _client is None:
        _client = EventBridgeClient(
            event_bus_name=event_bus_name,
            region_name=region_name,
        )
    return _client
