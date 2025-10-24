"""
Event store interface for incident state management.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncIterator
from datetime import datetime

from src.models.incident import Incident


class IncidentEvent:
    """Represents an event in the incident lifecycle."""
    
    def __init__(self, incident_id: str, event_type: str, 
                 event_data: Dict[str, Any], timestamp: Optional[datetime] = None):
        """Initialize incident event."""
        self.incident_id = incident_id
        self.event_type = event_type
        self.event_data = event_data
        self.timestamp = timestamp or datetime.utcnow()
        self.sequence_number: Optional[int] = None
        self.checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "incident_id": self.incident_id,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "timestamp": self.timestamp.isoformat(),
            "sequence_number": self.sequence_number,
            "checksum": self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IncidentEvent":
        """Create event from dictionary."""
        event = cls(
            incident_id=data["incident_id"],
            event_type=data["event_type"],
            event_data=data["event_data"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )
        event.sequence_number = data.get("sequence_number")
        event.checksum = data.get("checksum")
        return event


class IncidentState:
    """Represents the current state of an incident."""
    
    def __init__(self, incident: Optional[Incident] = None):
        """Initialize incident state."""
        self.incident = incident
        self.version = 0
        self.last_updated = datetime.utcnow()
        self.event_count = 0
    
    def apply_event(self, event: IncidentEvent) -> "IncidentState":
        """Apply an event to create new state."""
        # This would contain the business logic for applying events
        # For now, return a new state with incremented version
        new_state = IncidentState(self.incident)
        new_state.version = self.version + 1
        new_state.last_updated = event.timestamp
        new_state.event_count = self.event_count + 1
        return new_state


class EventStore(ABC):
    """Abstract event store interface."""
    
    @abstractmethod
    async def append_event(self, incident_id: str, event: IncidentEvent) -> int:
        """
        Append an event to the incident stream.
        
        Args:
            incident_id: ID of the incident
            event: Event to append
            
        Returns:
            Version number after append
            
        Raises:
            OptimisticLockException: If concurrent write detected
        """
        pass
    
    @abstractmethod
    async def get_events(self, incident_id: str, 
                        from_version: int = 0) -> List[IncidentEvent]:
        """
        Get events for an incident.
        
        Args:
            incident_id: ID of the incident
            from_version: Starting version number
            
        Returns:
            List of events
        """
        pass
    
    @abstractmethod
    async def get_current_version(self, incident_id: str) -> int:
        """
        Get current version for an incident.
        
        Args:
            incident_id: ID of the incident
            
        Returns:
            Current version number
        """
        pass
    
    @abstractmethod
    async def replay_events(self, incident_id: str) -> IncidentState:
        """
        Replay events to reconstruct incident state.
        
        Args:
            incident_id: ID of the incident
            
        Returns:
            Current incident state
        """
        pass
    
    @abstractmethod
    async def stream_events(self, from_timestamp: Optional[datetime] = None) -> AsyncIterator[IncidentEvent]:
        """
        Stream events in real-time.
        
        Args:
            from_timestamp: Start streaming from this timestamp
            
        Yields:
            Incident events as they occur
        """
        pass
    
    @abstractmethod
    async def create_snapshot(self, incident_id: str, state: IncidentState) -> None:
        """
        Create a state snapshot for performance optimization.
        
        Args:
            incident_id: ID of the incident
            state: Current state to snapshot
        """
        pass
    
    @abstractmethod
    async def get_snapshot(self, incident_id: str) -> Optional[IncidentState]:
        """
        Get the latest snapshot for an incident.
        
        Args:
            incident_id: ID of the incident
            
        Returns:
            Latest snapshot or None if no snapshot exists
        """
        pass


class CorruptionResistantEventStore(EventStore):
    """Event store with corruption detection and recovery."""
    
    @abstractmethod
    async def verify_integrity(self, incident_id: str) -> bool:
        """
        Verify integrity of event chain for an incident.
        
        Args:
            incident_id: ID of the incident
            
        Returns:
            True if integrity is intact
        """
        pass
    
    @abstractmethod
    async def detect_corruption(self) -> List[str]:
        """
        Detect corrupted incident chains.
        
        Returns:
            List of incident IDs with detected corruption
        """
        pass
    
    @abstractmethod
    async def repair_from_replica(self, incident_id: str, replica_region: str) -> bool:
        """
        Repair corrupted data from replica.
        
        Args:
            incident_id: ID of the incident to repair
            replica_region: Region to restore from
            
        Returns:
            True if repair successful
        """
        pass