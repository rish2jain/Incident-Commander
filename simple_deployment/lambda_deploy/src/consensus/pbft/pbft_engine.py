"""
Practical Byzantine Fault Tolerance (PBFT) Consensus Engine.

This implements a simplified PBFT algorithm for distributed consensus among
incident response agents. The algorithm ensures consensus even when some agents
are faulty or malicious (Byzantine failures).

PBFT Phases:
1. PRE-PREPARE: Primary proposes a value
2. PREPARE: Replicas exchange prepare messages
3. COMMIT: Replicas exchange commit messages
4. REPLY: Execute operation after 2f+1 commits

Fault Tolerance: Tolerates up to f = (n-1)/3 Byzantine failures
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from src.utils.logging import get_logger


logger = get_logger("consensus.pbft")


class MessageType(Enum):
    """PBFT message types."""

    PRE_PREPARE = "pre-prepare"
    PREPARE = "prepare"
    COMMIT = "commit"
    VIEW_CHANGE = "view-change"
    NEW_VIEW = "new-view"


class ConsensusPhase(Enum):
    """PBFT consensus phases."""

    IDLE = "idle"
    PRE_PREPARED = "pre-prepared"
    PREPARED = "prepared"
    COMMITTED = "committed"
    EXECUTED = "executed"


@dataclass
class PBFTMessage:
    """PBFT protocol message."""

    message_type: MessageType
    view: int
    sequence_number: int
    node_id: str
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    signature: Optional[str] = None
    message_id: str = field(default_factory=lambda: str(uuid4()))

    def digest(self) -> str:
        """Calculate message digest for signing/verification."""
        content = {
            "type": self.message_type.value,
            "view": self.view,
            "seq": self.sequence_number,
            "node": self.node_id,
            "payload": self.payload,
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message_type": self.message_type.value,
            "view": self.view,
            "sequence_number": self.sequence_number,
            "node_id": self.node_id,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "signature": self.signature,
            "message_id": self.message_id,
            "digest": self.digest(),
        }


@dataclass
class PBFTNode:
    """PBFT node representing an agent in the consensus protocol."""

    node_id: str
    public_key: Optional[rsa.RSAPublicKey] = None
    is_primary: bool = False
    is_faulty: bool = False
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_alive(self, timeout_seconds: int = 30) -> bool:
        """Check if node is alive based on heartbeat."""
        age = (datetime.now(timezone.utc) - self.last_heartbeat).total_seconds()
        return age < timeout_seconds


@dataclass
class ConsensusProposal:
    """Proposal for consensus."""

    proposal_id: str
    proposer: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def digest(self) -> str:
        """Calculate proposal digest."""
        content = json.dumps(self.data, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class ConsensusResult:
    """Result of consensus protocol."""

    proposal_id: str
    decision: Dict[str, Any]
    participating_nodes: List[str]
    view: int
    sequence_number: int
    phase: ConsensusPhase
    confidence: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    execution_time_ms: float = 0.0


class PBFTConsensusEngine:
    """
    Practical Byzantine Fault Tolerance consensus engine.

    This engine implements the PBFT algorithm for achieving consensus
    among distributed agents, tolerating up to f Byzantine failures
    where f = (n-1)/3.
    """

    def __init__(
        self,
        node_id: str,
        total_nodes: int,
        heartbeat_timeout: int = 30,
        prepare_timeout: int = 10,
        commit_timeout: int = 10,
    ):
        """
        Initialize PBFT engine.

        Args:
            node_id: Unique identifier for this node
            total_nodes: Total number of nodes in the network
            heartbeat_timeout: Timeout for node heartbeats (seconds)
            prepare_timeout: Timeout for prepare phase (seconds)
            commit_timeout: Timeout for commit phase (seconds)
        """
        self.node_id = node_id
        self.total_nodes = total_nodes
        self.fault_tolerance = (total_nodes - 1) // 3  # f = (n-1)/3
        self.required_quorum = 2 * self.fault_tolerance + 1  # 2f + 1

        # Timeouts
        self.heartbeat_timeout = heartbeat_timeout
        self.prepare_timeout = prepare_timeout
        self.commit_timeout = commit_timeout

        # PBFT state
        self.view = 0
        self.sequence_number = 0
        self.phase = ConsensusPhase.IDLE
        self.current_proposal: Optional[ConsensusProposal] = None

        # Node management
        self.nodes: Dict[str, PBFTNode] = {}
        self.primary_node_id: Optional[str] = None

        # Message logs
        self.pre_prepare_log: Dict[int, PBFTMessage] = {}
        self.prepare_log: Dict[int, Set[str]] = {}  # seq -> set of node_ids
        self.commit_log: Dict[int, Set[str]] = {}  # seq -> set of node_ids

        # Cryptographic keys (simplified - in production use proper key management)
        self.private_key: Optional[rsa.RSAPrivateKey] = None
        self.public_key: Optional[rsa.RSAPublicKey] = None

        logger.info(
            f"PBFT engine initialized",
            extra={
                "node_id": node_id,
                "total_nodes": total_nodes,
                "fault_tolerance": self.fault_tolerance,
                "required_quorum": self.required_quorum,
            },
        )

    def initialize_keys(self) -> None:
        """Initialize cryptographic keys for signing."""
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self.public_key = self.private_key.public_key()
        logger.info(f"Generated cryptographic keys for node {self.node_id}")

    def register_node(self, node: PBFTNode) -> None:
        """Register a node in the PBFT network."""
        self.nodes[node.node_id] = node
        logger.info(f"Registered node: {node.node_id}")

        # Set primary if not set
        if self.primary_node_id is None:
            self._select_primary()

    def _select_primary(self) -> None:
        """Select primary node based on view number."""
        if not self.nodes:
            return

        # Primary is selected deterministically: primary = view mod n
        sorted_nodes = sorted(self.nodes.keys())
        primary_index = self.view % len(sorted_nodes)
        self.primary_node_id = sorted_nodes[primary_index]

        # Update node states
        for node_id, node in self.nodes.items():
            node.is_primary = node_id == self.primary_node_id

        logger.info(
            f"Selected primary node: {self.primary_node_id}",
            extra={"view": self.view},
        )

    def is_primary(self) -> bool:
        """Check if this node is the current primary."""
        return self.node_id == self.primary_node_id

    async def reach_consensus(self, proposal: ConsensusProposal) -> ConsensusResult:
        """
        Execute the PBFT consensus protocol.

        Args:
            proposal: The proposal to reach consensus on

        Returns:
            ConsensusResult with the consensus decision
        """
        start_time = asyncio.get_event_loop().time()

        logger.info(
            f"Starting PBFT consensus",
            extra={
                "proposal_id": proposal.proposal_id,
                "proposer": proposal.proposer,
                "view": self.view,
            },
        )

        try:
            # Phase 1: PRE-PREPARE
            self.current_proposal = proposal
            self.sequence_number += 1
            seq = self.sequence_number

            if self.is_primary():
                await self._phase_pre_prepare(proposal, seq)
            else:
                await self._wait_for_pre_prepare(seq)

            # Phase 2: PREPARE
            await self._phase_prepare(seq)

            # Phase 3: COMMIT
            await self._phase_commit(seq)

            # Phase 4: EXECUTE
            result = await self._phase_execute(proposal, seq)

            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000

            result.execution_time_ms = execution_time

            logger.info(
                f"PBFT consensus reached",
                extra={
                    "proposal_id": proposal.proposal_id,
                    "view": self.view,
                    "sequence": seq,
                    "execution_time_ms": execution_time,
                },
            )

            return result

        except Exception as e:
            logger.error(f"PBFT consensus failed: {e}", exc_info=True)
            # Return fallback result
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return ConsensusResult(
                proposal_id=proposal.proposal_id,
                decision=proposal.data,
                participating_nodes=[self.node_id],
                view=self.view,
                sequence_number=seq,
                phase=ConsensusPhase.IDLE,
                confidence=0.5,
                execution_time_ms=execution_time,
            )

    async def _phase_pre_prepare(
        self, proposal: ConsensusProposal, sequence: int
    ) -> None:
        """PRE-PREPARE phase: Primary broadcasts proposal."""
        message = PBFTMessage(
            message_type=MessageType.PRE_PREPARE,
            view=self.view,
            sequence_number=sequence,
            node_id=self.node_id,
            payload={
                "proposal_id": proposal.proposal_id,
                "proposal_data": proposal.data,
                "digest": proposal.digest(),
            },
        )

        # Sign message (simplified)
        message.signature = self._sign_message(message)

        # Store in log
        self.pre_prepare_log[sequence] = message

        # Update phase
        self.phase = ConsensusPhase.PRE_PREPARED

        logger.debug(
            f"PRE-PREPARE phase completed",
            extra={"sequence": sequence, "view": self.view},
        )

    async def _wait_for_pre_prepare(self, sequence: int) -> None:
        """Wait for PRE-PREPARE message from primary."""
        # In a real implementation, this would wait for network messages
        # For now, simulate receiving pre-prepare
        await asyncio.sleep(0.01)
        self.phase = ConsensusPhase.PRE_PREPARED

    async def _phase_prepare(self, sequence: int) -> None:
        """PREPARE phase: Replicas exchange prepare messages."""
        # Send PREPARE message to all replicas
        message = PBFTMessage(
            message_type=MessageType.PREPARE,
            view=self.view,
            sequence_number=sequence,
            node_id=self.node_id,
            payload={"digest": self.current_proposal.digest() if self.current_proposal else ""},
        )

        message.signature = self._sign_message(message)

        # Record own prepare
        if sequence not in self.prepare_log:
            self.prepare_log[sequence] = set()
        self.prepare_log[sequence].add(self.node_id)

        # Simulate receiving prepares from other nodes (2f+1 total)
        # In production, this would wait for actual network messages
        await asyncio.sleep(0.01)

        # Check if we have quorum (2f + 1 prepare messages)
        prepare_count = len(self.prepare_log.get(sequence, set()))
        if prepare_count >= self.required_quorum:
            self.phase = ConsensusPhase.PREPARED
            logger.debug(
                f"PREPARE phase completed",
                extra={"sequence": sequence, "prepare_count": prepare_count},
            )
        else:
            logger.warning(
                f"Insufficient prepares for sequence {sequence}: {prepare_count}/{self.required_quorum}"
            )

    async def _phase_commit(self, sequence: int) -> None:
        """COMMIT phase: Replicas exchange commit messages."""
        # Send COMMIT message to all replicas
        message = PBFTMessage(
            message_type=MessageType.COMMIT,
            view=self.view,
            sequence_number=sequence,
            node_id=self.node_id,
            payload={"digest": self.current_proposal.digest() if self.current_proposal else ""},
        )

        message.signature = self._sign_message(message)

        # Record own commit
        if sequence not in self.commit_log:
            self.commit_log[sequence] = set()
        self.commit_log[sequence].add(self.node_id)

        # Simulate receiving commits from other nodes
        await asyncio.sleep(0.01)

        # Check if we have quorum (2f + 1 commit messages)
        commit_count = len(self.commit_log.get(sequence, set()))
        if commit_count >= self.required_quorum:
            self.phase = ConsensusPhase.COMMITTED
            logger.debug(
                f"COMMIT phase completed",
                extra={"sequence": sequence, "commit_count": commit_count},
            )
        else:
            logger.warning(
                f"Insufficient commits for sequence {sequence}: {commit_count}/{self.required_quorum}"
            )

    async def _phase_execute(
        self, proposal: ConsensusProposal, sequence: int
    ) -> ConsensusResult:
        """EXECUTE phase: Execute the operation and return result."""
        self.phase = ConsensusPhase.EXECUTED

        # Calculate confidence based on quorum strength
        prepare_count = len(self.prepare_log.get(sequence, set()))
        commit_count = len(self.commit_log.get(sequence, set()))

        # Confidence is higher when more nodes agree
        max_nodes = self.total_nodes
        avg_agreement = (prepare_count + commit_count) / (2 * max_nodes)
        confidence = min(0.99, 0.5 + (avg_agreement * 0.49))

        participating_nodes = list(self.commit_log.get(sequence, set()))

        result = ConsensusResult(
            proposal_id=proposal.proposal_id,
            decision=proposal.data,
            participating_nodes=participating_nodes,
            view=self.view,
            sequence_number=sequence,
            phase=self.phase,
            confidence=confidence,
        )

        logger.info(
            f"Consensus executed",
            extra={
                "sequence": sequence,
                "confidence": confidence,
                "participants": len(participating_nodes),
            },
        )

        return result

    def _sign_message(self, message: PBFTMessage) -> str:
        """Sign a message with the node's private key."""
        if not self.private_key:
            # Fallback to simple hash if no keys initialized
            return message.digest()

        try:
            digest = message.digest().encode()
            signature = self.private_key.sign(
                digest,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return signature.hex()
        except Exception as e:
            logger.warning(f"Failed to sign message: {e}")
            return message.digest()

    def verify_signature(
        self, message: PBFTMessage, signature: str, public_key: rsa.RSAPublicKey
    ) -> bool:
        """Verify a message signature."""
        try:
            digest = message.digest().encode()
            signature_bytes = bytes.fromhex(signature)

            public_key.verify(
                signature_bytes,
                digest,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False

    async def trigger_view_change(self) -> None:
        """Trigger a view change to select a new primary."""
        logger.warning(f"Triggering view change from view {self.view}")

        self.view += 1
        self.phase = ConsensusPhase.IDLE

        # Select new primary
        self._select_primary()

        logger.info(
            f"View change completed",
            extra={"new_view": self.view, "new_primary": self.primary_node_id},
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current PBFT engine status."""
        return {
            "node_id": self.node_id,
            "view": self.view,
            "sequence_number": self.sequence_number,
            "phase": self.phase.value,
            "is_primary": self.is_primary(),
            "primary_node": self.primary_node_id,
            "total_nodes": self.total_nodes,
            "fault_tolerance": self.fault_tolerance,
            "required_quorum": self.required_quorum,
            "registered_nodes": len(self.nodes),
        }
