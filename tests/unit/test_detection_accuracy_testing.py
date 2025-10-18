"""
Unit tests for Detection Accuracy Testing Service (Task 4.3)

Tests the comprehensive detection accuracy testing framework with
synthetic scenarios, performance benchmarking, and regression validation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from src.services.detection_accuracy_testing import (
    DetectionAccuracyTester,
    TestScenarioType,
    DetectionAccuracy,
    TestAlert,
    TestScenario,
    DetectionTestResult,
    AccuracyMetrics
)
from src.models.incident import IncidentSeverity
from src.models.agent import AgentRecommendation, AgentType, ActionType, RiskLevel


class MockMonitoringDataSource:
    """Mock monitoring data source for testing."""
    
    def __init__(self, name: str):
        self.name = name
    
    async def get_recent_alerts(self):
        return []


class MockDetectionAgent:
    """Mock detection agent for testing."""
    
    def __init__(self):
        self.monitoring_sources = {}
        self.name = "test_detection_agent"
    
    async def analyze_incident_data(self, incident_data: Dict[str, Any]) -> AgentRecommendation:
        """Mock incident analysis."""
        return AgentRecommendation(
            agent_name=AgentType.DETECTION,
            incident_id="test-incident",
            action_type=ActionType.NO_ACTION,
            action_id="mock-action-1",
            confidence=0.8,
            risk_level=RiskLevel.LOW,
            estimated_impact="medium",
            reasoning="Mock analysis result",
            urgency=0.5
        )


class TestDetectionAccuracyTester:
    """Test the detection accuracy testing framework."""
    
    @pytest.fixture
    def tester(self):
        """Create detection accuracy tester."""
        return DetectionAccuracyTester()
    
    @pytest.fixture
    def mock_agent(self):
        """Create mock detection agent."""
        return MockDetectionAgent()
    
    def test_tester_initialization(self, tester):
        """Test tester initialization."""
        assert len(tester.test_scenarios) > 0
        assert tester.baseline_metrics is None
        assert tester.regression_threshold == 0.05
        assert len(tester.test_results) == 0
    
    def test_scenario_generation(self, tester):
        """Test test scenario generation."""
        # Check that scenarios are properly initialized
        scenario_types = {scenario.scenario_type for scenario in tester.test_scenarios}
        
        expected_types = {
            TestScenarioType.SINGLE_SOURCE_ALERT,
            TestScenarioType.MULTI_SOURCE_CORRELATION,
            TestScenarioType.ALERT_STORM,
            TestScenarioType.FALSE_POSITIVE,
            TestScenarioType.BASELINE_NOISE
        }
        
        assert expected_types.issubset(scenario_types)
    
    def test_alert_storm_generation(self, tester):
        """Test alert storm generation."""
        alerts = tester._generate_alert_storm(
            count=100,
            base_metric="cpu_usage",
            base_value=90.0,
            threshold=80.0,
            duration_seconds=60
        )
        
        assert len(alerts) == 100
        assert all(isinstance(alert, TestAlert) for alert in alerts)
        assert all(alert.metric_name == "cpu_usage" for alert in alerts)
        assert all(alert.threshold == 80.0 for alert in alerts)
    
    def test_cascading_alerts_generation(self, tester):
        """Test cascading failure alert generation."""
        services = ["auth", "user", "order"]
        alerts = tester._generate_cascading_alerts(services, 10)
        
        assert len(alerts) == 30  # 10 alerts per service
        
        # Check service distribution
        service_counts = {}
        for alert in alerts:
            service = alert.tags.get("service")
            service_counts[service] = service_counts.get(service, 0) + 1
        
        assert all(count == 10 for count in service_counts.values())
    
    def test_baseline_noise_generation(self, tester):
        """Test baseline noise generation."""
        alerts = tester._generate_baseline_noise(50)
        
        assert len(alerts) == 50
        assert all(not alert.is_incident for alert in alerts)
        assert all(alert.severity == "info" for alert in alerts)
    
    def test_confidence_to_severity_mapping(self, tester):
        """Test confidence to severity mapping."""
        assert tester._confidence_to_severity(0.95) == IncidentSeverity.CRITICAL
        assert tester._confidence_to_severity(0.8) == IncidentSeverity.HIGH
        assert tester._confidence_to_severity(0.6) == IncidentSeverity.MEDIUM
        assert tester._confidence_to_severity(0.3) == IncidentSeverity.LOW
    
    def test_accuracy_classification(self, tester):
        """Test accuracy classification logic."""
        assert tester._classify_accuracy(True, True) == DetectionAccuracy.TRUE_POSITIVE
        assert tester._classify_accuracy(True, False) == DetectionAccuracy.FALSE_NEGATIVE
        assert tester._classify_accuracy(False, True) == DetectionAccuracy.FALSE_POSITIVE
        assert tester._classify_accuracy(False, False) == DetectionAccuracy.TRUE_NEGATIVE
    
    @pytest.mark.asyncio
    async def test_single_detection_test(self, tester, mock_agent):
        """Test running a single detection test."""
        # Create a simple test scenario
        scenario = TestScenario(
            name="test_scenario",
            scenario_type=TestScenarioType.SINGLE_SOURCE_ALERT,
            alerts=[
                TestAlert(
                    source="cloudwatch",
                    metric_name="CPUUtilization",
                    value=95.0,
                    threshold=80.0,
                    timestamp=datetime.utcnow(),
                    severity="critical"
                )
            ],
            expected_incident=True,
            expected_confidence=0.8,
            expected_severity=IncidentSeverity.HIGH,
            description="Test scenario"
        )
        
        result = await tester.run_detection_test(mock_agent, scenario)
        
        assert isinstance(result, DetectionTestResult)
        assert result.scenario_name == "test_scenario"
        assert result.detected_incident is True  # Mock agent returns confidence 0.8
        assert result.actual_confidence == 0.8
        assert result.processing_time_ms > 0
        assert result.alerts_processed == 1
    
    def test_accuracy_metrics_calculation(self, tester):
        """Test accuracy metrics calculation."""
        # Create mock test results
        tester.test_results = [
            DetectionTestResult(
                scenario_name="test1",
                scenario_type=TestScenarioType.SINGLE_SOURCE_ALERT,
                expected_incident=True,
                detected_incident=True,
                expected_confidence=0.8,
                actual_confidence=0.8,
                expected_severity=IncidentSeverity.HIGH,
                actual_severity=IncidentSeverity.HIGH,
                accuracy_classification=DetectionAccuracy.TRUE_POSITIVE,
                processing_time_ms=100.0,
                alerts_processed=1,
                correlation_count=1
            ),
            DetectionTestResult(
                scenario_name="test2",
                scenario_type=TestScenarioType.FALSE_POSITIVE,
                expected_incident=False,
                detected_incident=False,
                expected_confidence=0.2,
                actual_confidence=0.3,
                expected_severity=IncidentSeverity.LOW,
                actual_severity=IncidentSeverity.LOW,
                accuracy_classification=DetectionAccuracy.TRUE_NEGATIVE,
                processing_time_ms=50.0,
                alerts_processed=1,
                correlation_count=0
            )
        ]
        
        metrics = tester._calculate_accuracy_metrics()
        
        assert metrics.total_tests == 2
        assert metrics.true_positives == 1
        assert metrics.true_negatives == 1
        assert metrics.false_positives == 0
        assert metrics.false_negatives == 0
        assert metrics.accuracy == 1.0  # Perfect accuracy
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1_score == 1.0
        assert metrics.avg_processing_time_ms == 75.0
    
    def test_regression_detection(self, tester):
        """Test regression detection logic."""
        # Set baseline metrics
        baseline = AccuracyMetrics(
            total_tests=10,
            true_positives=8,
            false_positives=1,
            true_negatives=1,
            false_negatives=0,
            accuracy=0.9,
            precision=0.89,
            recall=1.0,
            f1_score=0.94,
            avg_processing_time_ms=100.0,
            confidence_correlation=0.85
        )
        tester.set_baseline_metrics(baseline)
        
        # Test with good metrics (no regression)
        good_metrics = AccuracyMetrics(
            total_tests=10,
            true_positives=8,
            false_positives=1,
            true_negatives=1,
            false_negatives=0,
            accuracy=0.91,  # Slight improvement
            precision=0.89,
            recall=1.0,
            f1_score=0.94,
            avg_processing_time_ms=95.0,  # Slight improvement
            confidence_correlation=0.86
        )
        
        assert not tester._check_regression(good_metrics)
        
        # Test with regression
        bad_metrics = AccuracyMetrics(
            total_tests=10,
            true_positives=6,
            false_positives=3,
            true_negatives=1,
            false_negatives=0,
            accuracy=0.7,  # Significant drop
            precision=0.67,  # Significant drop
            recall=1.0,
            f1_score=0.8,
            avg_processing_time_ms=200.0,  # Much slower
            confidence_correlation=0.7
        )
        
        assert tester._check_regression(bad_metrics)
    
    def test_mock_monitoring_sources_creation(self, tester):
        """Test creation of mock monitoring sources."""
        alerts = [
            TestAlert(
                source="cloudwatch",
                metric_name="CPUUtilization",
                value=95.0,
                threshold=80.0,
                timestamp=datetime.utcnow(),
                severity="critical"
            ),
            TestAlert(
                source="datadog",
                metric_name="memory.usage",
                value=0.9,
                threshold=0.8,
                timestamp=datetime.utcnow(),
                severity="warning"
            )
        ]
        
        mock_sources = tester._create_mock_monitoring_sources(alerts)
        
        assert "cloudwatch" in mock_sources
        assert "datadog" in mock_sources
        assert len(mock_sources) == 2
        
        # Check that mock sources have the expected interface
        for source in mock_sources.values():
            assert hasattr(source, 'get_recent_alerts')
            assert hasattr(source, 'name')
    
    def test_alert_to_dict_conversion(self, tester):
        """Test alert to dictionary conversion."""
        alert = TestAlert(
            source="cloudwatch",
            metric_name="CPUUtilization",
            value=95.0,
            threshold=80.0,
            timestamp=datetime.utcnow(),
            severity="critical",
            tags={"instance": "i-123456"},
            is_incident=True
        )
        
        alert_dict = tester._alert_to_dict(alert)
        
        assert alert_dict["source"] == "cloudwatch"
        assert alert_dict["metric_name"] == "CPUUtilization"
        assert alert_dict["value"] == 95.0
        assert alert_dict["threshold"] == 80.0
        assert alert_dict["severity"] == "critical"
        assert alert_dict["tags"] == {"instance": "i-123456"}
        assert alert_dict["is_incident"] is True
        assert "timestamp" in alert_dict
    
    @pytest.mark.asyncio
    async def test_alert_storm_benchmark(self, tester, mock_agent):
        """Test alert storm benchmarking."""
        # Use smaller alert counts for faster testing
        alert_counts = [10, 50]
        
        benchmark_results = await tester.run_alert_storm_benchmark(mock_agent, alert_counts)
        
        assert len(benchmark_results) == 2
        assert 10 in benchmark_results
        assert 50 in benchmark_results
        
        for count, results in benchmark_results.items():
            assert "avg_time_ms" in results
            assert "min_time_ms" in results
            assert "max_time_ms" in results
            assert "success_rate" in results
            assert "throughput_alerts_per_sec" in results
            assert 0 <= results["success_rate"] <= 1
            assert results["throughput_alerts_per_sec"] > 0
    
    def test_accuracy_report_generation(self, tester):
        """Test accuracy report generation."""
        # Add some mock test results
        tester.test_results = [
            DetectionTestResult(
                scenario_name="test1",
                scenario_type=TestScenarioType.SINGLE_SOURCE_ALERT,
                expected_incident=True,
                detected_incident=True,
                expected_confidence=0.8,
                actual_confidence=0.8,
                expected_severity=IncidentSeverity.HIGH,
                actual_severity=IncidentSeverity.HIGH,
                accuracy_classification=DetectionAccuracy.TRUE_POSITIVE,
                processing_time_ms=100.0,
                alerts_processed=1,
                correlation_count=1
            )
        ]
        
        report = tester.generate_accuracy_report()
        
        assert "timestamp" in report
        assert "overall_metrics" in report
        assert "performance_metrics" in report
        assert "scenario_type_breakdown" in report
        assert "failed_tests" in report
        assert "regression_status" in report
        
        # Check overall metrics
        overall = report["overall_metrics"]
        assert overall["total_tests"] == 1
        assert overall["accuracy"] == 1.0
        
        # Check performance metrics
        performance = report["performance_metrics"]
        assert performance["avg_processing_time_ms"] == 100.0
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, tester):
        """Test timeout handling in detection tests."""
        # Create a mock agent that times out
        slow_agent = MockDetectionAgent()
        
        async def slow_analyze(incident_data):
            await asyncio.sleep(2)  # Longer than timeout
            return AgentRecommendation(
                agent_name=AgentType.DETECTION,
                incident_id="test-incident",
                action_type=ActionType.NO_ACTION,
                action_id="slow-action-1",
                confidence=0.8,
                risk_level=RiskLevel.LOW,
                estimated_impact="medium",
                reasoning="Slow analysis",
                urgency=0.5
            )
        
        slow_agent.analyze_incident_data = slow_analyze
        
        # Create scenario with short timeout
        scenario = TestScenario(
            name="timeout_test",
            scenario_type=TestScenarioType.SINGLE_SOURCE_ALERT,
            alerts=[
                TestAlert(
                    source="cloudwatch",
                    metric_name="CPUUtilization",
                    value=95.0,
                    threshold=80.0,
                    timestamp=datetime.utcnow(),
                    severity="critical"
                )
            ],
            expected_incident=True,
            expected_confidence=0.8,
            expected_severity=IncidentSeverity.HIGH,
            description="Timeout test",
            timeout_seconds=1  # Short timeout
        )
        
        result = await tester.run_detection_test(slow_agent, scenario)
        
        assert result.error_message is not None
        assert "timeout" in result.error_message.lower()
        assert result.accuracy_classification == DetectionAccuracy.FALSE_NEGATIVE
        assert not result.detected_incident