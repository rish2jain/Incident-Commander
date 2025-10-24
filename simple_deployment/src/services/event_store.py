"""
Event store implementation using Kinesis and DynamoDB.
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncIterator
from uuid import uuid4

import aioboto3
from botocore.exceptions import ClientError

from src.interfaces.event_store import EventStore, CorruptionResistantEventStore, IncidentEvent, IncidentState
from src.services.aws import AWSServiceFactory
from src.utils.config import config
from src.utils.logging import get_logger
from src.utils.exceptions import OptimisticLockException, EventCorruptionError


logger = get_logger("event_store")


class ScalableEventStore(EventStore):
    """Kinesis-based event store with DynamoDB persistence."""
    
    def __init__(self, service_factory: AWSServiceFactory):
        """Initialize event store."""
        self._service_factory = service_factory
        self._kinesis_client = None
        self._dynamodb_resource = None
        self._stream_name = config.database.kinesis_stream_name
        self._table_name = config.get_table_name("events")
        self._sequence_counters: Dict[str, int] = {}
    
    async def _get_kinesis_client(self):
        """Get or create Kinesis client."""
        if not self._kinesis_client:
            self._kinesis_client = await self._service_factory.create_client('kinesis')
        return self._kinesis_client
    
    async def _get_dynamodb_resource(self):
        """Get or create DynamoDB resource."""
        if not self._dynamodb_resource:
            self._dynamodb_resource = await self._service_factory.create_resource('dynamodb')
        return self._dynamodb_resource
    
    def _generate_partition_key(self, incident_id: str) -> str:
        """Generate composite partition key to avoid hot partitions."""
        # Use hash of incident_id to distribute across partitions
        hash_value = hashlib.md5(incident_id.encode()).hexdigest()
        partition_suffix = hash_value[:2]  # Use first 2 chars for distribution
        return f"incident_{partition_suffix}_{incident_id}"
    
    def _calculate_integrity_hash(self, event: IncidentEvent) -> str:
        """Calculate cryptographic hash for event integrity."""
        event_data = {
            "incident_id": event.incident_id,
            "event_type": event.event_type,
            "event_data": event.event_data,
            "timestamp": event.timestamp.isoformat()
        }
        json_str = json.dumps(event_data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    async def append_event(self, incident_id: str, event: IncidentEvent) -> int:
        """
        Append event to both Kinesis stream and DynamoDB table.
        
        Args:
            incident_id: ID of the incident
            event: Event to append
            
        Returns:
            Version number after append
        """
        try:
            # Get current version for optimistic locking
            current_version = await self.get_current_version(incident_id)
            new_version = current_version + 1
            
            # Set event metadata
            event.sequence_number = new_version
            event.checksum = self._calculate_integrity_hash(event)
            
            # Publish to Kinesis stream first (for real-time processing)
            kinesis_client = await self._get_kinesis_client()
            partition_key = self._generate_partition_key(incident_id)
            
            kinesis_record = {
                "Data": json.dumps(event.to_dict()),
                "PartitionKey": partition_key
            }
            
            await kinesis_client.put_record(
                StreamName=self._stream_name,
                **kinesis_record
            )
            
            # Store in DynamoDB for persistence and querying
            dynamodb = await self._get_dynamodb_resource()
            table = await dynamodb.Table(self._table_name)
            
            await table.put_item(
                Item={
                    "incident_id": incident_id,
                    "version": new_version,
                    "event_type": event.event_type,
                    "event_data": event.event_data,
                    "timestamp": event.timestamp.isoformat(),
                    "checksum": event.checksum,
                    "partition_key": partition_key,
                    "ttl": int(time.time()) + (365 * 24 * 60 * 60)  # 1 year TTL
                },
                ConditionExpression="attribute_not_exists(version) OR version = :expected_version",
                ExpressionAttributeValues={":expected_version": current_version}
            )
            
            logger.info(f"Appended event {event.event_type} for incident {incident_id}, version {new_version}")
            return new_version
            
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                raise OptimisticLockException(f"Version conflict for incident {incident_id}")
            raise
        except Exception as e:
            logger.error(f"Failed to append event: {e}")
            raise
    
    async def get_events(self, incident_id: str, from_version: int = 0) -> List[IncidentEvent]:
        """Get events for an incident from DynamoDB."""
        try:
            dynamodb = await self._get_dynamodb_resource()
            table = await dynamodb.Table(self._table_name)
            
            response = await table.query(
                KeyConditionExpression="incident_id = :incident_id AND version >= :from_version",
                ExpressionAttributeValues={
                    ":incident_id": incident_id,
                    ":from_version": from_version
                },
                ScanIndexForward=True  # Sort by version ascending
            )
            
            events = []
            for item in response.get("Items", []):
                event = IncidentEvent(
                    incident_id=item["incident_id"],
                    event_type=item["event_type"],
                    event_data=item["event_data"],
                    timestamp=datetime.fromisoformat(item["timestamp"])
                )
                event.sequence_number = item["version"]
                event.checksum = item.get("checksum")
                events.append(event)
            
            return events
            
        except Exception as e:
            logger.error(f"Failed to get events for incident {incident_id}: {e}")
            raise
    
    async def get_current_version(self, incident_id: str) -> int:
        """Get current version for an incident."""
        try:
            dynamodb = await self._get_dynamodb_resource()
            table = await dynamodb.Table(self._table_name)
            
            response = await table.query(
                KeyConditionExpression="incident_id = :incident_id",
                ExpressionAttributeValues={":incident_id": incident_id},
                ScanIndexForward=False,  # Sort descending to get latest
                Limit=1
            )
            
            items = response.get("Items", [])
            if not items:
                return 0
            
            return items[0]["version"]
            
        except Exception as e:
            logger.error(f"Failed to get current version for incident {incident_id}: {e}")
            return 0
    
    async def replay_events(self, incident_id: str) -> IncidentState:
        """Replay events to reconstruct incident state."""
        events = await self.get_events(incident_id)
        
        state = IncidentState()
        for event in events:
            state = state.apply_event(event)
        
        return state
    
    async def stream_events(self, from_timestamp: Optional[datetime] = None) -> AsyncIterator[IncidentEvent]:
        """Stream events from Kinesis in real-time."""
        try:
            kinesis_client = await self._get_kinesis_client()
            
            # Get stream description
            stream_desc = await kinesis_client.describe_stream(StreamName=self._stream_name)
            shards = stream_desc["StreamDescription"]["Shards"]
            
            # Create iterators for each shard
            shard_iterators = []
            for shard in shards:
                shard_id = shard["ShardId"]
                
                iterator_response = await kinesis_client.get_shard_iterator(
                    StreamName=self._stream_name,
                    ShardId=shard_id,
                    ShardIteratorType="LATEST" if not from_timestamp else "AT_TIMESTAMP",
                    Timestamp=from_timestamp if from_timestamp else None
                )
                
                shard_iterators.append(iterator_response["ShardIterator"])
            
            # Poll shards for records
            while True:
                for i, iterator in enumerate(shard_iterators):
                    if not iterator:
                        continue
                    
                    try:
                        response = await kinesis_client.get_records(ShardIterator=iterator)
                        
                        for record in response.get("Records", []):
                            try:
                                event_data = json.loads(record["Data"])
                                event = IncidentEvent.from_dict(event_data)
                                yield event
                            except Exception as e:
                                logger.warning(f"Failed to parse event record: {e}")
                        
                        # Update iterator for next poll
                        shard_iterators[i] = response.get("NextShardIterator")
                        
                    except Exception as e:
                        logger.warning(f"Error reading from shard: {e}")
                        shard_iterators[i] = None
                
                # Brief pause between polls
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Error streaming events: {e}")
            raise
    
    async def create_snapshot(self, incident_id: str, state: IncidentState) -> None:
        """Create state snapshot for performance optimization."""
        try:
            dynamodb = await self._get_dynamodb_resource()
            snapshot_table = await dynamodb.Table(config.get_table_name("snapshots"))
            
            await snapshot_table.put_item(
                Item={
                    "incident_id": incident_id,
                    "version": state.version,
                    "state_data": state.__dict__,
                    "created_at": datetime.utcnow().isoformat(),
                    "ttl": int(time.time()) + (30 * 24 * 60 * 60)  # 30 days TTL
                }
            )
            
            logger.info(f"Created snapshot for incident {incident_id} at version {state.version}")
            
        except Exception as e:
            logger.error(f"Failed to create snapshot: {e}")
            raise
    
    async def get_snapshot(self, incident_id: str) -> Optional[IncidentState]:
        """Get latest snapshot for an incident."""
        try:
            dynamodb = await self._get_dynamodb_resource()
            snapshot_table = await dynamodb.Table(config.get_table_name("snapshots"))
            
            response = await snapshot_table.get_item(
                Key={"incident_id": incident_id}
            )
            
            if "Item" not in response:
                return None
            
            item = response["Item"]
            state = IncidentState()
            state.__dict__.update(item["state_data"])
            
            return state
            
        except Exception as e:
            logger.error(f"Failed to get snapshot: {e}")
            return None


class CorruptionResistantEventStoreImpl(ScalableEventStore, CorruptionResistantEventStore):
    """Event store with corruption detection and multi-region replication."""
    
    def __init__(self, service_factory: AWSServiceFactory, replica_regions: List[str] = None):
        """Initialize corruption-resistant event store."""
        super().__init__(service_factory)
        self._replica_regions = replica_regions or ["us-west-2", "eu-west-1"]
        self._replica_clients = {}
        self._replication_enabled = True
        self._cross_region_timeout = 10  # seconds
    
    async def _get_replica_client(self, region: str):
        """Get DynamoDB client for replica region."""
        if region not in self._replica_clients:
            self._replica_clients[region] = await self._service_factory.create_client(
                'dynamodb', region_name=region
            )
        return self._replica_clients[region]
    
    async def verify_integrity(self, incident_id: str) -> bool:
        """Verify integrity of event chain for an incident."""
        try:
            events = await self.get_events(incident_id)
            
            for event in events:
                # Verify checksum
                expected_checksum = self._calculate_integrity_hash(event)
                if event.checksum != expected_checksum:
                    logger.error(f"Checksum mismatch for event {event.sequence_number} in incident {incident_id}")
                    return False
            
            # Verify sequence continuity
            expected_sequence = 1
            for event in events:
                if event.sequence_number != expected_sequence:
                    logger.error(f"Sequence gap detected in incident {incident_id}: expected {expected_sequence}, got {event.sequence_number}")
                    return False
                expected_sequence += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify integrity for incident {incident_id}: {e}")
            return False
    
    async def detect_corruption(self) -> List[str]:
        """Detect corrupted incident chains."""
        corrupted_incidents = []
        
        try:
            # This would typically scan all incidents, but for demo we'll check recent ones
            dynamodb = await self._get_dynamodb_resource()
            table = await dynamodb.Table(self._table_name)
            
            # Get unique incident IDs from recent events
            response = await table.scan(
                ProjectionExpression="incident_id",
                FilterExpression="attribute_exists(incident_id)"
            )
            
            incident_ids = set()
            for item in response.get("Items", []):
                incident_ids.add(item["incident_id"])
            
            # Check integrity for each incident
            for incident_id in incident_ids:
                if not await self.verify_integrity(incident_id):
                    corrupted_incidents.append(incident_id)
            
        except Exception as e:
            logger.error(f"Failed to detect corruption: {e}")
        
        return corrupted_incidents
    
    async def repair_from_replica(self, incident_id: str, replica_region: str) -> bool:
        """Repair corrupted data from replica region."""
        try:
            replica_client = await self._get_replica_client(replica_region)
            
            # Get events from replica
            response = await replica_client.query(
                TableName=self._table_name,
                KeyConditionExpression="incident_id = :incident_id",
                ExpressionAttributeValues={":incident_id": {"S": incident_id}},
                ScanIndexForward=True
            )
            
            # Restore events to primary region
            dynamodb = await self._get_dynamodb_resource()
            table = await dynamodb.Table(self._table_name)
            
            for item in response.get("Items", []):
                # Convert DynamoDB format to our format
                restored_item = {
                    "incident_id": item["incident_id"]["S"],
                    "version": int(item["version"]["N"]),
                    "event_type": item["event_type"]["S"],
                    "event_data": json.loads(item["event_data"]["S"]),
                    "timestamp": item["timestamp"]["S"],
                    "checksum": item["checksum"]["S"],
                    "partition_key": item["partition_key"]["S"]
                }
                
                await table.put_item(Item=restored_item)
            
            logger.info(f"Repaired incident {incident_id} from replica region {replica_region}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to repair from replica: {e}")
            return False
    
    async def replicate_to_regions(self, incident_id: str, event: IncidentEvent) -> Dict[str, bool]:
        """Replicate event to all configured regions."""
        replication_results = {}
        
        if not self._replication_enabled:
            return replication_results
        
        for region in self._replica_regions:
            try:
                replica_client = await self._get_replica_client(region)
                
                # Replicate to region with timeout
                await asyncio.wait_for(
                    self._replicate_single_event(replica_client, incident_id, event),
                    timeout=self._cross_region_timeout
                )
                
                replication_results[region] = True
                logger.debug(f"Successfully replicated event to {region}")
                
            except asyncio.TimeoutError:
                logger.warning(f"Replication to {region} timed out")
                replication_results[region] = False
            except Exception as e:
                logger.error(f"Failed to replicate to {region}: {e}")
                replication_results[region] = False
        
        return replication_results
    
    async def _replicate_single_event(self, replica_client, incident_id: str, event: IncidentEvent) -> None:
        """Replicate a single event to a replica region."""
        await replica_client.put_item(
            TableName=self._table_name,
            Item={
                "incident_id": {"S": incident_id},
                "version": {"N": str(event.sequence_number)},
                "event_type": {"S": event.event_type},
                "event_data": {"S": json.dumps(event.event_data)},
                "timestamp": {"S": event.timestamp.isoformat()},
                "checksum": {"S": event.checksum},
                "partition_key": {"S": self._generate_partition_key(incident_id)},
                "ttl": {"N": str(int(time.time()) + (365 * 24 * 60 * 60))}
            }
        )
    
    async def failover_to_region(self, target_region: str) -> bool:
        """Failover to a specific region in case of primary region failure."""
        try:
            logger.warning(f"Initiating failover to region: {target_region}")
            
            # Update service factory to use target region
            self._service_factory.region = target_region
            
            # Reset clients to force recreation with new region
            self._kinesis_client = None
            self._dynamodb_resource = None
            
            # Test connectivity to new region
            test_client = await self._get_dynamodb_resource()
            await test_client.meta.client.describe_table(TableName=self._table_name)
            
            logger.info(f"Successfully failed over to region: {target_region}")
            return True
            
        except Exception as e:
            logger.error(f"Failover to {target_region} failed: {e}")
            return False
    
    async def get_replication_status(self) -> Dict[str, Any]:
        """Get replication status across all regions."""
        status = {
            "primary_region": self._service_factory.region,
            "replication_enabled": self._replication_enabled,
            "replica_regions": self._replica_regions,
            "region_health": {}
        }
        
        for region in self._replica_regions:
            try:
                replica_client = await self._get_replica_client(region)
                
                # Test connectivity with a simple describe operation
                await asyncio.wait_for(
                    replica_client.describe_table(TableName=self._table_name),
                    timeout=5
                )
                
                status["region_health"][region] = {
                    "status": "healthy",
                    "last_check": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                status["region_health"][region] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "last_check": datetime.utcnow().isoformat()
                }
        
        return status