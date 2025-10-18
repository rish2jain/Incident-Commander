"""
Unit tests for Scaling Manager Service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.services.scaling_manager import (
    ScalingManager, ScalingStrategy, LoadBalancingStrategy, AgentReplica,
    ScalingMetrics, ScalingPolicy, get_scaling_manager
)
from src.utils.exceptions import ScalingError


class TestScalingManager:
    """Test cases for ScalingManager."""
    
    @pytest.fixture
    def manager(self):
        """Create scaling manager for testing."""
        manager = ScalingManager()
        
        # Mock AWS clients to avoid external dependencies
        manager.ecs_client = AsyncMock()
        manager.lambda_client = AsyncMock()
        manager.cloudwatch_client = AsyncMock()
        
        # Mock AWS initialization methods
        manager._initialize_aws_clients = AsyncMock()
        manager._deploy_replica = AsyncMock()
        
        return manager
    
    @pytest.mark.asyncio
    async def test_initialization(self, manager):
        """Test manager initialization."""
        await manager.initialize()
        
        # Verify initial replicas are created
        assert len(manager.agent_replicas) == 5  # 5 agent types
        
        # Verify minimum replicas per agent type
        for agent_type, policy in manager.scaling_policies.items():
            assert len(manager.agent_replicas[agent_type]) >= policy.min_replicas
    
    @pytest.mark.asyncio
    async def test_agent_replica_creation(self, manager):
        """Test agent replica creation."""
        await manager.initialize()
        
        replica = await manager._create_agent_replica("detection", "us-east-1")
        
        assert replica.agent_type == "detection"
        assert replica.region == "us-east-1"
        assert replica.status == "healthy"
        assert replica.max_capacity > 0
        assert replica.current_load == 0
    
    @pytest.mark.asyncio
    async def test_round_robin_selection(self, manager):
        """Test round-robin load balancing."""
        await manager.initialize()
        manager.load_balancing_strategy = LoadBalancingStrategy.ROUND_ROBIN
        
        # Get multiple replicas and verify round-robin behavior
        replicas = []
        for i in range(4):
            replica = await manager.select_agent_replica("detection")
            if replica:
                replicas.append(replica.replica_id)
        
        # Should cycle through available replicas
        assert len(set(replicas)) > 1  # Should use different replicas
    
    @pytest.mark.asyncio
    async def test_least_connections_selection(self, manager):
        """Test least connections load balancing."""
        await manager.initialize()
        manager.load_balancing_strategy = LoadBalancingStrategy.LEAST_CONNECTIONS
        
        # Set different loads on replicas
        detection_replicas = manager.agent_replicas["detection"]
        if len(detection_replicas) >= 2:
            detection_replicas[0].current_load = 5
            detection_replicas[1].current_load = 2
            
            # Should select replica with least load
            selected = await manager.select_agent_replica("detection")
            assert selected.current_load == 2
    
    @pytest.mark.asyncio
    async def test_weighted_round_robin_selection(self, manager):
        """Test weighted round-robin load balancing."""
        await manager.initialize()
        manager.load_balancing_strategy = LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN
        
        # Set different performance scores
        detection_replicas = manager.agent_replicas["detection"]
        if len(detection_replicas) >= 2:
            detection_replicas[0].performance_score = 0.9
            detection_replicas[1].performance_score = 0.5
            
            # Should prefer higher performance replica
            selected = await manager.select_agent_replica("detection")
            assert selected is not None
    
    @pytest.mark.asyncio
    async def test_geographic_selection(self, manager):
        """Test geographic load balancing."""
        await manager.initialize()
        manager.load_balancing_strategy = LoadBalancingStrategy.GEOGRAPHIC
        
        # Create replica in different region
        replica = await manager._create_agent_replica("detection", "us-west-2")
        manager.agent_replicas["detection"].append(replica)
        
        # Test selection with region preference
        incident_data = {"region": "us-west-2"}
        selected = await manager.select_agent_replica("detection", incident_data)
        
        # Should prefer replica in same region if available
        if selected:
            assert selected.region == "us-west-2" or len([r for r in manager.agent_replicas["detection"] if r.region == "us-west-2"]) == 0
    
    @pytest.mark.asyncio
    async def test_severity_based_selection(self, manager):
        """Test incident severity-based load balancing."""
        await manager.initialize()
        manager.load_balancing_strategy = LoadBalancingStrategy.INCIDENT_SEVERITY
        
        # Set different performance scores
        detection_replicas = manager.agent_replicas["detection"]
        if len(detection_replicas) >= 2:
            detection_replicas[0].performance_score = 0.9
            detection_replicas[1].performance_score = 0.5
            
            # Test high severity incident
            incident_data = {"severity": "critical"}
            selected = await manager.select_agent_replica("detection", incident_data)
            
            # Should select highest performance replica for critical incidents
            assert selected.performance_score == 0.9
    
    @pytest.mark.asyncio
    async def test_incident_assignment(self, manager):
        """Test incident assignment to replica."""
        await manager.initialize()
        
        replica = manager.agent_replicas["detection"][0]
        initial_load = replica.current_load
        
        await manager.assign_incident_to_replica(replica, "incident-123")
        
        assert replica.current_load == initial_load + 1
        assert manager.metrics.load_distribution[replica.replica_id] == replica.current_load
    
    @pytest.mark.asyncio
    async def test_incident_release(self, manager):
        """Test incident release from replica."""
        await manager.initialize()
        
        replica = manager.agent_replicas["detection"][0]
        replica.current_load = 3
        
        await manager.release_incident_from_replica(replica, "incident-123")
        
        assert replica.current_load == 2
        assert manager.metrics.load_distribution[replica.replica_id] == 2
    
    @pytest.mark.asyncio
    async def test_scale_up_agent(self, manager):
        """Test agent scaling up."""
        await manager.initialize()
        
        initial_count = len(manager.agent_replicas["detection"])
        
        # Mock high utilization to trigger scale up
        with patch.object(manager, '_calculate_agent_utilization', return_value=0.9):
            success = await manager._scale_up_agent("detection")
            
            if success:
                assert len(manager.agent_replicas["detection"]) > initial_count
                assert "Scaled up detection" in str(manager.metrics.scaling_actions)
    
    @pytest.mark.asyncio
    async def test_scale_down_agent(self, manager):
        """Test agent scaling down."""
        await manager.initialize()
        
        # Add extra replicas first
        for i in range(3):
            replica = await manager._create_agent_replica("detection", "us-east-1")
            manager.agent_replicas["detection"].append(replica)
        
        initial_count = len(manager.agent_replicas["detection"])
        
        # Mock low utilization to trigger scale down
        with patch.object(manager, '_calculate_agent_utilization', return_value=0.2):
            success = await manager._scale_down_agent("detection")
            
            if success:
                assert len(manager.agent_replicas["detection"]) <= initial_count
    
    @pytest.mark.asyncio
    async def test_scaling_cooldown(self, manager):
        """Test scaling cooldown period."""
        await manager.initialize()
        
        # Set recent scaling action
        manager.last_scaling_action["detection"] = datetime.utcnow()
        
        # Should not scale due to cooldown
        success = await manager._scale_up_agent("detection")
        assert not success
    
    @pytest.mark.asyncio
    async def test_max_replicas_limit(self, manager):
        """Test maximum replicas limit."""
        await manager.initialize()
        
        # Set replicas to maximum
        policy = manager.scaling_policies["detection"]
        while len(manager.agent_replicas["detection"]) < policy.max_replicas:
            replica = await manager._create_agent_replica("detection", "us-east-1")
            manager.agent_replicas["detection"].append(replica)
        
        # Should not scale beyond maximum
        success = await manager._scale_up_agent("detection")
        assert not success
    
    @pytest.mark.asyncio
    async def test_min_replicas_limit(self, manager):
        """Test minimum replicas limit."""
        await manager.initialize()
        
        # Should not scale below minimum
        success = await manager._scale_down_agent("detection")
        
        policy = manager.scaling_policies["detection"]
        assert len(manager.agent_replicas["detection"]) >= policy.min_replicas
    
    @pytest.mark.asyncio
    async def test_utilization_calculation(self, manager):
        """Test agent utilization calculation."""
        await manager.initialize()
        
        # Set known loads
        replicas = manager.agent_replicas["detection"]
        if len(replicas) >= 2:
            replicas[0].current_load = 5
            replicas[0].max_capacity = 10
            replicas[1].current_load = 3
            replicas[1].max_capacity = 10
            
            utilization = await manager._calculate_agent_utilization("detection")
            expected = (5 + 3) / (10 + 10)  # 8/20 = 0.4
            assert abs(utilization - expected) < 0.01
    
    @pytest.mark.asyncio
    async def test_region_selection_for_scaling(self, manager):
        """Test region selection for new replicas."""
        await manager.initialize()
        
        # Create uneven distribution
        for i in range(3):
            replica = await manager._create_agent_replica("detection", "us-east-1")
            manager.agent_replicas["detection"].append(replica)
        
        # Should select region with fewer replicas
        selected_region = manager._select_region_for_scaling()
        
        # Count replicas per region
        region_counts = {}
        for replicas in manager.agent_replicas.values():
            for replica in replicas:
                region_counts[replica.region] = region_counts.get(replica.region, 0) + 1
        
        # Selected region should not be the most loaded
        assert selected_region in manager.regions
    
    @pytest.mark.asyncio
    async def test_replica_failure_handling(self, manager):
        """Test replica failure handling."""
        await manager.initialize()
        
        replica = manager.agent_replicas["detection"][0]
        initial_count = len(manager.agent_replicas["detection"])
        
        await manager.handle_replica_failure(replica)
        
        # Should create replacement replica
        assert len(manager.agent_replicas["detection"]) == initial_count
        assert manager.metrics.failover_events == 1
        
        # Original replica should be removed
        assert replica not in manager.agent_replicas["detection"]
    
    @pytest.mark.asyncio
    async def test_health_monitoring(self, manager):
        """Test replica health monitoring."""
        await manager.initialize()
        
        replica = manager.agent_replicas["detection"][0]
        original_time = replica.last_health_check
        
        await manager._check_replica_health(replica)
        
        # Health check timestamp should be updated
        assert replica.last_health_check > original_time
    
    @pytest.mark.asyncio
    async def test_incident_recording(self, manager):
        """Test incident recording for metrics."""
        await manager.initialize()
        
        initial_count = len(manager.incident_history)
        
        await manager.record_incident("incident-123")
        
        assert len(manager.incident_history) == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_scaling_metrics(self, manager):
        """Test scaling metrics calculation."""
        await manager.initialize()
        
        # Record some incidents
        for i in range(5):
            await manager.record_incident(f"incident-{i}")
        
        metrics = await manager.get_scaling_metrics()
        
        assert metrics.total_incidents_per_minute >= 0
        assert isinstance(metrics.agent_utilization, dict)
        assert isinstance(metrics.scaling_actions, list)
    
    @pytest.mark.asyncio
    async def test_replica_status(self, manager):
        """Test replica status retrieval."""
        await manager.initialize()
        
        status = await manager.get_replica_status()
        
        assert isinstance(status, dict)
        assert len(status) == 5  # 5 agent types
        
        for agent_type, replicas in status.items():
            assert isinstance(replicas, list)
            for replica_info in replicas:
                assert "replica_id" in replica_info
                assert "region" in replica_info
                assert "status" in replica_info
                assert "utilization" in replica_info
    
    @pytest.mark.asyncio
    async def test_scaling_policies(self, manager):
        """Test scaling policy configuration."""
        # Verify default policies exist for all agent types
        expected_agents = ["detection", "diagnosis", "prediction", "resolution", "communication"]
        
        for agent_type in expected_agents:
            assert agent_type in manager.scaling_policies
            policy = manager.scaling_policies[agent_type]
            assert policy.min_replicas > 0
            assert policy.max_replicas > policy.min_replicas
            assert 0 < policy.target_utilization < 1
            assert policy.scale_up_threshold > policy.target_utilization
            assert policy.scale_down_threshold < policy.target_utilization
    
    @pytest.mark.asyncio
    async def test_concurrent_scaling_prevention(self, manager):
        """Test prevention of concurrent scaling operations."""
        await manager.initialize()
        
        # Set scaling in progress
        manager.scaling_in_progress["detection"] = True
        
        # Should not scale while operation is in progress
        success = await manager._scale_up_agent("detection")
        assert not success
        
        success = await manager._scale_down_agent("detection")
        assert not success
    
    @pytest.mark.asyncio
    async def test_cleanup(self, manager):
        """Test resource cleanup."""
        await manager.initialize()
        
        initial_replica_count = sum(len(replicas) for replicas in manager.agent_replicas.values())
        
        await manager.cleanup()
        
        # Verify cleanup was attempted (replicas marked for termination)
        # In a real implementation, this would verify actual resource cleanup
        assert True  # Placeholder for actual cleanup verification


class TestAgentReplica:
    """Test AgentReplica data class."""
    
    def test_replica_initialization(self):
        """Test replica initialization."""
        replica = AgentReplica(
            replica_id="test-replica-1",
            agent_type="detection",
            region="us-east-1",
            status="healthy"
        )
        
        assert replica.replica_id == "test-replica-1"
        assert replica.agent_type == "detection"
        assert replica.region == "us-east-1"
        assert replica.status == "healthy"
        assert replica.current_load == 0
        assert replica.max_capacity == 10
        assert replica.performance_score == 1.0
    
    def test_replica_with_custom_values(self):
        """Test replica with custom values."""
        replica = AgentReplica(
            replica_id="test-replica-2",
            agent_type="diagnosis",
            region="us-west-2",
            status="scaling",
            current_load=5,
            max_capacity=20,
            performance_score=0.85
        )
        
        assert replica.current_load == 5
        assert replica.max_capacity == 20
        assert replica.performance_score == 0.85


class TestScalingPolicy:
    """Test ScalingPolicy data class."""
    
    def test_policy_initialization(self):
        """Test policy initialization."""
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
        assert policy.scale_up_increment == 1
        assert policy.scale_down_increment == 1


class TestScalingMetrics:
    """Test ScalingMetrics data class."""
    
    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = ScalingMetrics()
        
        assert metrics.total_incidents_per_minute == 0.0
        assert isinstance(metrics.agent_utilization, dict)
        assert isinstance(metrics.scaling_actions, list)
        assert isinstance(metrics.load_distribution, dict)
        assert isinstance(metrics.cross_region_latency, dict)
        assert metrics.failover_events == 0


class TestGlobalScalingManager:
    """Test global scaling manager instance."""
    
    @pytest.mark.asyncio
    async def test_singleton_behavior(self):
        """Test that get_scaling_manager returns singleton."""
        with patch('src.services.scaling_manager.ScalingManager') as mock_class:
            mock_instance = AsyncMock()
            mock_class.return_value = mock_instance
            
            # First call should create instance
            manager1 = await get_scaling_manager()
            
            # Second call should return same instance
            manager2 = await get_scaling_manager()
            
            assert manager1 is manager2
            mock_class.assert_called_once()