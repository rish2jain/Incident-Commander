"""
Tests for the Scaling Manager service.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime

from src.services.scaling_manager import (
    ScalingManager, 
    AgentReplica, 
    ScalingStrategy, 
    LoadBalancingStrategy,
    ScalingPolicy
)


class TestScalingManager:
    """Test scaling manager functionality."""
    
    @pytest.fixture
    def scaling_manager(self):
        """Create scaling manager for testing."""
        return ScalingManager()
    
    def test_scaling_manager_initialization(self, scaling_manager):
        """Test scaling manager initialization."""
        assert scaling_manager is not None
        assert len(scaling_manager.scaling_policies) == 5
        assert "detection" in scaling_manager.scaling_policies
        assert "diagnosis" in scaling_manager.scaling_policies
        assert "prediction" in scaling_manager.scaling_policies
        assert "resolution" in scaling_manager.scaling_policies
        assert "communication" in scaling_manager.scaling_policies
    
    def test_scaling_policy_configuration(self, scaling_manager):
        """Test scaling policy configuration."""
        detection_policy = scaling_manager.scaling_policies["detection"]
        assert detection_policy.min_replicas == 2
        assert detection_policy.max_replicas == 10
        assert detection_policy.target_utilization == 0.7
        assert detection_policy.scale_up_threshold == 0.8
        assert detection_policy.scale_down_threshold == 0.3
        assert detection_policy.cooldown_period == 300
    
    def test_agent_capacity_configuration(self, scaling_manager):
        """Test agent capacity configuration."""
        assert scaling_manager._get_agent_capacity("detection") == 20
        assert scaling_manager._get_agent_capacity("diagnosis") == 10
        assert scaling_manager._get_agent_capacity("prediction") == 15
        assert scaling_manager._get_agent_capacity("resolution") == 5
        assert scaling_manager._get_agent_capacity("communication") == 25
        assert scaling_manager._get_agent_capacity("unknown") == 10  # Default
    
    @pytest.mark.asyncio
    async def test_create_agent_replica(self, scaling_manager):
        """Test agent replica creation."""
        with patch.object(scaling_manager, '_deploy_replica', new_callable=AsyncMock):
            replica = await scaling_manager._create_agent_replica("detection", "us-east-1")
            
            assert replica.agent_type == "detection"
            assert replica.region == "us-east-1"
            assert replica.status == "healthy"
            assert replica.max_capacity == 20
            assert replica.current_load == 0
            assert replica.replica_id.startswith("detection-replica-")
    
    def test_load_balancing_strategies(self, scaling_manager):
        """Test load balancing strategy selection."""
        # Create test replicas
        replicas = [
            AgentReplica("replica-1", "detection", "us-east-1", "healthy", current_load=5, max_capacity=20),
            AgentReplica("replica-2", "detection", "us-west-2", "healthy", current_load=3, max_capacity=20),
            AgentReplica("replica-3", "detection", "eu-west-1", "healthy", current_load=8, max_capacity=20)
        ]
        
        # Test least connections
        selected = scaling_manager._select_least_connections(replicas)
        assert selected.replica_id == "replica-2"  # Lowest load (3)
        
        # Test round robin
        selected1 = scaling_manager._select_round_robin("detection", replicas)
        selected2 = scaling_manager._select_round_robin("detection", replicas)
        selected3 = scaling_manager._select_round_robin("detection", replicas)
        
        # Should cycle through replicas
        assert selected1 != selected2 or selected2 != selected3
    
    def test_geographic_load_balancing(self, scaling_manager):
        """Test geographic load balancing."""
        replicas = [
            AgentReplica("replica-1", "detection", "us-east-1", "healthy", current_load=5, max_capacity=20),
            AgentReplica("replica-2", "detection", "us-west-2", "healthy", current_load=3, max_capacity=20),
            AgentReplica("replica-3", "detection", "eu-west-1", "healthy", current_load=8, max_capacity=20)
        ]
        
        # Test with incident in us-east-1
        incident_data = {"region": "us-east-1", "severity": "medium"}
        selected = scaling_manager._select_geographic(replicas, incident_data)
        assert selected.region == "us-east-1"
        
        # Test with incident in unknown region (should fall back to least connections)
        incident_data = {"region": "ap-south-1", "severity": "medium"}
        selected = scaling_manager._select_geographic(replicas, incident_data)
        assert selected.replica_id == "replica-2"  # Least loaded
    
    def test_severity_based_load_balancing(self, scaling_manager):
        """Test severity-based load balancing."""
        replicas = [
            AgentReplica("replica-1", "detection", "us-east-1", "healthy", current_load=5, max_capacity=20, performance_score=0.8),
            AgentReplica("replica-2", "detection", "us-west-2", "healthy", current_load=3, max_capacity=20, performance_score=0.9),
            AgentReplica("replica-3", "detection", "eu-west-1", "healthy", current_load=8, max_capacity=20, performance_score=0.7)
        ]
        
        # Test with high severity incident (should prefer best performance)
        incident_data = {"severity": "critical"}
        selected = scaling_manager._select_by_severity(replicas, incident_data)
        assert selected.performance_score == 0.9  # Best performance
        
        # Test with low severity incident (should use least connections)
        incident_data = {"severity": "low"}
        selected = scaling_manager._select_by_severity(replicas, incident_data)
        assert selected.current_load == 3  # Least loaded
    
    @pytest.mark.asyncio
    async def test_replica_load_management(self, scaling_manager):
        """Test replica load assignment and release."""
        replica = AgentReplica("test-replica", "detection", "us-east-1", "healthy", max_capacity=10)
        
        # Test assignment
        await scaling_manager.assign_incident_to_replica(replica, "incident-1")
        assert replica.current_load == 1
        assert scaling_manager.metrics.load_distribution["test-replica"] == 1
        
        # Test release
        await scaling_manager.release_incident_from_replica(replica, "incident-1")
        assert replica.current_load == 0
        assert scaling_manager.metrics.load_distribution["test-replica"] == 0
    
    def test_utilization_calculation(self, scaling_manager):
        """Test agent utilization calculation."""
        # Set up test replicas
        scaling_manager.agent_replicas["detection"] = [
            AgentReplica("replica-1", "detection", "us-east-1", "healthy", current_load=8, max_capacity=10),
            AgentReplica("replica-2", "detection", "us-west-2", "healthy", current_load=6, max_capacity=10)
        ]
        
        # Calculate utilization: (8 + 6) / (10 + 10) = 14/20 = 0.7
        utilization = asyncio.run(scaling_manager._calculate_agent_utilization("detection"))
        assert utilization == 0.7
        
        # Test with no replicas
        utilization = asyncio.run(scaling_manager._calculate_agent_utilization("nonexistent"))
        assert utilization == 0.0
    
    def test_region_selection_for_scaling(self, scaling_manager):
        """Test region selection for new replicas."""
        # Set up replicas in different regions
        scaling_manager.agent_replicas["detection"] = [
            AgentReplica("replica-1", "detection", "us-east-1", "healthy"),
            AgentReplica("replica-2", "detection", "us-east-1", "healthy"),
            AgentReplica("replica-3", "detection", "us-west-2", "healthy")
        ]
        
        # Should select region with least replicas
        selected_region = scaling_manager._select_region_for_scaling()
        # Should prefer regions with fewer replicas (us-west-2, eu-west-1, or ap-southeast-1)
        assert selected_region in ["us-west-2", "eu-west-1", "ap-southeast-1"]
    
    @pytest.mark.asyncio
    async def test_incident_recording(self, scaling_manager):
        """Test incident recording for metrics."""
        initial_count = len(scaling_manager.incident_history)
        
        await scaling_manager.record_incident("test-incident-1")
        await scaling_manager.record_incident("test-incident-2")
        
        assert len(scaling_manager.incident_history) == initial_count + 2
    
    @pytest.mark.asyncio
    async def test_scaling_metrics(self, scaling_manager):
        """Test scaling metrics collection."""
        # Record some incidents
        await scaling_manager.record_incident("incident-1")
        await scaling_manager.record_incident("incident-2")
        
        metrics = await scaling_manager.get_scaling_metrics()
        
        assert hasattr(metrics, 'total_incidents_per_minute')
        assert hasattr(metrics, 'agent_utilization')
        assert hasattr(metrics, 'scaling_actions')
        assert hasattr(metrics, 'load_distribution')
        assert hasattr(metrics, 'cross_region_latency')
        assert hasattr(metrics, 'failover_events')
    
    @pytest.mark.asyncio
    async def test_replica_status(self, scaling_manager):
        """Test replica status reporting."""
        # Add test replica
        replica = AgentReplica("test-replica", "detection", "us-east-1", "healthy", current_load=5, max_capacity=10)
        scaling_manager.agent_replicas["detection"] = [replica]
        
        status = await scaling_manager.get_replica_status()
        
        assert "detection" in status
        assert len(status["detection"]) == 1
        
        replica_status = status["detection"][0]
        assert replica_status["replica_id"] == "test-replica"
        assert replica_status["region"] == "us-east-1"
        assert replica_status["status"] == "healthy"
        assert replica_status["current_load"] == 5
        assert replica_status["max_capacity"] == 10
        assert replica_status["utilization"] == 0.5
        assert replica_status["performance_score"] == 1.0


class TestScalingPolicyValidation:
    """Test scaling policy validation and edge cases."""
    
    def test_scaling_policy_creation(self):
        """Test scaling policy creation and validation."""
        policy = ScalingPolicy(
            min_replicas=2,
            max_replicas=10,
            target_utilization=0.7,
            scale_up_threshold=0.8,
            scale_down_threshold=0.3,
            cooldown_period=300
        )
        
        assert policy.min_replicas == 2
        assert policy.max_replicas == 10
        assert policy.target_utilization == 0.7
        assert policy.scale_up_threshold == 0.8
        assert policy.scale_down_threshold == 0.3
        assert policy.cooldown_period == 300
        assert policy.scale_up_increment == 1  # Default
        assert policy.scale_down_increment == 1  # Default
    
    def test_agent_replica_creation(self):
        """Test agent replica creation and validation."""
        replica = AgentReplica(
            replica_id="test-replica",
            agent_type="detection",
            region="us-east-1",
            status="healthy",
            current_load=5,
            max_capacity=20
        )
        
        assert replica.replica_id == "test-replica"
        assert replica.agent_type == "detection"
        assert replica.region == "us-east-1"
        assert replica.status == "healthy"
        assert replica.current_load == 5
        assert replica.max_capacity == 20
        assert isinstance(replica.last_health_check, datetime)
        assert replica.performance_score == 1.0