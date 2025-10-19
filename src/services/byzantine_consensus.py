"""
Byzantine Fault-Tolerant Consensus Engine

Implements Practical Byzantine Fault Tolerance (PBFT) for multi-agent incident resolution.
Handles up to f = (n-1)/3 malicious agents where n is total agents.

Features:
- 3-phase PBFT protocol (pre-prepare, prepare, commit)
- Cryptographic message signatures
- Quorum verification
- Malicious agent detection and isolation
- View change for leader failures
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature

from src.models.incident import Incident
from src.models.agent import AgentRecommendation, ConsensusDecision, AgentType
from src.utils.logging import get_logger
from src.utils.exceptions import ByzantineConsensusError, MaliciousAgentDetected


logger = get_logger("byzantine_consensus")


class MessageType(Enum):
    """PBFT message types."""
    PRE_PREPARE = "pre_prepare"
    PREPARE = "prepare"
    COMMIT = "commit"
    VIEW_CHANGE = "view_change"
    NEW_VIEW = "new_view"


class NodeState(Enum):
    """Node states in PBFT protocol."""
    NORMAL = "normal"
    VIEW_CHANGE = "view_change"
    SUSPECTED = "suspected"
    ISOLATED = "isolated"


@dataclass
class PBFTMessage:
    """PBFT protocol message."""
    message_type: MessageType
    view: int
    sequence: int
    digest: str
    node_id: str
    timestamp: datetime
    payload: Dict[str, Any]
    signature: Optional[bytes] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "message_type": self.message_type.value,
            "view": self.view,
            "sequence": self.sequence,
            "digest": self.digest,
            "node_id": self.node_id,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "signature": self.signature.hex() if self.signature else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PBFTMessage':
        """Create message from dictionary."""
        return cls(
            message_type=MessageType(data["message_type"]),
            view=data["view"],
            sequence=data["sequence"],
            digest=data["digest"],
            node_id=data["node_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            payload=data["payload"],
            signature=bytes.fromhex(data["signature"]) if data["signature"] else None
        )


@dataclass
class NodeInfo:
    """Information about a PBFT node."""
    node_id: str
    public_key: bytes
    state: NodeState = NodeState.NORMAL
    last_seen: Optional[datetime] = None
    suspicious_count: int = 0
    performance_score: float = 1.0


@dataclass
class ConsensusRound:
    """Tracks a single consensus round."""
    sequence: int
    view: int
    proposal: AgentRecommendation
    digest: str
    pre_prepare_msg: Optional[PBFTMessage] = None
    prepare_msgs: Dict[str, PBFTMessage] = field(default_factory=dict)
    commit_msgs: Dict[str, PBFTMessage] = field(default_factory=dict)
    decided: bool = False
    decision: Optional[ConsensusDecision] = None
    start_time: datetime = field(default_factory=datetime.utcnow)


class ByzantineFaultTolerantConsensus:
    """
    Practical Byzantine Fault Tolerance implementation for agent consensus.
    
    Supports up to f = (n-1)/3 Byzantine (malicious) agents.
    """
    
    def __init__(self, node_id: str, total_nodes: int):
        """
        Initialize PBFT consensus engine.
        
        Args:
            node_id: Unique identifier for this node
            total_nodes: Total number of nodes in the system
        """
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.fault_tolerance = (total_nodes - 1) // 3  # Maximum Byzantine nodes
        self.quorum_size = 2 * self.fault_tolerance + 1  # Minimum for safety
        
        # PBFT state
        self.current_view = 0
        self.sequence_number = 0
        self.primary_node = self._calculate_primary(self.current_view)
        
        # Node management
        self.nodes: Dict[str, NodeInfo] = {}
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()
        
        # Consensus tracking
        self.active_rounds: Dict[int, ConsensusRound] = {}
        self.completed_rounds: List[ConsensusRound] = []
        self.message_log: List[PBFTMessage] = []
        
        # Byzantine detection
        self.suspicious_patterns: Dict[str, List[datetime]] = {}
        self.isolated_nodes: Set[str] = set()
        
        # Performance metrics
        self.consensus_times: List[float] = []
        self.byzantine_detections = 0
        self.view_changes = 0
        
        logger.info(f"Initialized PBFT node {node_id} with {total_nodes} total nodes, "
                   f"fault tolerance: {self.fault_tolerance}")
    
    def register_node(self, node_id: str, public_key: bytes):
        """Register a node in the PBFT network."""
        self.nodes[node_id] = NodeInfo(
            node_id=node_id,
            public_key=public_key,
            last_seen=datetime.utcnow()
        )
        logger.info(f"Registered node {node_id}")
    
    async def propose_action(self, incident: Incident, 
                           recommendation: AgentRecommendation) -> ConsensusDecision:
        """
        Propose an action for consensus using PBFT protocol.
        
        Args:
            incident: The incident requiring consensus
            recommendation: Proposed action
            
        Returns:
            Consensus decision
        """
        if self.node_id != self.primary_node:
            raise ByzantineConsensusError(f"Only primary node {self.primary_node} can propose")
        
        # Create new consensus round
        self.sequence_number += 1
        digest = self._calculate_digest(recommendation)
        
        round_info = ConsensusRound(
            sequence=self.sequence_number,
            view=self.current_view,
            proposal=recommendation,
            digest=digest
        )
        
        self.active_rounds[self.sequence_number] = round_info
        
        # Phase 1: Pre-prepare
        pre_prepare_msg = PBFTMessage(
            message_type=MessageType.PRE_PREPARE,
            view=self.current_view,
            sequence=self.sequence_number,
            digest=digest,
            node_id=self.node_id,
            timestamp=datetime.utcnow(),
            payload={
                "incident_id": incident.id,
                "recommendation": recommendation.to_dict() if hasattr(recommendation, 'to_dict') else str(recommendation)
            }
        )
        
        # Sign the message
        pre_prepare_msg.signature = self._sign_message(pre_prepare_msg)
        round_info.pre_prepare_msg = pre_prepare_msg
        
        # Broadcast pre-prepare to all nodes
        await self._broadcast_message(pre_prepare_msg)
        
        # Wait for consensus
        decision = await self._wait_for_consensus(self.sequence_number)
        return decision
    
    async def handle_message(self, message: PBFTMessage) -> Optional[ConsensusDecision]:
        """
        Handle incoming PBFT message.
        
        Args:
            message: PBFT message to process
            
        Returns:
            Consensus decision if reached, None otherwise
        """
        try:
            # Verify message signature
            if not self._verify_signature(message):
                logger.warning(f"Invalid signature from {message.node_id}")
                await self._record_suspicious_behavior(message.node_id, "invalid_signature")
                return None
            
            # Check if node is isolated
            if message.node_id in self.isolated_nodes:
                logger.debug(f"Ignoring message from isolated node {message.node_id}")
                return None
            
            # Update node last seen
            if message.node_id in self.nodes:
                self.nodes[message.node_id].last_seen = datetime.utcnow()
            
            # Process based on message type
            if message.message_type == MessageType.PRE_PREPARE:
                return await self._handle_pre_prepare(message)
            elif message.message_type == MessageType.PREPARE:
                return await self._handle_prepare(message)
            elif message.message_type == MessageType.COMMIT:
                return await self._handle_commit(message)
            elif message.message_type == MessageType.VIEW_CHANGE:
                return await self._handle_view_change(message)
            else:
                logger.warning(f"Unknown message type: {message.message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message from {message.node_id}: {e}")
            await self._record_suspicious_behavior(message.node_id, "message_processing_error")
            
        return None
    
    async def _handle_pre_prepare(self, message: PBFTMessage) -> Optional[ConsensusDecision]:
        """Handle pre-prepare message (Phase 1)."""
        # Only accept pre-prepare from primary
        if message.node_id != self.primary_node:
            logger.warning(f"Pre-prepare from non-primary {message.node_id}")
            await self._record_suspicious_behavior(message.node_id, "unauthorized_pre_prepare")
            return None
        
        # Check view and sequence
        if message.view != self.current_view:
            logger.debug(f"Pre-prepare view mismatch: {message.view} vs {self.current_view}")
            return None
        
        # Create or update consensus round
        if message.sequence not in self.active_rounds:
            # Reconstruct recommendation from payload
            recommendation = self._reconstruct_recommendation(message.payload)
            
            round_info = ConsensusRound(
                sequence=message.sequence,
                view=message.view,
                proposal=recommendation,
                digest=message.digest,
                pre_prepare_msg=message
            )
            self.active_rounds[message.sequence] = round_info
        
        # Send prepare message
        prepare_msg = PBFTMessage(
            message_type=MessageType.PREPARE,
            view=self.current_view,
            sequence=message.sequence,
            digest=message.digest,
            node_id=self.node_id,
            timestamp=datetime.utcnow(),
            payload={}
        )
        prepare_msg.signature = self._sign_message(prepare_msg)
        
        await self._broadcast_message(prepare_msg)
        return None
    
    async def _handle_prepare(self, message: PBFTMessage) -> Optional[ConsensusDecision]:
        """Handle prepare message (Phase 2)."""
        if message.sequence not in self.active_rounds:
            logger.debug(f"Prepare for unknown sequence {message.sequence}")
            return None
        
        round_info = self.active_rounds[message.sequence]
        
        # Verify digest matches
        if message.digest != round_info.digest:
            logger.warning(f"Digest mismatch from {message.node_id}")
            await self._record_suspicious_behavior(message.node_id, "digest_mismatch")
            return None
        
        # Store prepare message
        round_info.prepare_msgs[message.node_id] = message
        
        # Check if we have enough prepare messages (including our own)
        if len(round_info.prepare_msgs) >= self.quorum_size - 1:  # -1 for pre-prepare
            # Send commit message
            commit_msg = PBFTMessage(
                message_type=MessageType.COMMIT,
                view=self.current_view,
                sequence=message.sequence,
                digest=message.digest,
                node_id=self.node_id,
                timestamp=datetime.utcnow(),
                payload={}
            )
            commit_msg.signature = self._sign_message(commit_msg)
            
            await self._broadcast_message(commit_msg)
        
        return None
    
    async def _handle_commit(self, message: PBFTMessage) -> Optional[ConsensusDecision]:
        """Handle commit message (Phase 3)."""
        if message.sequence not in self.active_rounds:
            logger.debug(f"Commit for unknown sequence {message.sequence}")
            return None
        
        round_info = self.active_rounds[message.sequence]
        
        # Verify digest matches
        if message.digest != round_info.digest:
            logger.warning(f"Commit digest mismatch from {message.node_id}")
            await self._record_suspicious_behavior(message.node_id, "commit_digest_mismatch")
            return None
        
        # Store commit message
        round_info.commit_msgs[message.node_id] = message
        
        # Check if we have enough commit messages
        if len(round_info.commit_msgs) >= self.quorum_size and not round_info.decided:
            # Consensus reached!
            round_info.decided = True
            consensus_time = (datetime.utcnow() - round_info.start_time).total_seconds()
            self.consensus_times.append(consensus_time)
            
            # Create consensus decision
            decision = ConsensusDecision(
                incident_id=round_info.proposal.incident_id if hasattr(round_info.proposal, 'incident_id') else "unknown",
                selected_action=round_info.proposal.action_id if hasattr(round_info.proposal, 'action_id') else "unknown",
                action_type=str(round_info.proposal.action_type) if hasattr(round_info.proposal, 'action_type') else "unknown",
                final_confidence=1.0,  # PBFT provides certainty
                participating_agents=[msg.node_id for msg in round_info.commit_msgs.values()],
                agent_recommendations=[round_info.proposal],
                consensus_method="pbft",
                conflicts_detected=False,
                requires_human_approval=False,
                approval_threshold=1.0,
                processing_duration_ms=int(consensus_time * 1000),
                byzantine_nodes_detected=len(self.isolated_nodes),
                quorum_size=self.quorum_size,
                total_nodes=self.total_nodes
            )
            
            round_info.decision = decision
            self.completed_rounds.append(round_info)
            del self.active_rounds[message.sequence]
            
            logger.info(f"PBFT consensus reached for sequence {message.sequence} in {consensus_time:.2f}s")
            return decision
        
        return None
    
    async def _handle_view_change(self, message: PBFTMessage):
        """Handle view change message."""
        # TODO: Implement view change protocol for primary failures
        logger.info(f"View change requested by {message.node_id}")
        self.view_changes += 1
    
    def _calculate_primary(self, view: int) -> str:
        """Calculate primary node for given view."""
        node_ids = sorted(self.nodes.keys())
        if not node_ids:
            return self.node_id
        return node_ids[view % len(node_ids)]
    
    def _calculate_digest(self, recommendation: AgentRecommendation) -> str:
        """Calculate cryptographic digest of recommendation."""
        data = json.dumps(str(recommendation), sort_keys=True).encode()
        return hashlib.sha256(data).hexdigest()
    
    def _sign_message(self, message: PBFTMessage) -> bytes:
        """Sign a PBFT message."""
        message_data = json.dumps({
            "type": message.message_type.value,
            "view": message.view,
            "sequence": message.sequence,
            "digest": message.digest,
            "node_id": message.node_id,
            "timestamp": message.timestamp.isoformat(),
            "payload": message.payload
        }, sort_keys=True).encode()
        
        signature = self.private_key.sign(
            message_data,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return signature
    
    def _verify_signature(self, message: PBFTMessage) -> bool:
        """Verify message signature."""
        if not message.signature or message.node_id not in self.nodes:
            return False
        
        try:
            node_info = self.nodes[message.node_id]
            public_key = serialization.load_der_public_key(node_info.public_key)
            
            message_data = json.dumps({
                "type": message.message_type.value,
                "view": message.view,
                "sequence": message.sequence,
                "digest": message.digest,
                "node_id": message.node_id,
                "timestamp": message.timestamp.isoformat(),
                "payload": message.payload
            }, sort_keys=True).encode()
            
            public_key.verify(
                message.signature,
                message_data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
            
        except (InvalidSignature, Exception) as e:
            logger.debug(f"Signature verification failed for {message.node_id}: {e}")
            return False
    
    async def _record_suspicious_behavior(self, node_id: str, behavior_type: str):
        """Record suspicious behavior for Byzantine detection."""
        if node_id not in self.suspicious_patterns:
            self.suspicious_patterns[node_id] = []
        
        self.suspicious_patterns[node_id].append(datetime.utcnow())
        
        # Check for patterns indicating Byzantine behavior
        recent_suspicious = [
            ts for ts in self.suspicious_patterns[node_id]
            if datetime.utcnow() - ts < timedelta(minutes=5)
        ]
        
        if len(recent_suspicious) >= 3:  # 3 suspicious behaviors in 5 minutes
            await self._isolate_byzantine_node(node_id)
    
    async def _isolate_byzantine_node(self, node_id: str):
        """Isolate a detected Byzantine node."""
        if node_id not in self.isolated_nodes:
            self.isolated_nodes.add(node_id)
            self.byzantine_detections += 1
            
            if node_id in self.nodes:
                self.nodes[node_id].state = NodeState.ISOLATED
            
            logger.warning(f"Isolated Byzantine node {node_id}")
            
            # Trigger view change if primary is isolated
            if node_id == self.primary_node:
                await self._initiate_view_change()
    
    async def _initiate_view_change(self):
        """Initiate view change protocol."""
        self.current_view += 1
        self.primary_node = self._calculate_primary(self.current_view)
        logger.info(f"View change to {self.current_view}, new primary: {self.primary_node}")
    
    def _reconstruct_recommendation(self, payload: Dict[str, Any]) -> AgentRecommendation:
        """Reconstruct agent recommendation from message payload."""
        # TODO: Implement proper reconstruction based on your AgentRecommendation model
        # This is a placeholder implementation
        return payload.get("recommendation", {})
    
    async def _broadcast_message(self, message: PBFTMessage):
        """Broadcast message to all nodes."""
        # TODO: Implement actual network broadcasting
        # For now, just log the message
        logger.debug(f"Broadcasting {message.message_type.value} message from {message.node_id}")
        self.message_log.append(message)
    
    async def _wait_for_consensus(self, sequence: int, timeout: float = 30.0) -> ConsensusDecision:
        """Wait for consensus on a specific sequence."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if sequence in self.active_rounds:
                round_info = self.active_rounds[sequence]
                if round_info.decided and round_info.decision:
                    return round_info.decision
            
            await asyncio.sleep(0.1)
        
        raise ByzantineConsensusError(f"Consensus timeout for sequence {sequence}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get PBFT performance metrics."""
        avg_consensus_time = sum(self.consensus_times) / len(self.consensus_times) if self.consensus_times else 0
        
        return {
            "node_id": self.node_id,
            "current_view": self.current_view,
            "primary_node": self.primary_node,
            "total_nodes": self.total_nodes,
            "fault_tolerance": self.fault_tolerance,
            "quorum_size": self.quorum_size,
            "completed_rounds": len(self.completed_rounds),
            "active_rounds": len(self.active_rounds),
            "byzantine_detections": self.byzantine_detections,
            "isolated_nodes": list(self.isolated_nodes),
            "view_changes": self.view_changes,
            "average_consensus_time_ms": avg_consensus_time * 1000,
            "node_states": {
                node_id: {
                    "state": info.state.value,
                    "last_seen": info.last_seen.isoformat() if info.last_seen else None,
                    "suspicious_count": info.suspicious_count,
                    "performance_score": info.performance_score
                }
                for node_id, info in self.nodes.items()
            }
        }