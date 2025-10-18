"""
Tests for Fault Tolerance Showcase

Task 12.5: Interactive fault tolerance showcase testing
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.services.fault_tolerance_showcase import (
    FaultToleranceShowcase,
    FaultType,
    CircuitBreakerState,
    get_fault_tolerance_showcase
)


class TestFaultToleranceShowcase:
    """Test fault tolerance showcase functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.showcase = FaultToleranceShowcase()
        
    def test_initialize_circuit_breakers(self):
        """Test circuit breaker initialization."""
        assert len(self.showcase.circuit_breakers) == 12
        
        # Check specific services
        assert "bedrock_api" in self.showcase.circuit_breakers
        assert "detection_agent" in self.showcase.circuit_breakers
        assert "dynamodb" in self.showcase.circuit_breakers
        
        # Verify initial state
        for cb in self.showcase.circuit_breakers.values():
            assert cb.state == CircuitBreakerState.CLOSED
            assert cb.failure_count == 0
            assert cb.health_score == 1.0
            
    def test_initialize_agent_health(self):
        """Test agent health initialization."""
        assert len(self.showcase.agent_health) == 5
        
        agents = ["detection", "diagnosis", "prediction", "resolution", "communication"]
        for agent in agents:
            assert agent in self.showcase.agent_health
            health = self.showcase.agent_health[agent]
            assert health.is_healthy is True
            assert health.error_rate == 0.0
            assert 0.85 <= health.confidence_score <= 0.95
            
    def test_get_circuit_breaker_dashboard(self):
        """Test circuit breaker dashboard generation."""
        dashboard = self.showcase.get_circuit_breaker_dashboard()
        
        assert "circuit_breaker_dashboard" in dashboard
        assert "system_overview" in dashboard
        assert "real_time_features" in dashboard
        
        # Check system overview
        overview = dashboard["system_overview"]
        assert overview["total_services"] == 12
        assert overview["healthy_services"] == 12
        assert overview["system_health_percentage"] == 100.0
        assert overview["overall_status"] == "excellent"
        
        # Check real-time features
        features = dashboard["real_time_features"]
        assert features["live_state_transitions"] is True
        assert features["automatic_recovery_tracking"] is True
        
    @pytest.mark.asyncio
    async def test_inject_chaos_fault_agent_failure(self):
        """Test chaos fault injection for agent failure."""
        experiment_id = await self.showcase.inject_chaos_fault(
            judge_id="test_judge",
            fault_type=FaultType.AGENT_FAILURE,
            target_component="detection",
            duration_seconds=30,
            intensity=0.5
        )
        
        assert experiment_id.startswith("chaos_agent_failure_detection_")
        assert experiment_id in self.showcase.active_experiments
        
        # Check experiment details
        experiment = self.showcase.active_experiments[experiment_id]
        assert experiment.fault_type == FaultType.AGENT_FAILURE
        assert experiment.target_component == "detection"
        assert experiment.duration_seconds == 30
        assert experiment.intensity == 0.5
        
        # Check agent health impact
        agent_health = self.showcase.agent_health["detection"]
        assert agent_health.is_healthy is False
        assert agent_health.error_rate == 0.5
        assert agent_health.failure_reason is not None
        
    @pytest.mark.asyncio
    async def test_inject_chaos_fault_network_partition(self):
        """Test chaos fault injection for network partition."""
        experiment_id = await self.showcase.inject_chaos_fault(
            judge_id="test_judge",
            fault_type=FaultType.NETWORK_PARTITION,
            target_component="consensus_network",
            duration_seconds=60,
            intensity=0.8
        )
        
        assert experiment_id.startswith("chaos_network_partition_consensus_network_")
        
        # Check network partition creation
        assert len(self.showcase.network_partitions) > 0
        
        # Get the partition
        partition_id = list(self.showcase.network_partitions.keys())[0]
        partition = self.showcase.network_partitions[partition_id]
        
        assert partition.affected_agents == ["detection", "diagnosis", "prediction"]
        assert partition.partition_duration_seconds == 60
        
    def test_get_fault_recovery_visualization(self):
        """Test fault recovery visualization."""
        # First create an experiment
        experiment_id = "test_experiment_123"
        from src.services.fault_tolerance_showcase import ChaosExperiment
        
        experiment = ChaosExperiment(
            experiment_id=experiment_id,
            fault_type=FaultType.AGENT_FAILURE,
            target_component="detection",
            duration_seconds=60,
            intensity=0.5,
            start_time=datetime.utcnow(),
            end_time=None,
            recovery_observed=False,
            impact_metrics={}
        )
        
        self.showcase.active_experiments[experiment_id] = experiment
        
        # Get recovery visualization
        recovery_viz = self.showcase.get_fault_recovery_visualization(experiment_id)
        
        assert recovery_viz["experiment_id"] == experiment_id
        assert "fault_recovery_visualization" in recovery_viz
        assert "recovery_mechanisms" in recovery_viz
        assert "system_resilience_metrics" in recovery_viz
        assert "visual_indicators" in recovery_viz
        
        # Check fault recovery details
        fault_viz = recovery_viz["fault_recovery_visualization"]
        assert fault_viz["fault_type"] == "agent_failure"
        assert fault_viz["target_component"] == "detection"
        assert fault_viz["fault_intensity"] == "50%"
        
    def test_get_network_partition_demonstration(self):
        """Test network partition demonstration."""
        # First create a partition
        partition_id = "test_partition_123"
        from src.services.fault_tolerance_showcase import NetworkPartitionSimulation
        
        partition = NetworkPartitionSimulation(
            partition_id=partition_id,
            affected_agents=["detection", "diagnosis"],
            partition_start=datetime.utcnow(),
            partition_duration_seconds=120,
            healing_in_progress=False,
            state_consistency_issues=["Test consistency issue"],
            recovery_actions=["Test recovery action"]
        )
        
        self.showcase.network_partitions[partition_id] = partition
        
        # Get partition demonstration
        demo = self.showcase.get_network_partition_demonstration(partition_id)
        
        assert demo["partition_id"] == partition_id
        assert "network_partition_demonstration" in demo
        assert "partition_tolerance_features" in demo
        assert "cap_theorem_demonstration" in demo
        assert "recovery_timeline" in demo
        
        # Check CAP theorem demonstration
        cap_demo = demo["cap_theorem_demonstration"]
        assert cap_demo["consistency"] == "Eventually consistent after partition healing"
        assert cap_demo["availability"] == "Maintained for non-partitioned operations"
        assert cap_demo["partition_tolerance"] == "System continues operating during network splits"
        
    def test_get_comprehensive_fault_tolerance_report(self):
        """Test comprehensive fault tolerance report."""
        report = self.showcase.get_comprehensive_fault_tolerance_report()
        
        assert "fault_tolerance_showcase_report" in report
        assert "fault_tolerance_capabilities" in report
        assert "judge_interaction_features" in report
        
        # Check showcase report
        showcase_report = report["fault_tolerance_showcase_report"]
        assert "circuit_breaker_status" in showcase_report
        assert "active_chaos_experiments" in showcase_report
        assert "active_network_partitions" in showcase_report
        assert "system_resilience_summary" in showcase_report
        
        # Check capabilities
        capabilities = report["fault_tolerance_capabilities"]
        assert capabilities["circuit_breaker_protection"] == "Automatic failure detection and isolation"
        assert capabilities["self_healing"] == "Automatic recovery without human intervention"
        assert capabilities["partition_tolerance"] == "Continued operation during network splits"
        
    def test_calculate_resilience_score(self):
        """Test resilience score calculation."""
        # Test with healthy system
        score = self.showcase._calculate_resilience_score()
        assert score == 1.0  # All services healthy, no experiments
        
        # Add an experiment to test penalty
        from src.services.fault_tolerance_showcase import ChaosExperiment
        experiment = ChaosExperiment(
            experiment_id="test_exp",
            fault_type=FaultType.AGENT_FAILURE,
            target_component="detection",
            duration_seconds=60,
            intensity=0.5,
            start_time=datetime.utcnow(),
            end_time=None,
            recovery_observed=False,
            impact_metrics={}
        )
        self.showcase.active_experiments["test_exp"] = experiment
        
        # Score should be lower due to active experiment
        score_with_experiment = self.showcase._calculate_resilience_score()
        assert score_with_experiment < 1.0
        assert score_with_experiment >= 0.0
        
    def test_fault_type_enum(self):
        """Test fault type enumeration."""
        expected_fault_types = [
            "agent_failure",
            "network_partition", 
            "service_timeout",
            "memory_pressure",
            "cpu_overload",
            "database_failure",
            "external_api_failure"
        ]
        
        actual_fault_types = [ft.value for ft in FaultType]
        assert set(actual_fault_types) == set(expected_fault_types)
        
    def test_circuit_breaker_state_enum(self):
        """Test circuit breaker state enumeration."""
        expected_states = ["closed", "open", "half_open"]
        actual_states = [state.value for state in CircuitBreakerState]
        assert set(actual_states) == set(expected_states)
        
    def test_error_handling_invalid_experiment(self):
        """Test error handling for invalid experiment ID."""
        with pytest.raises(ValueError, match="Experiment invalid_id not found"):
            self.showcase.get_fault_recovery_visualization("invalid_id")
            
    def test_error_handling_invalid_partition(self):
        """Test error handling for invalid partition ID."""
        with pytest.raises(ValueError, match="Network partition invalid_id not found"):
            self.showcase.get_network_partition_demonstration("invalid_id")


class TestFaultToleranceShowcaseGlobalInstance:
    """Test global fault tolerance showcase instance."""
    
    def test_get_fault_tolerance_showcase_singleton(self):
        """Test that get_fault_tolerance_showcase returns singleton instance."""
        showcase1 = get_fault_tolerance_showcase()
        showcase2 = get_fault_tolerance_showcase()
        
        assert showcase1 is showcase2
        assert isinstance(showcase1, FaultToleranceShowcase)


if __name__ == "__main__":
    pytest.main([__file__])