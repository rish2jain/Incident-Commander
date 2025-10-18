"""
Detection Accuracy Testing and Validation (Task 4.3)

Comprehensive testing framework for detection agent accuracy with
known incident patterns, multi-source correlation validation, and
performance benchmarking for alert storm scenarios.
"""

import asyncio
import json
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import random
import statistics
from unittest.mock import AsyncMock, MagicMock

from src.utils.logging import get_logger
from src.models.incident import Incident, IncidentSeverity, BusinessImpact
from agents.detection.agent import RobustDetectionAgent
from src.services.monitoring import MonitoringDataSource

logger = get_logger(__name__)


class TestScenarioType(Enum):
    """Types of detection test scenarios."""
    SINGLE_SOURCE_ALERT = "single_source_alert"
    MULTI_SOURCE_CORRELATION = "multi_source_correlation"
    ALERT_STORM = "alert_storm"
    FALSE_POSITIVE = "false_positive"
    CASCADING_FAILURE = "cascading_failure"
    INTERMITTENT_ISSUE = "intermittent_issue"
    BASELINE_NOISE = "baseline_noise"


class DetectionAccuracy(Enum):
    """Detection accuracy classifications."""
    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    TRUE_NEGATIVE = "true_negative"
    FALSE_NEGATIVE = "false_negative"


@dataclass
class TestAlert:
    """Synthetic alert for testing."""
    source: str
    metric_name: str
    value: float
    threshold: float
    timestamp: datetime
    severity: str
    tags: Dict[str, str] = field(default_factory=dict)
    is_incident: bool = True  # Ground truth


@dataclass
class TestScenario:
    """Detection test scenario definition."""
    name: str
    scenario_type: TestScenarioType
    alerts: List[TestAlert]
    expected_incident: bool
    expected_confidence: float
    expected_severity: IncidentSeverity
    description: str
    timeout_seconds: int = 30


@dataclass
class DetectionTestResult:
    """Result of a detection test."""
    scenario_name: str
    scenario_type: TestScenarioType
    expected_incident: bool
    detected_incident: bool
    expected_confidence: float
    actual_confidence: float
    expected_severity: IncidentSeverity
    actual_severity: Optional[IncidentSeverity]
    accuracy_classification: DetectionAccuracy
    processing_time_ms: float
    alerts_processed: int
    correlation_count: int
    error_message: Optional[str] = None


@dataclass
class AccuracyMetrics:
    """Aggregated accuracy metrics."""
    total_tests: int
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    avg_processing_time_ms: float
    confidence_correlation: float


class DetectionAccuracyTester:
    """
    Comprehensive detection accuracy testing framework with
    synthetic scenarios, performance benchmarking, and regression validation.
    """
    
    def __init__(self):
        self.logger = logger
        
        # Test scenarios and results
        self.test_scenarios: List[TestScenario] = []
        self.test_results: List[DetectionTestResult] = []
        
        # Performance tracking
        self.performance_history = deque(maxlen=1000)
        self.accuracy_trends = defaultdict(list)
        
        # Regression baselines
        self.baseline_metrics: Optional[AccuracyMetrics] = None
        self.regression_threshold = 0.05  # 5% degradation threshold
        
        # Initialize test scenarios
        self._initialize_test_scenarios()
    
    def _initialize_test_scenarios(self):
        """Initialize comprehensive test scenarios."""
        
        # Single source alert scenarios
        self.test_scenarios.extend([
            TestScenario(
                name="high_cpu_single_source",
                scenario_type=TestScenarioType.SINGLE_SOURCE_ALERT,
                alerts=[
                    TestAlert(
                        source="cloudwatch",
                        metric_name="CPUUtilization",
                        value=95.0,
                        threshold=80.0,
                        timestamp=datetime.utcnow(),
                        severity="critical",
                        tags={"service": "web-api", "instance": "i-123456"}
                    )
                ],
                expected_incident=True,
                expected_confidence=0.8,
                expected_severity=IncidentSeverity.HIGH,
                description="Single high CPU alert should trigger incident"
            ),
            
            TestScenario(
                name="memory_leak_gradual",
                scenario_type=TestScenarioType.SINGLE_SOURCE_ALERT,
                alerts=[
                    TestAlert(
                        source="datadog",
                        metric_name="memory.usage",
                        value=0.92,
                        threshold=0.85,
                        timestamp=datetime.utcnow(),
                        severity="warning",
                        tags={"service": "background-worker", "host": "worker-01"}
                    )
                ],
                expected_incident=True,
                expected_confidence=0.7,
                expected_severity=IncidentSeverity.MEDIUM,
                description="Memory usage above threshold should be detected"
            )
        ])
        
        # Multi-source correlation scenarios
        self.test_scenarios.extend([
            TestScenario(
                name="database_cascade_correlation",
                scenario_type=TestScenarioType.MULTI_SOURCE_CORRELATION,
                alerts=[
                    TestAlert(
                        source="cloudwatch",
                        metric_name="DatabaseConnections",
                        value=450,
                        threshold=400,
                        timestamp=datetime.utcnow(),
                        severity="warning",
                        tags={"database": "primary-db"}
                    ),
                    TestAlert(
                        source="datadog",
                        metric_name="query.duration.p99",
                        value=5.2,
                        threshold=2.0,
                        timestamp=datetime.utcnow() + timedelta(seconds=30),
                        severity="critical",
                        tags={"database": "primary-db"}
                    ),
                    TestAlert(
                        source="application_logs",
                        metric_name="error_rate",
                        value=0.15,
                        threshold=0.05,
                        timestamp=datetime.utcnow() + timedelta(seconds=60),
                        severity="critical",
                        tags={"service": "api-gateway"}
                    )
                ],
                expected_incident=True,
                expected_confidence=0.95,
                expected_severity=IncidentSeverity.CRITICAL,
                description="Correlated database and application issues should have high confidence"
            ),
            
            TestScenario(
                name="network_partition_correlation",
                scenario_type=TestScenarioType.MULTI_SOURCE_CORRELATION,
                alerts=[
                    TestAlert(
                        source="cloudwatch",
                        metric_name="NetworkPacketsIn",
                        value=0,
                        threshold=1000,
                        timestamp=datetime.utcnow(),
                        severity="critical",
                        tags={"instance": "i-789012", "az": "us-east-1a"}
                    ),
                    TestAlert(
                        source="datadog",
                        metric_name="system.net.bytes_rcvd",
                        value=0,
                        threshold=1000000,
                        timestamp=datetime.utcnow() + timedelta(seconds=15),
                        severity="critical",
                        tags={"host": "web-01", "az": "us-east-1a"}
                    )
                ],
                expected_incident=True,
                expected_confidence=0.9,
                expected_severity=IncidentSeverity.CRITICAL,
                description="Network partition affecting multiple instances should correlate"
            )
        ])
        
        # Alert storm scenarios
        self.test_scenarios.extend([
            TestScenario(
                name="ddos_alert_storm",
                scenario_type=TestScenarioType.ALERT_STORM,
                alerts=self._generate_alert_storm(
                    count=1000,
                    base_metric="request_rate",
                    base_value=10000,
                    threshold=1000,
                    duration_seconds=300
                ),
                expected_incident=True,
                expected_confidence=0.85,
                expected_severity=IncidentSeverity.CRITICAL,
                description="DDoS attack generating 1000+ alerts should be detected efficiently",
                timeout_seconds=60
            ),
            
            TestScenario(
                name="cascading_microservice_storm",
                scenario_type=TestScenarioType.ALERT_STORM,
                alerts=self._generate_cascading_alerts(
                    services=["auth", "user", "order", "payment", "notification"],
                    alerts_per_service=200
                ),
                expected_incident=True,
                expected_confidence=0.9,
                expected_severity=IncidentSeverity.CRITICAL,
                description="Cascading failure across microservices should be correlated",
                timeout_seconds=90
            )
        ])
        
        # False positive scenarios
        self.test_scenarios.extend([
            TestScenario(
                name="maintenance_window_false_positive",
                scenario_type=TestScenarioType.FALSE_POSITIVE,
                alerts=[
                    TestAlert(
                        source="cloudwatch",
                        metric_name="CPUUtilization",
                        value=0,
                        threshold=10,
                        timestamp=datetime.utcnow(),
                        severity="warning",
                        tags={"service": "batch-processor", "maintenance": "true"}
                    )
                ],
                expected_incident=False,
                expected_confidence=0.2,
                expected_severity=IncidentSeverity.LOW,
                description="Maintenance window should not trigger incident"
            ),
            
            TestScenario(
                name="known_flaky_metric",
                scenario_type=TestScenarioType.FALSE_POSITIVE,
                alerts=[
                    TestAlert(
                        source="datadog",
                        metric_name="disk.io.wait",
                        value=0.95,
                        threshold=0.8,
                        timestamp=datetime.utcnow(),
                        severity="warning",
                        tags={"host": "analytics-01", "known_flaky": "true"}
                    )
                ],
                expected_incident=False,
                expected_confidence=0.3,
                expected_severity=IncidentSeverity.LOW,
                description="Known flaky metrics should have reduced confidence"
            )
        ])
        
        # Baseline noise scenarios
        self.test_scenarios.extend([
            TestScenario(
                name="normal_traffic_baseline",
                scenario_type=TestScenarioType.BASELINE_NOISE,
                alerts=self._generate_baseline_noise(count=50),
                expected_incident=False,
                expected_confidence=0.1,
                expected_severity=IncidentSeverity.LOW,
                description="Normal traffic variations should not trigger incidents"
            )
        ])
    
    def _generate_alert_storm(self, count: int, base_metric: str, base_value: float, 
                            threshold: float, duration_seconds: int) -> List[TestAlert]:
        """Generate synthetic alert storm for testing."""
        alerts = []
        start_time = datetime.utcnow()
        
        for i in range(count):
            # Vary timing within duration
            alert_time = start_time + timedelta(seconds=random.uniform(0, duration_seconds))
            
            # Add some variance to values
            value = base_value * random.uniform(0.8, 1.2)
            
            # Vary sources and instances
            sources = ["cloudwatch", "datadog", "prometheus"]
            instances = [f"i-{random.randint(100000, 999999)}" for _ in range(20)]
            
            alerts.append(TestAlert(
                source=random.choice(sources),
                metric_name=base_metric,
                value=value,
                threshold=threshold,
                timestamp=alert_time,
                severity="critical" if value > threshold * 2 else "warning",
                tags={
                    "instance": random.choice(instances),
                    "service": "web-frontend"
                }
            ))
        
        return alerts
    
    def _generate_cascading_alerts(self, services: List[str], alerts_per_service: int) -> List[TestAlert]:
        """Generate cascading failure alerts across services."""
        alerts = []
        start_time = datetime.utcnow()
        
        for i, service in enumerate(services):
            # Each service fails 30 seconds after the previous
            service_start = start_time + timedelta(seconds=i * 30)
            
            for j in range(alerts_per_service):
                alert_time = service_start + timedelta(seconds=random.uniform(0, 60))
                
                # Different types of alerts for each service
                metrics = ["error_rate", "response_time", "cpu_usage", "memory_usage"]
                metric = random.choice(metrics)
                
                # Values that indicate problems
                if metric == "error_rate":
                    value, threshold = 0.25, 0.05
                elif metric == "response_time":
                    value, threshold = 5.0, 1.0
                elif metric == "cpu_usage":
                    value, threshold = 95.0, 80.0
                else:  # memory_usage
                    value, threshold = 0.92, 0.85
                
                alerts.append(TestAlert(
                    source="datadog",
                    metric_name=f"{service}.{metric}",
                    value=value,
                    threshold=threshold,
                    timestamp=alert_time,
                    severity="critical",
                    tags={
                        "service": service,
                        "cascade_order": str(i)
                    }
                ))
        
        return alerts
    
    def _generate_baseline_noise(self, count: int) -> List[TestAlert]:
        """Generate normal baseline noise that shouldn't trigger incidents."""
        alerts = []
        start_time = datetime.utcnow()
        
        for i in range(count):
            alert_time = start_time + timedelta(seconds=random.uniform(0, 3600))
            
            # Normal variations that are close to but not exceeding thresholds
            metrics = [
                ("cpu_usage", 75.0, 80.0),
                ("memory_usage", 0.82, 0.85),
                ("response_time", 0.9, 1.0),
                ("error_rate", 0.04, 0.05)
            ]
            
            metric_name, value, threshold = random.choice(metrics)
            
            alerts.append(TestAlert(
                source="cloudwatch",
                metric_name=metric_name,
                value=value,
                threshold=threshold,
                timestamp=alert_time,
                severity="info",
                tags={"service": "background-service"},
                is_incident=False
            ))
        
        return alerts
    
    async def run_detection_test(self, agent: RobustDetectionAgent, scenario: TestScenario) -> DetectionTestResult:
        """Run a single detection test scenario."""
        start_time = time.time()
        
        try:
            # Mock monitoring data sources with scenario alerts
            mock_sources = self._create_mock_monitoring_sources(scenario.alerts)
            
            # Temporarily replace agent's monitoring sources
            original_sources = agent.monitoring_sources
            agent.monitoring_sources = mock_sources
            
            # Create synthetic incident data
            incident_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "test_framework",
                "alerts": [self._alert_to_dict(alert) for alert in scenario.alerts]
            }
            
            # Run detection with timeout
            try:
                recommendation = await asyncio.wait_for(
                    agent.analyze_incident_data(incident_data),
                    timeout=scenario.timeout_seconds
                )
                
                processing_time = (time.time() - start_time) * 1000
                
                # Determine if incident was detected
                detected_incident = recommendation.confidence > 0.5
                actual_severity = self._confidence_to_severity(recommendation.confidence)
                
                # Calculate accuracy classification
                accuracy_class = self._classify_accuracy(
                    scenario.expected_incident,
                    detected_incident
                )
                
                return DetectionTestResult(
                    scenario_name=scenario.name,
                    scenario_type=scenario.scenario_type,
                    expected_incident=scenario.expected_incident,
                    detected_incident=detected_incident,
                    expected_confidence=scenario.expected_confidence,
                    actual_confidence=recommendation.confidence,
                    expected_severity=scenario.expected_severity,
                    actual_severity=actual_severity,
                    accuracy_classification=accuracy_class,
                    processing_time_ms=processing_time,
                    alerts_processed=len(scenario.alerts),
                    correlation_count=1 if recommendation.reasoning else 0
                )
                
            except asyncio.TimeoutError:
                processing_time = (time.time() - start_time) * 1000
                return DetectionTestResult(
                    scenario_name=scenario.name,
                    scenario_type=scenario.scenario_type,
                    expected_incident=scenario.expected_incident,
                    detected_incident=False,
                    expected_confidence=scenario.expected_confidence,
                    actual_confidence=0.0,
                    expected_severity=scenario.expected_severity,
                    actual_severity=None,
                    accuracy_classification=DetectionAccuracy.FALSE_NEGATIVE,
                    processing_time_ms=processing_time,
                    alerts_processed=len(scenario.alerts),
                    correlation_count=0,
                    error_message=f"Detection timeout after {scenario.timeout_seconds}s"
                )
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            return DetectionTestResult(
                scenario_name=scenario.name,
                scenario_type=scenario.scenario_type,
                expected_incident=scenario.expected_incident,
                detected_incident=False,
                expected_confidence=scenario.expected_confidence,
                actual_confidence=0.0,
                expected_severity=scenario.expected_severity,
                actual_severity=None,
                accuracy_classification=DetectionAccuracy.FALSE_NEGATIVE,
                processing_time_ms=processing_time,
                alerts_processed=len(scenario.alerts),
                correlation_count=0,
                error_message=str(e)
            )
        
        finally:
            # Restore original monitoring sources
            if 'original_sources' in locals():
                agent.monitoring_sources = original_sources
    
    def _create_mock_monitoring_sources(self, alerts: List[TestAlert]) -> Dict[str, MonitoringDataSource]:
        """Create mock monitoring sources for test alerts."""
        sources = {}
        
        # Group alerts by source
        alerts_by_source = defaultdict(list)
        for alert in alerts:
            alerts_by_source[alert.source].append(alert)
        
        # Create mock source for each
        for source_name, source_alerts in alerts_by_source.items():
            mock_source = AsyncMock(spec=MonitoringDataSource)
            
            # Mock the get_recent_alerts method
            mock_alerts = []
            for alert in source_alerts:
                mock_alerts.append({
                    "metric_name": alert.metric_name,
                    "value": alert.value,
                    "threshold": alert.threshold,
                    "timestamp": alert.timestamp.isoformat(),
                    "severity": alert.severity,
                    "tags": alert.tags
                })
            
            mock_source.get_recent_alerts.return_value = mock_alerts
            mock_source.name = source_name
            
            sources[source_name] = mock_source
        
        return sources
    
    def _alert_to_dict(self, alert: TestAlert) -> Dict[str, Any]:
        """Convert TestAlert to dictionary format."""
        return {
            "source": alert.source,
            "metric_name": alert.metric_name,
            "value": alert.value,
            "threshold": alert.threshold,
            "timestamp": alert.timestamp.isoformat(),
            "severity": alert.severity,
            "tags": alert.tags,
            "is_incident": alert.is_incident
        }
    
    def _confidence_to_severity(self, confidence: float) -> IncidentSeverity:
        """Convert confidence score to incident severity."""
        if confidence >= 0.9:
            return IncidentSeverity.CRITICAL
        elif confidence >= 0.7:
            return IncidentSeverity.HIGH
        elif confidence >= 0.5:
            return IncidentSeverity.MEDIUM
        else:
            return IncidentSeverity.LOW
    
    def _classify_accuracy(self, expected: bool, actual: bool) -> DetectionAccuracy:
        """Classify detection accuracy."""
        if expected and actual:
            return DetectionAccuracy.TRUE_POSITIVE
        elif expected and not actual:
            return DetectionAccuracy.FALSE_NEGATIVE
        elif not expected and actual:
            return DetectionAccuracy.FALSE_POSITIVE
        else:
            return DetectionAccuracy.TRUE_NEGATIVE
    
    async def run_full_test_suite(self, agent: RobustDetectionAgent) -> AccuracyMetrics:
        """Run the complete detection accuracy test suite."""
        self.logger.info(f"Starting detection accuracy test suite with {len(self.test_scenarios)} scenarios")
        
        self.test_results = []
        
        # Run all test scenarios
        for scenario in self.test_scenarios:
            self.logger.info(f"Running test scenario: {scenario.name}")
            result = await self.run_detection_test(agent, scenario)
            self.test_results.append(result)
            
            # Log result
            if result.error_message:
                self.logger.warning(f"Test {scenario.name} failed: {result.error_message}")
            else:
                self.logger.info(f"Test {scenario.name}: {result.accuracy_classification.value}, "
                               f"confidence {result.actual_confidence:.3f}, "
                               f"time {result.processing_time_ms:.1f}ms")
        
        # Calculate aggregated metrics
        metrics = self._calculate_accuracy_metrics()
        
        # Store performance history
        self.performance_history.append({
            'timestamp': datetime.utcnow(),
            'metrics': metrics,
            'test_count': len(self.test_results)
        })
        
        # Check for regression
        if self.baseline_metrics:
            regression_detected = self._check_regression(metrics)
            if regression_detected:
                self.logger.warning("Detection accuracy regression detected!")
        
        return metrics
    
    def _calculate_accuracy_metrics(self) -> AccuracyMetrics:
        """Calculate aggregated accuracy metrics from test results."""
        if not self.test_results:
            return AccuracyMetrics(0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        # Count accuracy classifications
        tp = sum(1 for r in self.test_results if r.accuracy_classification == DetectionAccuracy.TRUE_POSITIVE)
        fp = sum(1 for r in self.test_results if r.accuracy_classification == DetectionAccuracy.FALSE_POSITIVE)
        tn = sum(1 for r in self.test_results if r.accuracy_classification == DetectionAccuracy.TRUE_NEGATIVE)
        fn = sum(1 for r in self.test_results if r.accuracy_classification == DetectionAccuracy.FALSE_NEGATIVE)
        
        total = len(self.test_results)
        
        # Calculate metrics
        accuracy = (tp + tn) / total if total > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Average processing time
        avg_processing_time = statistics.mean([r.processing_time_ms for r in self.test_results])
        
        # Confidence correlation (how well confidence matches expected)
        confidence_errors = [abs(r.actual_confidence - r.expected_confidence) for r in self.test_results]
        confidence_correlation = 1.0 - statistics.mean(confidence_errors)
        
        return AccuracyMetrics(
            total_tests=total,
            true_positives=tp,
            false_positives=fp,
            true_negatives=tn,
            false_negatives=fn,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            avg_processing_time_ms=avg_processing_time,
            confidence_correlation=confidence_correlation
        )
    
    def _check_regression(self, current_metrics: AccuracyMetrics) -> bool:
        """Check if current metrics show regression from baseline."""
        if not self.baseline_metrics:
            return False
        
        # Check key metrics for regression
        accuracy_regression = (self.baseline_metrics.accuracy - current_metrics.accuracy) > self.regression_threshold
        precision_regression = (self.baseline_metrics.precision - current_metrics.precision) > self.regression_threshold
        recall_regression = (self.baseline_metrics.recall - current_metrics.recall) > self.regression_threshold
        
        # Check performance regression (50% slower)
        performance_regression = (current_metrics.avg_processing_time_ms / self.baseline_metrics.avg_processing_time_ms) > 1.5
        
        return accuracy_regression or precision_regression or recall_regression or performance_regression
    
    def set_baseline_metrics(self, metrics: AccuracyMetrics):
        """Set baseline metrics for regression detection."""
        self.baseline_metrics = metrics
        self.logger.info(f"Set baseline metrics: accuracy={metrics.accuracy:.3f}, "
                        f"precision={metrics.precision:.3f}, recall={metrics.recall:.3f}")
    
    async def run_alert_storm_benchmark(self, agent: RobustDetectionAgent, 
                                      alert_counts: List[int] = None) -> Dict[str, Any]:
        """Run alert storm performance benchmarking."""
        if alert_counts is None:
            alert_counts = [100, 500, 1000, 5000, 10000, 50000]
        
        benchmark_results = {}
        
        for count in alert_counts:
            self.logger.info(f"Running alert storm benchmark with {count} alerts")
            
            # Generate alert storm scenario
            storm_scenario = TestScenario(
                name=f"benchmark_storm_{count}",
                scenario_type=TestScenarioType.ALERT_STORM,
                alerts=self._generate_alert_storm(
                    count=count,
                    base_metric="request_rate",
                    base_value=10000,
                    threshold=1000,
                    duration_seconds=60
                ),
                expected_incident=True,
                expected_confidence=0.8,
                expected_severity=IncidentSeverity.CRITICAL,
                description=f"Benchmark with {count} alerts",
                timeout_seconds=120
            )
            
            # Run test multiple times for statistical significance
            times = []
            success_count = 0
            
            for run in range(5):  # 5 runs per alert count
                result = await self.run_detection_test(agent, storm_scenario)
                times.append(result.processing_time_ms)
                
                if not result.error_message and result.detected_incident:
                    success_count += 1
            
            benchmark_results[count] = {
                'avg_time_ms': statistics.mean(times),
                'min_time_ms': min(times),
                'max_time_ms': max(times),
                'std_time_ms': statistics.stdev(times) if len(times) > 1 else 0,
                'success_rate': success_count / 5,
                'throughput_alerts_per_sec': count / (statistics.mean(times) / 1000)
            }
            
            self.logger.info(f"Alert count {count}: avg_time={benchmark_results[count]['avg_time_ms']:.1f}ms, "
                           f"success_rate={benchmark_results[count]['success_rate']:.1f}, "
                           f"throughput={benchmark_results[count]['throughput_alerts_per_sec']:.1f} alerts/sec")
        
        return benchmark_results
    
    def generate_accuracy_report(self) -> Dict[str, Any]:
        """Generate comprehensive accuracy report."""
        if not self.test_results:
            return {"error": "No test results available"}
        
        metrics = self._calculate_accuracy_metrics()
        
        # Results by scenario type
        results_by_type = defaultdict(list)
        for result in self.test_results:
            results_by_type[result.scenario_type].append(result)
        
        type_metrics = {}
        for scenario_type, type_results in results_by_type.items():
            tp = sum(1 for r in type_results if r.accuracy_classification == DetectionAccuracy.TRUE_POSITIVE)
            fp = sum(1 for r in type_results if r.accuracy_classification == DetectionAccuracy.FALSE_POSITIVE)
            tn = sum(1 for r in type_results if r.accuracy_classification == DetectionAccuracy.TRUE_NEGATIVE)
            fn = sum(1 for r in type_results if r.accuracy_classification == DetectionAccuracy.FALSE_NEGATIVE)
            
            total = len(type_results)
            accuracy = (tp + tn) / total if total > 0 else 0.0
            avg_time = statistics.mean([r.processing_time_ms for r in type_results])
            
            type_metrics[scenario_type.value] = {
                'total_tests': total,
                'accuracy': accuracy,
                'avg_processing_time_ms': avg_time,
                'true_positives': tp,
                'false_positives': fp,
                'true_negatives': tn,
                'false_negatives': fn
            }
        
        # Failed tests
        failed_tests = [
            {
                'name': r.scenario_name,
                'error': r.error_message,
                'expected_confidence': r.expected_confidence,
                'actual_confidence': r.actual_confidence
            }
            for r in self.test_results if r.error_message
        ]
        
        # Performance analysis
        processing_times = [r.processing_time_ms for r in self.test_results if not r.error_message]
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'overall_metrics': {
                'total_tests': metrics.total_tests,
                'accuracy': metrics.accuracy,
                'precision': metrics.precision,
                'recall': metrics.recall,
                'f1_score': metrics.f1_score,
                'confidence_correlation': metrics.confidence_correlation
            },
            'performance_metrics': {
                'avg_processing_time_ms': metrics.avg_processing_time_ms,
                'min_processing_time_ms': min(processing_times) if processing_times else 0,
                'max_processing_time_ms': max(processing_times) if processing_times else 0,
                'p95_processing_time_ms': np.percentile(processing_times, 95) if processing_times else 0,
                'p99_processing_time_ms': np.percentile(processing_times, 99) if processing_times else 0
            },
            'scenario_type_breakdown': type_metrics,
            'failed_tests': failed_tests,
            'regression_status': {
                'baseline_set': self.baseline_metrics is not None,
                'regression_detected': self._check_regression(metrics) if self.baseline_metrics else False,
                'regression_threshold': self.regression_threshold
            }
        }
        
        return report
    
    async def run_continuous_accuracy_monitoring(self, agent: RobustDetectionAgent, 
                                               interval_hours: int = 24):
        """Run continuous accuracy monitoring and regression detection."""
        self.logger.info(f"Starting continuous detection accuracy monitoring with {interval_hours}h intervals")
        
        # Set initial baseline if not set
        if not self.baseline_metrics:
            initial_metrics = await self.run_full_test_suite(agent)
            self.set_baseline_metrics(initial_metrics)
        
        while True:
            try:
                # Run test suite
                current_metrics = await self.run_full_test_suite(agent)
                
                # Generate report
                report = self.generate_accuracy_report()
                
                # Check for significant changes
                if self._check_regression(current_metrics):
                    self.logger.error("Detection accuracy regression detected!")
                    # In production, this would trigger alerts
                
                # Update accuracy trends
                self.accuracy_trends['accuracy'].append({
                    'timestamp': datetime.utcnow(),
                    'value': current_metrics.accuracy
                })
                self.accuracy_trends['precision'].append({
                    'timestamp': datetime.utcnow(),
                    'value': current_metrics.precision
                })
                self.accuracy_trends['recall'].append({
                    'timestamp': datetime.utcnow(),
                    'value': current_metrics.recall
                })
                
                # Wait for next interval
                await asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                self.logger.error(f"Continuous accuracy monitoring error: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry


# Example usage and testing
async def main():
    """Example usage of detection accuracy testing."""
    from agents.detection.agent import RobustDetectionAgent
    
    # Initialize detection agent and tester
    agent = RobustDetectionAgent()
    tester = DetectionAccuracyTester()
    
    # Run full test suite
    print("Running detection accuracy test suite...")
    metrics = await tester.run_full_test_suite(agent)
    
    print(f"\nAccuracy Results:")
    print(f"Overall Accuracy: {metrics.accuracy:.3f}")
    print(f"Precision: {metrics.precision:.3f}")
    print(f"Recall: {metrics.recall:.3f}")
    print(f"F1 Score: {metrics.f1_score:.3f}")
    print(f"Avg Processing Time: {metrics.avg_processing_time_ms:.1f}ms")
    
    # Set as baseline
    tester.set_baseline_metrics(metrics)
    
    # Run alert storm benchmark
    print("\nRunning alert storm benchmark...")
    benchmark_results = await tester.run_alert_storm_benchmark(agent)
    
    for count, results in benchmark_results.items():
        print(f"Alert count {count}: {results['avg_time_ms']:.1f}ms avg, "
              f"{results['throughput_alerts_per_sec']:.1f} alerts/sec")
    
    # Generate comprehensive report
    report = tester.generate_accuracy_report()
    print(f"\nGenerated accuracy report with {len(report['failed_tests'])} failed tests")


if __name__ == "__main__":
    asyncio.run(main())