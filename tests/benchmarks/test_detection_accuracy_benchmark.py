"""
Deep Detection Accuracy Benchmarking and Regression Harness (Task 4.3)

Comprehensive benchmarking system for detection agent accuracy with
regression testing, performance tracking, and continuous evaluation.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np
from unittest.mock import Mock, AsyncMock, patch

from agents.detection.agent import RobustDetectionAgent
from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact
from src.models.agent import AgentRecommendation, AgentType, ActionType, RiskLevel
from src.utils.logging import get_logger


logger = get_logger(__name__)


@dataclass
class DetectionBenchmarkResult:
    """Results from detection accuracy benchmarking."""
    test_case_id: str
    incident_type: str
    expected_confidence: float
    actual_confidence: float
    expected_action: str
    actual_action: str
    processing_time_ms: float
    accuracy_score: float
    false_positive: bool
    false_negative: bool
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BenchmarkSuite:
    """Collection of benchmark test cases."""
    suite_name: str
    test_cases: List[Dict[str, Any]]
    expected_accuracy_threshold: float = 0.85
    performance_threshold_ms: float = 30000  # 30 seconds


class DetectionAccuracyBenchmark:
    """
    Comprehensive detection accuracy benchmarking system with
    regression testing and performance tracking.
    """
    
    def __init__(self):
        self.logger = logger
        self.benchmark_results: List[DetectionBenchmarkResult] = []
        self.historical_results: Dict[str, List[DetectionBenchmarkResult]] = defaultdict(list)
        self.regression_threshold = 0.05  # 5% accuracy drop triggers regression alert
        
        # Load benchmark test suites
        self.benchmark_suites = self._create_benchmark_suites()
    
    def _create_benchmark_suites(self) -> Dict[str, BenchmarkSuite]:
        """Create comprehensive benchmark test suites."""
        return {
            "database_incidents": BenchmarkSuite(
                suite_name="Database Incident Detection",
                expected_accuracy_threshold=0.90,
                test_cases=[
                    {
                        "test_case_id": "db_001",
                        "incident_type": "database_connection_pool_exhaustion",
                        "title": "Database Connection Pool Exhausted",
                        "description": "Connection pool exhausted, 500 errors increasing",
                        "severity": IncidentSeverity.CRITICAL,
                        "expected_confidence": 0.95,
                        "expected_action": "restart_database_service",
                        "monitoring_data": {
                            "cpu_usage": 85.0,
                            "memory_usage": 78.0,
                            "connection_count": 500,
                            "error_rate": 0.25
                        }
                    },
                    {
                        "test_case_id": "db_002", 
                        "incident_type": "database_slow_queries",
                        "title": "Database Query Performance Degradation",
                        "description": "Query response times increased 300%, timeout errors",
                        "severity": IncidentSeverity.HIGH,
                        "expected_confidence": 0.88,
                        "expected_action": "optimize_database_queries",
                        "monitoring_data": {
                            "query_time_avg": 5.2,
                            "query_time_p95": 12.8,
                            "timeout_errors": 45,
                            "active_connections": 320
                        }
                    },
                    {
                        "test_case_id": "db_003",
                        "incident_type": "database_deadlock",
                        "title": "Database Deadlock Detection",
                        "description": "Multiple deadlock errors detected in transaction logs",
                        "severity": IncidentSeverity.MEDIUM,
                        "expected_confidence": 0.82,
                        "expected_action": "resolve_database_deadlocks",
                        "monitoring_data": {
                            "deadlock_count": 15,
                            "transaction_rollbacks": 28,
                            "lock_wait_time": 2.5
                        }
                    }
                ]
            ),
            
            "api_incidents": BenchmarkSuite(
                suite_name="API Gateway Incident Detection",
                expected_accuracy_threshold=0.87,
                test_cases=[
                    {
                        "test_case_id": "api_001",
                        "incident_type": "api_rate_limit_exceeded",
                        "title": "API Rate Limit Exceeded",
                        "description": "429 errors spiking, rate limit threshold reached",
                        "severity": IncidentSeverity.HIGH,
                        "expected_confidence": 0.92,
                        "expected_action": "increase_api_rate_limits",
                        "monitoring_data": {
                            "requests_per_second": 5000,
                            "rate_limit_errors": 1200,
                            "response_time_p99": 8.5
                        }
                    },
                    {
                        "test_case_id": "api_002",
                        "incident_type": "api_gateway_overload",
                        "title": "API Gateway Overload",
                        "description": "Gateway CPU at 95%, response times degraded",
                        "severity": IncidentSeverity.CRITICAL,
                        "expected_confidence": 0.94,
                        "expected_action": "scale_api_gateway",
                        "monitoring_data": {
                            "gateway_cpu": 95.0,
                            "response_time_avg": 3.2,
                            "queue_depth": 850
                        }
                    }
                ]
            ),
            
            "infrastructure_incidents": BenchmarkSuite(
                suite_name="Infrastructure Incident Detection",
                expected_accuracy_threshold=0.85,
                test_cases=[
                    {
                        "test_case_id": "infra_001",
                        "incident_type": "memory_leak",
                        "title": "Application Memory Leak",
                        "description": "Memory usage steadily increasing, GC pressure high",
                        "severity": IncidentSeverity.MEDIUM,
                        "expected_confidence": 0.86,
                        "expected_action": "restart_application_service",
                        "monitoring_data": {
                            "memory_usage_trend": [65, 68, 72, 76, 81, 85],
                            "gc_frequency": 45,
                            "heap_size": "2.1GB"
                        }
                    },
                    {
                        "test_case_id": "infra_002",
                        "incident_type": "disk_space_critical",
                        "title": "Disk Space Critical",
                        "description": "Disk usage at 95%, log files growing rapidly",
                        "severity": IncidentSeverity.HIGH,
                        "expected_confidence": 0.91,
                        "expected_action": "cleanup_disk_space",
                        "monitoring_data": {
                            "disk_usage_percent": 95.2,
                            "log_growth_rate": "500MB/hour",
                            "available_space": "2.1GB"
                        }
                    }
                ]
            ),
            
            "edge_cases": BenchmarkSuite(
                suite_name="Edge Case Detection",
                expected_accuracy_threshold=0.75,  # Lower threshold for edge cases
                test_cases=[
                    {
                        "test_case_id": "edge_001",
                        "incident_type": "intermittent_failure",
                        "title": "Intermittent Service Failure",
                        "description": "Sporadic failures, no clear pattern in metrics",
                        "severity": IncidentSeverity.LOW,
                        "expected_confidence": 0.65,
                        "expected_action": "monitor_and_investigate",
                        "monitoring_data": {
                            "error_rate": 0.02,
                            "error_pattern": "random",
                            "affected_users": 12
                        }
                    },
                    {
                        "test_case_id": "edge_002",
                        "incident_type": "false_alarm",
                        "title": "Monitoring False Alarm",
                        "description": "Alert triggered but no actual service impact",
                        "severity": IncidentSeverity.LOW,
                        "expected_confidence": 0.30,  # Should have low confidence
                        "expected_action": "dismiss_alert",
                        "monitoring_data": {
                            "metric_spike": True,
                            "user_impact": False,
                            "service_health": "normal"
                        }
                    }
                ]
            )
        }
    
    async def run_comprehensive_benchmark(self, agent: RobustDetectionAgent) -> Dict[str, Any]:
        """Run comprehensive detection accuracy benchmark."""
        self.logger.info("Starting comprehensive detection accuracy benchmark")
        
        benchmark_results = {}
        overall_results = []
        
        for suite_name, suite in self.benchmark_suites.items():
            self.logger.info(f"Running benchmark suite: {suite_name}")
            
            suite_results = await self._run_benchmark_suite(agent, suite)
            benchmark_results[suite_name] = suite_results
            overall_results.extend(suite_results)
        
        # Calculate overall metrics
        overall_metrics = self._calculate_benchmark_metrics(overall_results)
        
        # Check for regressions
        regression_analysis = await self._analyze_regressions(overall_results)
        
        # Generate performance report
        performance_report = self._generate_performance_report(overall_results)
        
        return {
            "benchmark_timestamp": datetime.utcnow().isoformat(),
            "suite_results": benchmark_results,
            "overall_metrics": overall_metrics,
            "regression_analysis": regression_analysis,
            "performance_report": performance_report,
            "total_test_cases": len(overall_results),
            "benchmark_passed": overall_metrics["accuracy"] >= 0.85
        }
    
    async def _run_benchmark_suite(self, agent: RobustDetectionAgent, suite: BenchmarkSuite) -> List[DetectionBenchmarkResult]:
        """Run a specific benchmark suite."""
        results = []
        
        for test_case in suite.test_cases:
            result = await self._run_single_benchmark(agent, test_case)
            results.append(result)
        
        return results
    
    async def _run_single_benchmark(self, agent: RobustDetectionAgent, test_case: Dict[str, Any]) -> DetectionBenchmarkResult:
        """Run a single benchmark test case."""
        # Create incident from test case
        business_impact = BusinessImpact(
            service_tier=ServiceTier.TIER_1,
            affected_users=test_case.get("affected_users", 1000),
            revenue_impact_per_minute=test_case.get("revenue_impact", 500.0)
        )
        
        from src.models.incident import IncidentMetadata
        
        metadata = IncidentMetadata(
            source_system="benchmark_test",
            alert_ids=[test_case["test_case_id"]]
        )
        
        incident = Incident(
            title=test_case["title"],
            description=test_case["description"],
            severity=test_case["severity"],
            business_impact=business_impact,
            metadata=metadata
        )
        
        # Measure processing time
        start_time = time.time()
        
        try:
            recommendation = await agent.analyze_incident(incident)
            processing_time_ms = (time.time() - start_time) * 1000
                
            # Calculate accuracy metrics
            accuracy_score = self._calculate_accuracy_score(
                test_case["expected_confidence"],
                recommendation.confidence,
                test_case["expected_action"],
                recommendation.action_id
            )
            
            # Determine false positive/negative
            false_positive = recommendation.confidence > 0.8 and test_case["expected_confidence"] < 0.5
            false_negative = recommendation.confidence < 0.5 and test_case["expected_confidence"] > 0.8
            
            return DetectionBenchmarkResult(
                test_case_id=test_case["test_case_id"],
                incident_type=test_case["incident_type"],
                expected_confidence=test_case["expected_confidence"],
                actual_confidence=recommendation.confidence,
                expected_action=test_case["expected_action"],
                actual_action=recommendation.action_id,
                processing_time_ms=processing_time_ms,
                accuracy_score=accuracy_score,
                false_positive=false_positive,
                false_negative=false_negative
            )
            
        except Exception as e:
            self.logger.error(f"Benchmark test case {test_case['test_case_id']} failed: {e}")
            
            return DetectionBenchmarkResult(
                test_case_id=test_case["test_case_id"],
                incident_type=test_case["incident_type"],
                expected_confidence=test_case["expected_confidence"],
                actual_confidence=0.0,
                expected_action=test_case["expected_action"],
                actual_action="error",
                processing_time_ms=(time.time() - start_time) * 1000,
                accuracy_score=0.0,
                false_positive=False,
                false_negative=True
            )
    
    def _calculate_accuracy_score(self, expected_conf: float, actual_conf: float, 
                                expected_action: str, actual_action: str) -> float:
        """Calculate accuracy score for a test case."""
        # Confidence accuracy (70% weight)
        conf_diff = abs(expected_conf - actual_conf)
        conf_accuracy = max(0, 1 - (conf_diff / 0.5))  # Normalize to 0-1
        
        # Action accuracy (30% weight)
        action_accuracy = 1.0 if expected_action.lower() in actual_action.lower() else 0.0
        
        return (conf_accuracy * 0.7) + (action_accuracy * 0.3)
    
    def _calculate_benchmark_metrics(self, results: List[DetectionBenchmarkResult]) -> Dict[str, Any]:
        """Calculate overall benchmark metrics."""
        if not results:
            return {}
        
        accuracy_scores = [r.accuracy_score for r in results]
        processing_times = [r.processing_time_ms for r in results]
        
        return {
            "accuracy": np.mean(accuracy_scores),
            "accuracy_std": np.std(accuracy_scores),
            "min_accuracy": np.min(accuracy_scores),
            "max_accuracy": np.max(accuracy_scores),
            "avg_processing_time_ms": np.mean(processing_times),
            "p95_processing_time_ms": np.percentile(processing_times, 95),
            "p99_processing_time_ms": np.percentile(processing_times, 99),
            "false_positive_rate": sum(1 for r in results if r.false_positive) / len(results),
            "false_negative_rate": sum(1 for r in results if r.false_negative) / len(results),
            "total_test_cases": len(results),
            "passed_test_cases": sum(1 for r in results if r.accuracy_score >= 0.7)
        }
    
    async def _analyze_regressions(self, current_results: List[DetectionBenchmarkResult]) -> Dict[str, Any]:
        """Analyze for performance regressions compared to historical data."""
        regression_analysis = {
            "regressions_detected": False,
            "regression_details": [],
            "accuracy_trend": "stable",
            "performance_trend": "stable"
        }
        
        # Group current results by test case ID
        current_by_id = {r.test_case_id: r for r in current_results}
        
        # Compare with historical results
        for test_case_id, current_result in current_by_id.items():
            historical = self.historical_results.get(test_case_id, [])
            
            if len(historical) >= 3:  # Need at least 3 historical results
                # Calculate historical average
                hist_accuracy = np.mean([h.accuracy_score for h in historical[-5:]])  # Last 5 runs
                hist_performance = np.mean([h.processing_time_ms for h in historical[-5:]])
                
                # Check for accuracy regression
                accuracy_drop = hist_accuracy - current_result.accuracy_score
                if accuracy_drop > self.regression_threshold:
                    regression_analysis["regressions_detected"] = True
                    regression_analysis["regression_details"].append({
                        "test_case_id": test_case_id,
                        "type": "accuracy_regression",
                        "historical_accuracy": hist_accuracy,
                        "current_accuracy": current_result.accuracy_score,
                        "accuracy_drop": accuracy_drop
                    })
                
                # Check for performance regression (>50% slower)
                performance_increase = (current_result.processing_time_ms - hist_performance) / hist_performance
                if performance_increase > 0.5:
                    regression_analysis["regressions_detected"] = True
                    regression_analysis["regression_details"].append({
                        "test_case_id": test_case_id,
                        "type": "performance_regression",
                        "historical_time_ms": hist_performance,
                        "current_time_ms": current_result.processing_time_ms,
                        "performance_increase_percent": performance_increase * 100
                    })
        
        # Store current results as historical data
        for result in current_results:
            self.historical_results[result.test_case_id].append(result)
            # Keep only last 10 results per test case
            if len(self.historical_results[result.test_case_id]) > 10:
                self.historical_results[result.test_case_id] = self.historical_results[result.test_case_id][-10:]
        
        return regression_analysis
    
    def _generate_performance_report(self, results: List[DetectionBenchmarkResult]) -> Dict[str, Any]:
        """Generate detailed performance report."""
        # Group by incident type
        by_type = defaultdict(list)
        for result in results:
            by_type[result.incident_type].append(result)
        
        type_performance = {}
        for incident_type, type_results in by_type.items():
            type_performance[incident_type] = {
                "accuracy": np.mean([r.accuracy_score for r in type_results]),
                "avg_processing_time_ms": np.mean([r.processing_time_ms for r in type_results]),
                "test_cases": len(type_results),
                "false_positive_rate": sum(1 for r in type_results if r.false_positive) / len(type_results),
                "false_negative_rate": sum(1 for r in type_results if r.false_negative) / len(type_results)
            }
        
        # Identify best and worst performing categories
        best_category = max(type_performance.items(), key=lambda x: x[1]["accuracy"])
        worst_category = min(type_performance.items(), key=lambda x: x[1]["accuracy"])
        
        return {
            "performance_by_type": type_performance,
            "best_performing_category": {
                "type": best_category[0],
                "accuracy": best_category[1]["accuracy"]
            },
            "worst_performing_category": {
                "type": worst_category[0],
                "accuracy": worst_category[1]["accuracy"]
            },
            "recommendations": self._generate_improvement_recommendations(type_performance)
        }
    
    def _generate_improvement_recommendations(self, type_performance: Dict[str, Dict]) -> List[str]:
        """Generate recommendations for improving detection accuracy."""
        recommendations = []
        
        for incident_type, metrics in type_performance.items():
            if metrics["accuracy"] < 0.8:
                recommendations.append(f"Improve {incident_type} detection accuracy (currently {metrics['accuracy']:.2f})")
            
            if metrics["false_positive_rate"] > 0.1:
                recommendations.append(f"Reduce false positives for {incident_type} (currently {metrics['false_positive_rate']:.1%})")
            
            if metrics["avg_processing_time_ms"] > 30000:
                recommendations.append(f"Optimize processing time for {incident_type} (currently {metrics['avg_processing_time_ms']:.0f}ms)")
        
        return recommendations
    
    async def run_continuous_benchmark(self, agent: RobustDetectionAgent, interval_hours: int = 24) -> None:
        """Run continuous benchmarking for regression detection."""
        self.logger.info(f"Starting continuous benchmarking with {interval_hours}h intervals")
        
        while True:
            try:
                results = await self.run_comprehensive_benchmark(agent)
                
                # Log results
                self.logger.info(f"Benchmark completed - Accuracy: {results['overall_metrics']['accuracy']:.3f}")
                
                # Check for regressions
                if results["regression_analysis"]["regressions_detected"]:
                    self.logger.warning("Performance regressions detected!")
                    for regression in results["regression_analysis"]["regression_details"]:
                        self.logger.warning(f"Regression: {regression}")
                
                # Wait for next interval
                await asyncio.sleep(interval_hours * 3600)
                
            except Exception as e:
                self.logger.error(f"Continuous benchmark error: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retry


# Test classes for the benchmarking system
class TestDetectionAccuracyBenchmark:
    """Test the detection accuracy benchmarking system."""
    
    @pytest.fixture
    def benchmark_system(self):
        """Create benchmark system for testing."""
        return DetectionAccuracyBenchmark()
    
    @pytest.fixture
    def mock_detection_agent(self):
        """Create mock detection agent."""
        agent = Mock(spec=RobustDetectionAgent)
        agent.analyze_incident = AsyncMock()
        return agent
    
    @pytest.mark.asyncio
    async def test_comprehensive_benchmark(self, benchmark_system, mock_detection_agent):
        """Test comprehensive benchmark execution."""
        # Mock agent responses
        mock_detection_agent.analyze_incident.return_value = AgentRecommendation(
            agent_name=AgentType.DETECTION,
            incident_id="test-incident-123",
            action_type="restart_service",
            action_id="restart_database_service",
            confidence=0.9,
            risk_level="medium",
            estimated_impact="Service restart will resolve connection issues",
            reasoning="High confidence detection based on connection pool metrics",
            urgency=0.8
        )
        
        results = await benchmark_system.run_comprehensive_benchmark(mock_detection_agent)
        
        assert "benchmark_timestamp" in results
        assert "suite_results" in results
        assert "overall_metrics" in results
        assert "regression_analysis" in results
        assert results["total_test_cases"] > 0
    
    @pytest.mark.asyncio
    async def test_regression_detection(self, benchmark_system, mock_detection_agent):
        """Test regression detection functionality."""
        # Add some historical data
        historical_result = DetectionBenchmarkResult(
            test_case_id="db_001",
            incident_type="database_connection_pool_exhaustion",
            expected_confidence=0.95,
            actual_confidence=0.92,
            expected_action="restart_database_service",
            actual_action="restart_database_service",
            processing_time_ms=1500.0,
            accuracy_score=0.95,
            false_positive=False,
            false_negative=False
        )
        
        benchmark_system.historical_results["db_001"] = [historical_result] * 5
        
        # Mock current result with regression
        mock_detection_agent.analyze_incident.return_value = AgentRecommendation(
            agent_name=AgentType.DETECTION,
            incident_id="test-incident-123",
            action_type="restart_service",
            action_id="restart_database_service",
            confidence=0.7,  # Significant drop
            risk_level="medium",
            estimated_impact="Service restart may resolve issues",
            reasoning="Lower confidence due to incomplete data",
            urgency=0.6
        )
        
        results = await benchmark_system.run_comprehensive_benchmark(mock_detection_agent)
        
        # Should detect regression
        assert results["regression_analysis"]["regressions_detected"] is True
    
    def test_accuracy_calculation(self, benchmark_system):
        """Test accuracy score calculation."""
        # Perfect match
        score = benchmark_system._calculate_accuracy_score(0.9, 0.9, "restart_service", "restart_service")
        assert score == 1.0
        
        # Confidence mismatch
        score = benchmark_system._calculate_accuracy_score(0.9, 0.5, "restart_service", "restart_service")
        assert 0.3 < score < 0.7  # Should be reduced but not zero
        
        # Action mismatch
        score = benchmark_system._calculate_accuracy_score(0.9, 0.9, "restart_service", "scale_service")
        assert 0.6 < score < 0.8  # Should be reduced by action weight
    
    def test_benchmark_metrics_calculation(self, benchmark_system):
        """Test benchmark metrics calculation."""
        results = [
            DetectionBenchmarkResult(
                test_case_id="test_1",
                incident_type="test",
                expected_confidence=0.9,
                actual_confidence=0.85,
                expected_action="action",
                actual_action="action",
                processing_time_ms=1000.0,
                accuracy_score=0.9,
                false_positive=False,
                false_negative=False
            ),
            DetectionBenchmarkResult(
                test_case_id="test_2",
                incident_type="test",
                expected_confidence=0.8,
                actual_confidence=0.75,
                expected_action="action",
                actual_action="action",
                processing_time_ms=1500.0,
                accuracy_score=0.8,
                false_positive=False,
                false_negative=False
            )
        ]
        
        metrics = benchmark_system._calculate_benchmark_metrics(results)
        
        assert abs(metrics["accuracy"] - 0.85) < 0.001  # Average of 0.9 and 0.8
        assert metrics["avg_processing_time_ms"] == 1250.0  # Average of 1000 and 1500
        assert metrics["total_test_cases"] == 2
        assert metrics["false_positive_rate"] == 0.0
        assert metrics["false_negative_rate"] == 0.0