"""
Comprehensive tests for Byzantine Fault-Tolerant Consensus.
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from src.services.byzantine_consensus import (
    ByzantineFaultTolerantConsensus,
    PBFTMessage,
    MessageType,
    NodeState,
    ConsensusRound
)
from src.models.incident import Incident
from src.models.agent import AgentRecommendation
from src.utils.exceptions import ByzantineConsensusError


@pytest.fixture
def pbft_engine():
    """Create a PBFT engine for testing."""
    return ByzantineFaultTolerantConsensus("test_node", 4)  # 4 nodes, can tolerate 1 Byzantine


@pytest.fixture
def mock_incident():
    """Create a mock incident for testing."""
    incident = Mock(spec=Incident)
    incident.id = "test_incident_123"
    incident.title = "Test Database Failure"
    incident.severity = "high"
    return incident


@pytest.fixture
def mock_recommendation():
    """Create a mock agent recommendation."""
    recommendation = Mock(spec=AgentRecommendation)
    recommendation.incident_id = "test_incident_123"
    recommendation.action_id = "restart_database"
    recommendation.action_type = "restart_service"
    recommendation.confidence = 0.9
    recommendation.agent_name = "diagnosis_agent"
    return recommendation


class TestByzantineFaultTolerantConsensus:
    """Test Byzantine fault-tolerant consensus implementation."""
    
    def test_initialization(self, pbft_engine):
        """Test PBFT engine initialization."""
        assert pbft_engine.node_id == "test_node"
        assert pbft_engine.total_nodes == 4
        assert pbft_engine.fault_tolerance == 1  # (4-1)//3 = 1
        assert pbft_engine.quorum_size == 3  # 2*1+1 = 3
        assert pbft_engine.current_view == 0
        assert pbft_engine.sequence_number == 0
    
    def test_node_registration(self, pbft_engine):
        """Test node registration."""
        public_key = b"test_public_key"
        pbft_engine.register_node("node_1", public_key)
        
        assert "node_1" in pbft_engine.nodes
        assert pbft_engine.nodes["node_1"].public_key == public_key
        assert pbft_engine.nodes["node_1"].state == NodeState.NORMAL
    
    def test_digest_calculation(self, pbft_engine, mock_recommendation):
        """Test digest calculation for recommendations."""
        digest1 = pbft_engine._calculate_digest(mock_recommendation)
        digest2 = pbft_engine._calculate_digest(mock_recommendation)
        
        # Same recommendation should produce same digest
        assert digest1 == digest2
        assert len(digest1) == 64  # SHA256 hex digest
    
    def test_message_signing_and_verification(self, pbft_engine):
        """Test message signing and verification."""
        # Register our own node
        public_key_bytes = pbft_engine.public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        pbft_engine.register_node(pbft_engine.node_id, public_key_bytes)
        
        # Create a test message
        message = PBFTMessage(
            message_type=MessageType.PREPARE,
            view=0,
            sequence=1,
            digest="test_digest",
            node_id=pbft_engine.node_id,
            timestamp=datetime.utcnow(),
            payload={"test": "data"}
        )
        
        # Sign the message
        signature = pbft_engine._sign_message(message)
        message.signature = signature
        
        # Verify the signature
        assert pbft_engine._verify_signature(message) == True
    
    def test_primary_calculation(self, pbft_engine):
        """Test primary node calculation."""
        # Register some nodes
        nodes = ["node_1", "node_2", "node_3", "node_4"]
        for node in nodes:
            pbft_engine.register_node(node, b"key")
        
        # Primary should be deterministic based on view
        primary_0 = pbft_engine._calculate_primary(0)
        primary_1 = pbft_engine._calculate_primary(1)
        
        assert primary_0 in nodes
        assert primary_1 in nodes
        assert primary_0 != primary_1  # Different views should have different primaries
    
    @pytest.mark.asyncio
    async def test_suspicious_behavior_detection(self, pbft_engine):
        """Test Byzantine behavior detection."""
        node_id = "suspicious_node"
        pbft_engine.register_node(node_id, b"key")
        
        # Record multiple suspicious behaviors
        for _ in range(3):
            await pbft_engine._record_suspicious_behavior(node_id, "invalid_signature")
        
        # Node should be isolated
        assert node_id in pbft_engine.isolated_nodes
        assert pbft_engine.nodes[node_id].state == NodeState.ISOLATED
        assert pbft_engine.byzantine_detections == 1
    
    @pytest.mark.asyncio
    async def test_pre_prepare_handling(self, pbft_engine, mock_incident, mock_recommendation):
        """Test pre-prepare message handling."""
        # Set up as non-primary node
        pbft_engine.register_node("primary_node", b"primary_key")
        pbft_engine.primary_node = "primary_node"
        
        # Create pre-prepare message
        digest = pbft_engine._calculate_digest(mock_recommendation)
        pre_prepare_msg = PBFTMessage(
            message_type=MessageType.PRE_PREPARE,
            view=0,
            sequence=1,
            digest=digest,
            node_id="primary_node",
            timestamp=datetime.utcnow(),
            payload={
                "incident_id": mock_incident.id,
                "recommendation": str(mock_recommendation)
            }
        )
        
        # Mock signature verification to return True
        pbft_engine._verify_signature = Mock(return_value=True)
        pbft_engine._broadcast_message = AsyncMock()
        
        # Handle the message
        result = await pbft_engine._handle_pre_prepare(pre_prepare_msg)
        
        # Should create consensus round and broadcast prepare
        assert 1 in pbft_engine.active_rounds
        assert pbft_engine._broadcast_message.called
    
    @pytest.mark.asyncio
    async def test_prepare_message_handling(self, pbft_engine):
        """Test prepare message handling."""
        # Set up consensus round
        round_info = ConsensusRound(
            sequence=1,
            view=0,
            proposal=Mock(),
            digest="test_digest"
        )
        pbft_engine.active_rounds[1] = round_info
        
        # Create prepare message
        prepare_msg = PBFTMessage(
            message_type=MessageType.PREPARE,
            view=0,
            sequence=1,
            digest="test_digest",
            node_id="node_1",
            timestamp=datetime.utcnow(),
            payload={}
        )
        
        # Mock dependencies
        pbft_engine._verify_signature = Mock(return_value=True)
        pbft_engine._broadcast_message = AsyncMock()
        pbft_engine.register_node("node_1", b"key")
        
        # Handle the message
        await pbft_engine._handle_prepare(prepare_msg)
        
        # Should store the prepare message
        assert "node_1" in round_info.prepare_msgs
    
    @pytest.mark.asyncio
    async def test_commit_message_handling(self, pbft_engine):
        """Test commit message handling and consensus completion."""
        # Set up consensus round
        mock_proposal = Mock()
        mock_proposal.incident_id = "test_incident"
        mock_proposal.action_id = "test_action"
        mock_proposal.action_type = "test_type"
        
        round_info = ConsensusRound(
            sequence=1,
            view=0,
            proposal=mock_proposal,
            digest="test_digest"
        )
        pbft_engine.active_rounds[1] = round_info
        
        # Add enough commit messages to reach consensus
        for i in range(pbft_engine.quorum_size):
            node_id = f"node_{i}"
            pbft_engine.register_node(node_id, b"key")
            
            commit_msg = PBFTMessage(
                message_type=MessageType.COMMIT,
                view=0,
                sequence=1,
                digest="test_digest",
                node_id=node_id,
                timestamp=datetime.utcnow(),
                payload={}
            )
            
            round_info.commit_msgs[node_id] = commit_msg
        
        # Mock signature verification
        pbft_engine._verify_signature = Mock(return_value=True)
        
        # Handle final commit message
        final_commit = PBFTMessage(
            message_type=MessageType.COMMIT,
            view=0,
            sequence=1,
            digest="test_digest",
            node_id="final_node",
            timestamp=datetime.utcnow(),
            payload={}
        )
        pbft_engine.register_node("final_node", b"key")
        
        result = await pbft_engine._handle_commit(final_commit)
        
        # Should reach consensus
        assert result is not None
        assert result.consensus_method == "pbft"
        assert result.final_confidence == 1.0
        assert round_info.decided == True
        assert 1 not in pbft_engine.active_rounds  # Should be moved to completed
    
    @pytest.mark.asyncio
    async def test_malicious_message_rejection(self, pbft_engine):
        """Test rejection of malicious messages."""
        # Register a node
        pbft_engine.register_node("malicious_node", b"key")
        
        # Create message with invalid signature
        malicious_msg = PBFTMessage(
            message_type=MessageType.PREPARE,
            view=0,
            sequence=1,
            digest="fake_digest",
            node_id="malicious_node",
            timestamp=datetime.utcnow(),
            payload={},
            signature=b"fake_signature"
        )
        
        # Mock signature verification to fail
        pbft_engine._verify_signature = Mock(return_value=False)
        pbft_engine._record_suspicious_behavior = AsyncMock()
        
        # Handle the message
        result = await pbft_engine.handle_message(malicious_msg)
        
        # Should reject message and record suspicious behavior
        assert result is None
        pbft_engine._record_suspicious_behavior.assert_called_with(
            "malicious_node", "invalid_signature"
        )
    
    @pytest.mark.asyncio
    async def test_consensus_timeout(self, pbft_engine, mock_incident, mock_recommendation):
        """Test consensus timeout handling."""
        # Set as primary
        pbft_engine.primary_node = pbft_engine.node_id
        
        # Mock broadcast to do nothing (simulate network partition)
        pbft_engine._broadcast_message = AsyncMock()
        
        # Attempt consensus with very short timeout
        with pytest.raises(ByzantineConsensusError, match="Consensus timeout"):
            await asyncio.wait_for(
                pbft_engine.propose_action(mock_incident, mock_recommendation),
                timeout=0.1
            )
    
    def test_metrics_collection(self, pbft_engine):
        """Test metrics collection."""
        # Add some test data
        pbft_engine.byzantine_detections = 2
        pbft_engine.view_changes = 1
        pbft_engine.consensus_times = [0.5, 0.3, 0.7]
        pbft_engine.isolated_nodes.add("bad_node")
        
        metrics = pbft_engine.get_metrics()
        
        assert metrics["node_id"] == "test_node"
        assert metrics["byzantine_detections"] == 2
        assert metrics["view_changes"] == 1
        assert metrics["average_consensus_time_ms"] == 500.0  # (0.5+0.3+0.7)/3 * 1000
        assert "bad_node" in metrics["isolated_nodes"]
    
    @pytest.mark.asyncio
    async def test_view_change_on_primary_isolation(self, pbft_engine):
        """Test view change when primary is isolated."""
        # Set up nodes
        nodes = ["node_1", "node_2", "node_3"]
        for node in nodes:
            pbft_engine.register_node(node, b"key")
        
        # Set primary
        pbft_engine.primary_node = "node_1"
        original_view = pbft_engine.current_view
        
        # Isolate the primary
        await pbft_engine._isolate_byzantine_node("node_1")
        
        # Should trigger view change
        assert pbft_engine.current_view == original_view + 1
        assert pbft_engine.primary_node != "node_1"
    
    @pytest.mark.asyncio
    async def test_fault_tolerance_limits(self, pbft_engine):
        """Test that system handles up to f Byzantine nodes correctly."""
        # With 4 nodes, can tolerate 1 Byzantine node
        assert pbft_engine.fault_tolerance == 1
        
        # Isolate 1 node (at the limit)
        pbft_engine.register_node("byzantine_1", b"key")
        await pbft_engine._isolate_byzantine_node("byzantine_1")
        
        # System should still be operational
        assert len(pbft_engine.isolated_nodes) == 1
        assert len(pbft_engine.nodes) - len(pbft_engine.isolated_nodes) >= pbft_engine.quorum_size
        
        # Isolating another node would break the system
        # (This would be tested in integration tests with actual consensus attempts)


class TestPBFTIntegration:
    """Integration tests for PBFT with the rest of the system."""
    
    @pytest.mark.asyncio
    async def test_full_consensus_flow(self):
        """Test complete PBFT consensus flow with multiple nodes."""
        # This would be a more complex integration test
        # involving multiple PBFT engines communicating
        pass
    
    @pytest.mark.asyncio
    async def test_byzantine_attack_scenarios(self):
        """Test various Byzantine attack scenarios."""
        # Test scenarios like:
        # - Conflicting messages from same node
        # - Messages with wrong view/sequence
        # - Delayed messages
        # - Corrupted message content
        pass