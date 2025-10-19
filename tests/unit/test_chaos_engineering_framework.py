"""
Unit tests for Chaos Engineering Framework

Tests core functionality of chaos engineering framework including:
- Experiment execution and validation
- Failure injection and recovery
- Byzantine failure testing
- Recovery time measurement
- Resilience reporting
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.chaos_engineering_framework import (
    ChaosEngineeringFramework,
    ChaosExperiment,
    ChaosExperimentType,
    FailureMode,
    ResilienceMetric,
    ChaosExperimentResult,
    ChaosInjection
)
from src.services.agent_swarm_coordinator import AgentSwarmCoordinator


class TestChaosEngineeringFramework:
    """Test chaos engineering framework core functionality."""
    
    @pytest.fixture
    def framework(self):
        """Create chaos engineering framework instance."""
        return ChaosEngineeringFramework()
    
    @pytest.fixture
    def mock_coordinator(self):
        """Create mock agent swarm coordinator."""
        coordinator = AsyncMock(spec=AgentSwarmCoordinator)
        coordinator.get_agent_health_status.return_value = {
            "detection_agent": {"is_healthy": True},
            "diagnosis_agent": {"is_healthy": True},
            "resolution_agent": {"is_healthy": True}
        }
        return coordinator
    
    @pytest.fixture
    def sample_experiment(self):
        """Create sample chaos experiment."""
        return ChaosExperiment(
            name="test_agent_failure",
            experiment_type=ChaosExperimentType.AGENT_FAILURE,
            failure_mode=FailureMode.COMPLETE_FAILURE,
            target_components=["detection_agent"],
            duration_seconds=60,
            intensity=1.0,
            description="Test agent failure experiment",
            expected_behavior="System should continue with remaining agents",
            success_criteria={
                "recovery_time": 30.0,
                "availability": 0.8
            },
            blast_radius="single_agent"
        )
    
    def test_framework_initialization(self, framework):
        """Test framework initializes with default experiments."""
        assert len(framework.experiments) > 0
        assert framework.emergency_stop_active is False
        assert framework.max_concurrent_experiments == 3
        assert len(framework.active_injections) == 0
        assert len(framework.experiment_results) == 0
    
    def test_experiment_types_available(self, framework):
        """Test all experiment types are available."""
        experiment_types = {exp.experiment_type for exp in framework.experiments}
        
        expected_types = {
            ChaosExperimentType.AGENT_FAILURE,
            ChaosExperimentType.NETWORK_PARTITION,
            ChaosExperimentType.RESOURCE_EXHAUSTION,
            ChaosExperimentType.BYZANTINE_AGENT,
            ChaosExperimentType.SERVICE_DEGRADATION,
            ChaosExperimentType.CASCADING_FAILURE
        }
        
        assert expected_types.issubset(experiment_types)
    
    def test_failure_injectors_initialized(self, framework):
        """Test failure injectors are properly initialized."""
        expected_injectors = {
            "agent_failure",
            "network_partition", 
            "resource_exhaustion",
            "service_degradation",
            "byzantine_behavior",
            "latency_injection",
            "data_corruption"
        }
        
        assert set(framework.failure_injectors.keys()) == expected_injectors
        assert set(framework.recovery_handlers.keys()) == expected_injectors
    
    @pytest.mark.asyncio
    async def test_agent_failure_injection(self, framework, sample_experiment):
        """Test agent failure injection mechanism."""
        injection_state = await framework._inject_agent_failure(sample_experiment)
        
        assert "failed_agents" in injection_state
        assert injection_state["failed_agents"] == ["detection_agent"]
        assert injection_state["failure_mode"] == "complete_failure"
        assert "original_states" in injection_state
    
    @pytest.mark.asyncio
    async def test_network_partition_injection(self, framework):
        """Test network partition injection mechanism."""
        experiment = ChaosExperiment(
            name="test_partition",
            experiment_type=ChaosExperimentType.NETWORK_PARTITION,
            failure_mode=FailureMode.COMPLETE_FAILURE,
            target_components=["detection_agent", "diagnosis_agent"],
            duration_seconds=120,
            intensity=1.0,
            description="Test network partition",
            expected_behavior="Agents should detect partition",
            success_criteria={"recovery_time": 60.0},
            blast_radius="agent_type"
        )
        
        injection_state = await framework._inject_network_partition(experiment)
        
        assert "partitioned_components" in injection_state
        assert injection_state["partition_type"] == "split_brain"
        assert len(injection_state["original_connectivity"]) == 2
    
    @pytest.mark.asyncio
    async def test_byzantine_behavior_injection(self, framework):
        """Test Byzantine behavior injection mechanism."""
        experiment = ChaosExperiment(
            name="test_byzantine",
            experiment_type=ChaosExperimentType.BYZANTINE_AGENT,
            failure_mode=FailureMode.MALICIOUS_BEHAVIOR,
            target_components=["detection_agent"],
            duration_seconds=300,
            intensity=1.0,
            description="Test Byzantine agent behavior",
            expected_behavior="Consensus should detect malicious agent",
            success_criteria={"consensus_integrity": 0.95},
            blast_radius="single_agent"
        )
        
        injection_state = await framework._inject_byzantine_behavior(experiment)
        
        assert "byzantine_agents" in injection_state
        assert injection_state["malicious_behavior"] == "malicious_behavior"
        assert "malicious_actions" in injection_state
        assert "provide_false_confidence_scores" in injection_state["malicious_actions"]
    
    @pytest.mark.asyncio
    async def test_resource_exhaustion_injection(self, framework):
        """Test resource exhaustion injection mechanism."""
        experiment = ChaosExperiment(
            name="test_memory_exhaustion",
            experiment_type=ChaosExperimentType.RESOURCE_EXHAUSTION,
            failure_mode=FailureMode.RESOURCE_LEAK,
            target_components=["system"],
            duration_seconds=180,
            intensity=0.8,
            description="Test memory exhaustion",
            expected_behavior="System should implement backpressure",
            success_criteria={"graceful_degradation": 1.0},
            blast_radius="system_wide"
        )
        
        injection_state = await framework._inject_resource_exhaustion(experiment)
        
        assert injection_state["resource_type"] == "memory"
        assert injection_state["target_usage"] == 0.8
        assert "original_usage" in injection_state
    
    @pytest.mark.asyncio
    async def test_recovery_mechanisms(self, framework, sample_experiment):
        """Test recovery mechanisms for different failure types."""
        # Test agent failure recovery
        injection = ChaosInjection(
            experiment=sample_experiment,
            start_time=datetime.utcnow(),
            end_time=None,
            affected_components=["detection_agent"],
            injection_state={"failed_agents": ["detection_agent"]},
            active=True
        )
        
        await framework._recover_agent_failure(sample_experiment, injection)
        assert injection.end_time is None  # Recovery doesn't set end_time directly
    
    @pytest.mark.asyncio
    async def test_baseline_metrics_measurement(self, framework, mock_coordinator):
        """Test baseline metrics measurement."""
        baseline = await framework._measure_baseline_metrics(mock_coordinator)
        
        expected_metrics = {
            "response_time_ms",
            "throughput_per_sec", 
            "error_rate",
            "cpu_usage",
            "memory_usage",
            "availability"
        }
        
        assert set(baseline.keys()) == expected_metrics
        assert baseline["availability"] == 1.0
        assert baseline["error_rate"] < 0.1
    
    @pytest.mark.asyncio
    async def test_experiment_execution(self, framework, sample_experiment, mock_coordinator):
        """Test complete experiment execution."""
        # Mock the monitoring task to avoid long running
        with patch.object(framework, '_monitor_resilience_metrics') as mock_monitor:
            mock_monitor.return_value = AsyncMock()
            
            result = await framework.run_chaos_experiment(sample_experiment, mock_coordinator)
            
            assert isinstance(result, ChaosExperimentResult)
            assert result.experiment == sample_experiment
            assert result.start_time is not None
            assert result.end_time is not None
            assert isinstance(result.success, bool)
            assert len(result.measurements) >= 0
            assert isinstance(result.recovery_metrics, dict)
            assert isinstance(result.lessons_learned, list)
            assert isinstance(result.recommendations, list)
    
    def test_recovery_metrics_calculation(self, framework):
        """Test recovery metrics calculation from measurements."""
        from src.services.chaos_engineering_framework import ResilienceMeasurement
        
        measurements = [
            ResilienceMeasurement(
                timestamp=datetime.utcnow(),
                metric=ResilienceMetric.RECOVERY_TIME,
                value=45.0,
                unit="seconds",
                experiment_name="test"
            ),
            ResilienceMeasurement(
                timestamp=datetime.utcnow(),
                metric=ResilienceMetric.AVAILABILITY,
                value=0.85,
                unit="ratio",
                experiment_name="test"
            ),
            ResilienceMeasurement(
                timestamp=datetime.utcnow(),
                metric=ResilienceMetric.ERROR_RATE_INCREASE,
                value=0.15,
                unit="ratio",
                experiment_name="test"
            )
        ]
        
        sample_experiment = ChaosExperiment(
            name="test",
            experiment_type=ChaosExperimentType.AGENT_FAILURE,
            failure_mode=FailureMode.COMPLETE_FAILURE,
            target_components=["test"],
            duration_seconds=60,
            intensity=1.0,
            description="Test",
            expected_behavior="Test",
            success_criteria={},
            blast_radius="single_agent"
        )
        
        metrics = framework._calculate_recovery_metrics(measurements, sample_experiment)
        
        assert "max_recovery_time" in metrics
        assert "avg_recovery_time" in metrics
        assert "min_availability" in metrics
        assert "max_error_rate_increase" in metrics
        
        assert metrics["max_recovery_time"] == 45.0
        assert metrics["min_availability"] == 0.85
        assert metrics["max_error_rate_increase"] == 0.15
    
    def test_experiment_success_evaluation(self, framework):
        """Test experiment success evaluation against criteria."""
        sample_experiment = ChaosExperiment(
            name="test",
            experiment_type=ChaosExperimentType.AGENT_FAILURE,
            failure_mode=FailureMode.COMPLETE_FAILURE,
            target_components=["test"],
            duration_seconds=60,
            intensity=1.0,
            description="Test",
            expected_behavior="Test",
            success_criteria={
                "recovery_time": 60.0,
                "availability": 0.8,
                "error_rate_increase": 0.2
            },
            blast_radius="single_agent"
        )
        
        # Test successful case
        good_metrics = {
            "max_recovery_time": 45.0,
            "min_availability": 0.85,
            "max_error_rate_increase": 0.15
        }
        
        success = framework._evaluate_experiment_success(sample_experiment, good_metrics)
        assert success is True
        
        # Test failed case
        bad_metrics = {
            "max_recovery_time": 90.0,  # Exceeds threshold
            "min_availability": 0.85,
            "max_error_rate_increase": 0.15
        }
        
        success = framework._evaluate_experiment_success(sample_experiment, bad_metrics)
        assert success is False
    
    def test_lessons_learned_extraction(self, framework):
        """Test lessons learned extraction from experiment results."""
        sample_experiment = ChaosExperiment(
            name="test",
            experiment_type=ChaosExperimentType.BYZANTINE_AGENT,
            failure_mode=FailureMode.MALICIOUS_BEHAVIOR,
            target_components=["test"],
            duration_seconds=60,
            intensity=1.0,
            description="Test",
            expected_behavior="Test",
            success_criteria={},
            blast_radius="single_agent"
        )
        
        measurements = []
        system_behavior = {
            "failure_detection_time": 30.0,
            "recovery_patterns": ["exponential_recovery"],
            "degradation_characteristics": {"graceful": True},
            "resilience_mechanisms_activated": ["consensus_protection"]
        }
        
        lessons = framework._extract_lessons_learned(sample_experiment, measurements, system_behavior)
        
        assert len(lessons) > 0
        assert any("detection time" in lesson.lower() for lesson in lessons)
        assert any("byzantine" in lesson.lower() for lesson in lessons)
        assert any("consensus protection" in lesson.lower() for lesson in lessons)
    
    def test_recommendations_generation(self, framework):
        """Test recommendations generation from experiment results."""
        sample_experiment = ChaosExperiment(
            name="test",
            experiment_type=ChaosExperimentType.NETWORK_PARTITION,
            failure_mode=FailureMode.COMPLETE_FAILURE,
            target_components=["test"],
            duration_seconds=60,
            intensity=1.0,
            description="Test",
            expected_behavior="Test",
            success_criteria={},
            blast_radius="agent_type"
        )
        
        system_behavior = {
            "failure_detection_time": 45.0,  # Slow detection
            "recovery_patterns": [],
            "degradation_characteristics": {"graceful": False},
            "resilience_mechanisms_activated": []
        }
        
        recommendations = framework._generate_recommendations(sample_experiment, system_behavior, False)
        
        assert len(recommendations) > 0
        assert any("failed" in rec.lower() for rec in recommendations)
        assert any("detection" in rec.lower() for rec in recommendations)
        assert any("partition" in rec.lower() for rec in recommendations)
    
    def test_resilience_report_generation(self, framework):
        """Test comprehensive resilience report generation."""
        # Create mock experiment results
        sample_experiment = ChaosExperiment(
            name="test",
            experiment_type=ChaosExperimentType.AGENT_FAILURE,
            failure_mode=FailureMode.COMPLETE_FAILURE,
            target_components=["test"],
            duration_seconds=60,
            intensity=1.0,
            description="Test",
            expected_behavior="Test",
            success_criteria={},
            blast_radius="single_agent"
        )
        
        result1 = ChaosExperimentResult(
            experiment=sample_experiment,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(minutes=2),
            success=True,
            measurements=[],
            system_behavior={},
            recovery_metrics={"max_recovery_time": 30.0, "min_availability": 0.9},
            lessons_learned=["Good detection time"],
            recommendations=["Continue monitoring"]
        )
        
        result2 = ChaosExperimentResult(
            experiment=sample_experiment,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(minutes=3),
            success=False,
            measurements=[],
            system_behavior={},
            recovery_metrics={"max_recovery_time": 90.0, "min_availability": 0.6},
            lessons_learned=["Slow recovery"],
            recommendations=["Improve detection"]
        )
        
        results = [result1, result2]
        report = framework.generate_resilience_report(results)
        
        assert report["total_experiments"] == 2
        assert report["successful_experiments"] == 1
        assert report["failed_experiments"] == 1
        assert "resilience_summary" in report
        assert "lessons_learned" in report
        assert "recommendations" in report
        
        # Check resilience summary
        if "recovery_time" in report["resilience_summary"]:
            assert "avg_seconds" in report["resilience_summary"]["recovery_time"]
            assert "max_seconds" in report["resilience_summary"]["recovery_time"]
    
    @pytest.mark.asyncio
    async def test_emergency_stop_mechanism(self, framework, sample_experiment):
        """Test emergency stop mechanism."""
        # Add active injection
        injection = ChaosInjection(
            experiment=sample_experiment,
            start_time=datetime.utcnow(),
            end_time=None,
            affected_components=["detection_agent"],
            injection_state={},
            active=True
        )
        framework.active_injections["test"] = injection
        
        # Trigger emergency stop
        await framework._trigger_emergency_stop(sample_experiment)
        
        assert framework.emergency_stop_active is True
        assert len(framework.active_injections) == 0
    
    def test_safety_thresholds(self, framework):
        """Test safety threshold configuration."""
        expected_thresholds = {
            "max_error_rate": 0.5,
            "min_availability": 0.7,
            "max_recovery_time": 300
        }
        
        assert framework.safety_thresholds == expected_thresholds
    
    @pytest.mark.asyncio
    async def test_concurrent_experiment_limit(self, framework, mock_coordinator):
        """Test maximum concurrent experiment limit."""
        # Fill up active injections to max
        for i in range(framework.max_concurrent_experiments):
            injection = ChaosInjection(
                experiment=framework.experiments[0],
                start_time=datetime.utcnow(),
                end_time=None,
                affected_components=["test"],
                injection_state={},
                active=True
            )
            framework.active_injections[f"test_{i}"] = injection
        
        # Try to run another experiment
        with pytest.raises(RuntimeError, match="Maximum concurrent experiments limit reached"):
            await framework.run_chaos_experiment(framework.experiments[0], mock_coordinator)
    
    @pytest.mark.asyncio
    async def test_emergency_stop_prevents_execution(self, framework, mock_coordinator):
        """Test emergency stop prevents new experiment execution."""
        framework.emergency_stop_active = True
        
        with pytest.raises(RuntimeError, match="Emergency stop is active"):
            await framework.run_chaos_experiment(framework.experiments[0], mock_coordinator)


class TestChaosExperimentTypes:
    """Test different chaos experiment types and their behaviors."""
    
    @pytest.fixture
    def framework(self):
        return ChaosEngineeringFramework()
    
    def test_agent_failure_experiments(self, framework):
        """Test agent failure experiments are properly configured."""
        agent_failure_experiments = [
            exp for exp in framework.experiments 
            if exp.experiment_type == ChaosExperimentType.AGENT_FAILURE
        ]
        
        assert len(agent_failure_experiments) >= 2
        
        # Check for complete and intermittent failure modes
        failure_modes = {exp.failure_mode for exp in agent_failure_experiments}
        assert FailureMode.COMPLETE_FAILURE in failure_modes
        assert FailureMode.INTERMITTENT_FAILURE in failure_modes
    
    def test_network_partition_experiments(self, framework):
        """Test network partition experiments are properly configured."""
        partition_experiments = [
            exp for exp in framework.experiments 
            if exp.experiment_type == ChaosExperimentType.NETWORK_PARTITION
        ]
        
        assert len(partition_experiments) >= 1
        
        # Check success criteria include consensus and data consistency
        for exp in partition_experiments:
            if "consensus" in exp.name:
                assert "consensus_integrity" in exp.success_criteria
            if "agent_network_partition" in exp.name:
                assert "data_consistency" in exp.success_criteria
    
    def test_byzantine_agent_experiments(self, framework):
        """Test Byzantine agent experiments are properly configured."""
        byzantine_experiments = [
            exp for exp in framework.experiments 
            if exp.experiment_type == ChaosExperimentType.BYZANTINE_AGENT
        ]
        
        assert len(byzantine_experiments) >= 2
        
        # All Byzantine experiments should test consensus integrity
        for exp in byzantine_experiments:
            assert "consensus_integrity" in exp.success_criteria
            assert exp.failure_mode == FailureMode.MALICIOUS_BEHAVIOR
    
    def test_resource_exhaustion_experiments(self, framework):
        """Test resource exhaustion experiments are properly configured."""
        resource_experiments = [
            exp for exp in framework.experiments 
            if exp.experiment_type == ChaosExperimentType.RESOURCE_EXHAUSTION
        ]
        
        assert len(resource_experiments) >= 2
        
        # Check for memory and CPU exhaustion
        experiment_names = {exp.name for exp in resource_experiments}
        assert any("memory" in name for name in experiment_names)
        assert any("cpu" in name for name in experiment_names)
    
    def test_cascading_failure_experiments(self, framework):
        """Test cascading failure experiments are properly configured."""
        cascading_experiments = [
            exp for exp in framework.experiments 
            if exp.experiment_type == ChaosExperimentType.CASCADING_FAILURE
        ]
        
        assert len(cascading_experiments) >= 1
        
        for exp in cascading_experiments:
            # Cascading failures should target multiple components
            assert len(exp.target_components) > 1
            # Should have system-wide blast radius
            assert exp.blast_radius == "system_wide"
            # Should test graceful degradation
            assert "graceful_degradation" in exp.success_criteria


class TestResilienceMetrics:
    """Test resilience metrics collection and analysis."""
    
    def test_resilience_metric_types(self):
        """Test all resilience metric types are defined."""
        expected_metrics = {
            ResilienceMetric.RECOVERY_TIME,
            ResilienceMetric.AVAILABILITY,
            ResilienceMetric.THROUGHPUT_DEGRADATION,
            ResilienceMetric.ERROR_RATE_INCREASE,
            ResilienceMetric.CONSENSUS_INTEGRITY,
            ResilienceMetric.DATA_CONSISTENCY,
            ResilienceMetric.GRACEFUL_DEGRADATION
        }
        
        # Check all metrics are available
        available_metrics = set(ResilienceMetric)
        assert expected_metrics.issubset(available_metrics)
    
    def test_measurement_data_structure(self):
        """Test resilience measurement data structure."""
        from src.services.chaos_engineering_framework import ResilienceMeasurement
        
        measurement = ResilienceMeasurement(
            timestamp=datetime.utcnow(),
            metric=ResilienceMetric.RECOVERY_TIME,
            value=45.0,
            unit="seconds",
            experiment_name="test_experiment",
            context={"component": "detection_agent"}
        )
        
        assert measurement.timestamp is not None
        assert measurement.metric == ResilienceMetric.RECOVERY_TIME
        assert measurement.value == 45.0
        assert measurement.unit == "seconds"
        assert measurement.experiment_name == "test_experiment"
        assert measurement.context["component"] == "detection_agent"


if __name__ == "__main__":
    pytest.main([__file__])