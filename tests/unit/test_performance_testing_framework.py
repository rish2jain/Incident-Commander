"""
Unit tests for Performance Testing Framework (Task 15.3)

Tests the comprehensive performance testing and benchmarking framework
for 1000+ concurrent incidents, load testing, and capacity planning.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from src.services.performance_testing_framework import (
    PerformanceTestingFramework,
    LoadTestType,
    PerformanceMetric,
    LoadTestConfiguration,
    PerformanceMeasurement,
    LoadTestResult,
    BenchmarkResult
)


class MockAgentSwarmCoordinator:
    """Mock coordinator for testing."""
    
    async def handle_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mock incident handling."""
        await asyncio.sleep(0.1)  # Simulate processing time
        return {
            "status": "resolved",
            "incident_id": incident_data.get("id"),
            "resolution_time": 0.1
        }


class TestPerformanceTestingFramework:
    """Test the performance testing framework."""
    
    @pytest.fixture
    def framework(self):
        """Create performance testing framework."""
        return PerformanceTestingFramework()
    
    @pytest.fixture
    def mock_coordinator(self):
        """Create mock coordinator."""
        return MockAgentSwarmCoordinator()
    
    def test_framework_initialization(self, framework):
        """Test framework initialization."""
        assert len(framework.test_configurations) > 0
        assert framework.incident_counter == 0
        assert len(framework.test_results) == 0
        assert len(framework.performance_history) == 0
    
    def test_test_configurations_loaded(self, framework):
        """Test that test configurations are properly loaded."""
        config_names = {config.name for config in framework.test_configurations}
        
        expected_configs = {
            "concurrent_incidents_1000",
            "alert_storm_50k",
            "sustained_load_24h",
            "spike_load_test",
            "stress_test_5000",
            "capacity_test"
        }
        
        assert expected_configs.issubset(config_names)
    
    def test_concurrent_incidents_config(self, framework):
        """Test concurrent incidents configuration."""
        config = next(
            (c for c in framework.test_configurations if c.name == "concurrent_incidents_1000"),
            None
        )
        
        assert config is not None
        assert config.test_type == LoadTestType.CONCURRENT_INCIDENTS
        assert config.target_load == 1000
        assert config.success_criteria["mttr"] == 180.0  # 3 minutes
        assert config.success_criteria["error_rate"] == 0.05  # 5%
    
    def test_alert_storm_config(self, framework):
        """Test alert storm configuration."""
        config = next(
            (c for c in framework.test_configurations if c.name == "alert_storm_50k"),
            None
        )
        
        assert config is not None
        assert config.test_type == LoadTestType.ALERT_STORM
        assert config.target_load == 50000
        assert config.success_criteria["throughput"] == 500.0  # 500 alerts/sec
    
    def test_generate_test_incidents(self, framework):
        """Test test incident generation."""
        incidents = framework._generate_test_incidents(10, ["database_cascade", "ddos_attack"])
        
        assert len(incidents) == 10
        assert all(isinstance(incident, dict) for incident in incidents)
        assert all("id" in incident for incident in incidents)
        assert all("severity" in incident for incident in incidents)
        assert all("pattern" in incident for incident in incidents)
        
        # Check patterns are from the provided list
        patterns = {incident["pattern"] for incident in incidents}
        assert patterns.issubset({"database_cascade", "ddos_attack"})
    
    def test_generate_alert_storm(self, framework):
        """Test alert storm generation."""
        alerts = framework._generate_alert_storm(100)
        
        assert len(alerts) == 100
        assert all(isinstance(alert, dict) for alert in alerts)
        assert all("id" in alert for alert in alerts)
        assert all("metric" in alert for alert in alerts)
        assert all("value" in alert for alert in alerts)
        assert all("threshold" in alert for alert in alerts)
    
    @pytest.mark.asyncio
    async def test_process_incident_with_timing(self, framework, mock_coordinator):
        """Test incident processing with timing measurement."""
        incident = {
            "id": "test_incident_1",
            "severity": "high",
            "title": "Test incident"
        }
        
        measurements = []
        
        result = await framework._process_incident_with_timing(
            incident, measurements, mock_coordinator
        )
        
        assert result["status"] == "resolved"
        assert result["incident_id"] == "test_incident_1"
        
        # Check measurements were recorded
        response_time_measurements = [
            m for m in measurements if m.metric == PerformanceMetric.RESPONSE_TIME
        ]
        assert len(response_time_measurements) > 0
        
        mttr_measurements = [
            m for m in measurements if m.metric == PerformanceMetric.MTTR
        ]
        assert len(mttr_measurements) > 0
    
    @pytest.mark.asyncio
    async def test_process_alert_with_timing(self, framework, mock_coordinator):
        """Test alert processing with timing measurement."""
        alert = {
            "id": "test_alert_1",
            "metric": "cpu_usage",
            "value": 0.9
        }
        
        measurements = []
        
        result = await framework._process_alert_with_timing(
            alert, measurements, mock_coordinator
        )
        
        assert result["status"] == "processed"
        assert result["alert_id"] == "test_alert_1"
        
        # Check measurements were recorded
        response_time_measurements = [
            m for m in measurements if m.metric == PerformanceMetric.RESPONSE_TIME
        ]
        assert len(response_time_measurements) > 0
    
    def test_calculate_summary_stats(self, framework):
        """Test summary statistics calculation."""
        measurements = [
            PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.RESPONSE_TIME,
                value=100.0,
                unit="ms"
            ),
            PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.RESPONSE_TIME,
                value=200.0,
                unit="ms"
            ),
            PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.RESPONSE_TIME,
                value=150.0,
                unit="ms"
            )
        ]
        
        stats = framework._calculate_summary_stats(measurements)
        
        assert "response_time" in stats
        response_stats = stats["response_time"]
        
        assert response_stats["min"] == 100.0
        assert response_stats["max"] == 200.0
        assert response_stats["avg"] == 150.0
        assert response_stats["count"] == 3
    
    def test_detect_bottlenecks(self, framework):
        """Test bottleneck detection."""
        measurements = [
            PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.CPU_USAGE,
                value=0.95,  # High CPU usage
                unit="ratio"
            ),
            PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.MEMORY_USAGE,
                value=0.97,  # High memory usage
                unit="ratio"
            ),
            PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.RESPONSE_TIME,
                value=35000.0,  # High response time
                unit="ms"
            )
        ]
        
        config = LoadTestConfiguration(
            name="test_config",
            test_type=LoadTestType.CONCURRENT_INCIDENTS,
            target_load=100,
            duration_seconds=300,
            ramp_up_seconds=60,
            ramp_down_seconds=60,
            success_criteria={}
        )
        
        bottlenecks = framework._detect_bottlenecks(measurements, config)
        
        assert len(bottlenecks) >= 2  # Should detect CPU and memory bottlenecks
        assert any("CPU bottleneck" in b for b in bottlenecks)
        assert any("Memory bottleneck" in b for b in bottlenecks)
    
    def test_evaluate_success_criteria(self, framework):
        """Test success criteria evaluation."""
        config = LoadTestConfiguration(
            name="test_config",
            test_type=LoadTestType.CONCURRENT_INCIDENTS,
            target_load=100,
            duration_seconds=300,
            ramp_up_seconds=60,
            ramp_down_seconds=60,
            success_criteria={
                "mttr": 180.0,  # 3 minutes
                "error_rate": 0.05,  # 5%
                "cpu_usage": 0.8,  # 80%
                "memory_usage": 0.85  # 85%
            }
        )
        
        # Test passing criteria
        good_stats = {
            "mttr": {"avg": 120.0},  # Under 3 minutes
            "error_rate": {"avg": 0.02},  # Under 5%
            "cpu_usage": {"max": 0.75},  # Under 80%
            "memory_usage": {"max": 0.80}  # Under 85%
        }
        
        assert framework._evaluate_success_criteria(config, good_stats, [])
        
        # Test failing criteria
        bad_stats = {
            "mttr": {"avg": 200.0},  # Over 3 minutes
            "error_rate": {"avg": 0.08},  # Over 5%
            "cpu_usage": {"max": 0.85},  # Over 80%
            "memory_usage": {"max": 0.90}  # Over 85%
        }
        
        assert not framework._evaluate_success_criteria(config, bad_stats, [])
        
        # Test with errors
        assert not framework._evaluate_success_criteria(config, good_stats, ["Test error"])
    
    @pytest.mark.asyncio
    async def test_run_load_test_basic(self, framework, mock_coordinator):
        """Test basic load test execution."""
        config = LoadTestConfiguration(
            name="test_load_test",
            test_type=LoadTestType.CONCURRENT_INCIDENTS,
            target_load=5,  # Small load for testing
            duration_seconds=10,  # Short duration
            ramp_up_seconds=2,
            ramp_down_seconds=2,
            success_criteria={
                "mttr": 300.0,  # Generous criteria for testing
                "error_rate": 0.5
            },
            incident_patterns=["test_pattern"]
        )
        
        with patch.object(framework, '_monitor_resources') as mock_monitor:
            mock_monitor.return_value = None
            
            result = await framework.run_load_test(config, mock_coordinator)
        
        assert isinstance(result, LoadTestResult)
        assert result.configuration == config
        assert result.start_time <= result.end_time
        assert len(result.measurements) > 0
        assert isinstance(result.success, bool)
    
    @pytest.mark.asyncio
    async def test_concurrent_incidents_test(self, framework, mock_coordinator):
        """Test concurrent incidents load test."""
        config = LoadTestConfiguration(
            name="test_concurrent",
            test_type=LoadTestType.CONCURRENT_INCIDENTS,
            target_load=3,  # Small load for testing
            duration_seconds=5,
            ramp_up_seconds=1,
            ramp_down_seconds=1,
            success_criteria={},
            incident_patterns=["test_pattern"]
        )
        
        measurements = []
        
        with patch.object(framework, '_ramp_up_load') as mock_ramp_up, \
             patch.object(framework, '_ramp_down_load') as mock_ramp_down:
            
            mock_ramp_up.return_value = None
            mock_ramp_down.return_value = None
            
            await framework._run_concurrent_incidents_test(config, measurements, mock_coordinator)
        
        # Check that throughput measurements were recorded
        throughput_measurements = [
            m for m in measurements if m.metric == PerformanceMetric.THROUGHPUT
        ]
        assert len(throughput_measurements) > 0
    
    @pytest.mark.asyncio
    async def test_alert_storm_test(self, framework, mock_coordinator):
        """Test alert storm load test."""
        config = LoadTestConfiguration(
            name="test_alert_storm",
            test_type=LoadTestType.ALERT_STORM,
            target_load=50,  # Small storm for testing
            duration_seconds=5,
            ramp_up_seconds=1,
            ramp_down_seconds=1,
            success_criteria={}
        )
        
        measurements = []
        
        await framework._run_alert_storm_test(config, measurements, mock_coordinator)
        
        # Check that throughput measurements were recorded
        throughput_measurements = [
            m for m in measurements if m.metric == PerformanceMetric.THROUGHPUT
        ]
        assert len(throughput_measurements) > 0
    
    def test_generate_performance_report(self, framework):
        """Test performance report generation."""
        # Create mock test results
        config = LoadTestConfiguration(
            name="test_config",
            test_type=LoadTestType.CONCURRENT_INCIDENTS,
            target_load=100,
            duration_seconds=300,
            ramp_up_seconds=60,
            ramp_down_seconds=60,
            success_criteria={}
        )
        
        measurements = [
            PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.RESPONSE_TIME,
                value=150.0,
                unit="ms"
            ),
            PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.MTTR,
                value=120.0,
                unit="seconds"
            ),
            PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.THROUGHPUT,
                value=10.0,
                unit="incidents/sec"
            )
        ]
        
        result = LoadTestResult(
            configuration=config,
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(seconds=300),
            success=True,
            measurements=measurements,
            summary_stats={
                "response_time": {"avg": 150.0, "p95": 200.0},
                "mttr": {"avg": 120.0},
                "throughput": {"avg": 10.0}
            },
            errors=[],
            resource_usage={},
            bottlenecks_detected=[]
        )
        
        report = framework.generate_performance_report([result])
        
        assert "timestamp" in report
        assert "total_tests" in report
        assert "passed_tests" in report
        assert "failed_tests" in report
        assert "test_results" in report
        assert "performance_summary" in report
        
        assert report["total_tests"] == 1
        assert report["passed_tests"] == 1
        assert report["failed_tests"] == 0
        
        # Check test results
        assert len(report["test_results"]) == 1
        test_result = report["test_results"][0]
        assert test_result["name"] == "test_config"
        assert test_result["success"] is True
        assert "key_metrics" in test_result
    
    @pytest.mark.asyncio
    async def test_error_handling_in_incident_processing(self, framework):
        """Test error handling during incident processing."""
        # Create a coordinator that raises an exception
        failing_coordinator = AsyncMock()
        failing_coordinator.handle_incident.side_effect = Exception("Test error")
        
        incident = {"id": "test_incident", "severity": "high"}
        measurements = []
        
        with pytest.raises(Exception, match="Test error"):
            await framework._process_incident_with_timing(
                incident, measurements, failing_coordinator
            )
        
        # Check that error measurement was recorded
        error_measurements = [
            m for m in measurements if m.metric == PerformanceMetric.ERROR_RATE
        ]
        assert len(error_measurements) > 0
        assert error_measurements[0].value == 1.0
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, framework):
        """Test timeout handling in load tests."""
        # Create a slow coordinator
        slow_coordinator = AsyncMock()
        
        async def slow_handle_incident(incident_data):
            await asyncio.sleep(2)  # Longer than test timeout
            return {"status": "resolved"}
        
        slow_coordinator.handle_incident = slow_handle_incident
        
        config = LoadTestConfiguration(
            name="timeout_test",
            test_type=LoadTestType.CONCURRENT_INCIDENTS,
            target_load=1,
            duration_seconds=1,  # Short timeout
            ramp_up_seconds=0,
            ramp_down_seconds=0,
            success_criteria={}
        )
        
        with patch.object(framework, '_monitor_resources') as mock_monitor:
            mock_monitor.return_value = None
            
            result = await framework.run_load_test(config, slow_coordinator)
        
        # Test should complete even with timeout
        assert isinstance(result, LoadTestResult)
    
    def test_performance_measurement_creation(self):
        """Test performance measurement creation."""
        measurement = PerformanceMeasurement(
            timestamp=datetime.utcnow(),
            metric=PerformanceMetric.RESPONSE_TIME,
            value=150.0,
            unit="ms",
            context={"incident_id": "test_123"}
        )
        
        assert measurement.metric == PerformanceMetric.RESPONSE_TIME
        assert measurement.value == 150.0
        assert measurement.unit == "ms"
        assert measurement.context["incident_id"] == "test_123"
    
    def test_load_test_configuration_creation(self):
        """Test load test configuration creation."""
        config = LoadTestConfiguration(
            name="test_config",
            test_type=LoadTestType.STRESS_TEST,
            target_load=5000,
            duration_seconds=600,
            ramp_up_seconds=120,
            ramp_down_seconds=120,
            success_criteria={
                "error_rate": 0.2,
                "system_availability": 0.95
            },
            incident_patterns=["extreme_load"],
            description="Stress test beyond normal capacity"
        )
        
        assert config.name == "test_config"
        assert config.test_type == LoadTestType.STRESS_TEST
        assert config.target_load == 5000
        assert config.success_criteria["error_rate"] == 0.2
        assert "extreme_load" in config.incident_patterns