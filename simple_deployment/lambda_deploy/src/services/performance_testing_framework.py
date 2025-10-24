"""
Performance Testing and Benchmarking Framework (Task 15.3)

Comprehensive performance testing for 1000+ concurrent incidents,
load testing, capacity planning, and performance regression detection.
"""

import asyncio
import time
import json
import statistics
import psutil
import resource
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import concurrent.futures
import threading
import random
import numpy as np
from unittest.mock import AsyncMock, MagicMock

from src.utils.logging import get_logger
from src.models.incident import Incident, IncidentSeverity, BusinessImpact
from src.services.agent_swarm_coordinator import AgentSwarmCoordinator

logger = get_logger(__name__)


class LoadTestType(Enum):
    """Types of load tests."""
    CONCURRENT_INCIDENTS = "concurrent_incidents"
    ALERT_STORM = "alert_storm"
    SUSTAINED_LOAD = "sustained_load"
    SPIKE_LOAD = "spike_load"
    STRESS_TEST = "stress_test"
    ENDURANCE_TEST = "endurance_test"
    CAPACITY_TEST = "capacity_test"


class PerformanceMetric(Enum):
    """Performance metrics to track."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_IO = "disk_io"
    NETWORK_IO = "network_io"
    CONCURRENT_USERS = "concurrent_users"
    QUEUE_DEPTH = "queue_depth"
    MTTR = "mttr"  # Mean Time To Resolution


@dataclass
class LoadTestConfiguration:
    """Configuration for a load test."""
    name: str
    test_type: LoadTestType
    target_load: int  # Number of concurrent incidents/requests
    duration_seconds: int
    ramp_up_seconds: int
    ramp_down_seconds: int
    success_criteria: Dict[str, float]  # metric -> threshold
    incident_patterns: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class PerformanceMeasurement:
    """Single performance measurement."""
    timestamp: datetime
    metric: PerformanceMetric
    value: float
    unit: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoadTestResult:
    """Result of a load test execution."""
    configuration: LoadTestConfiguration
    start_time: datetime
    end_time: datetime
    success: bool
    measurements: List[PerformanceMeasurement]
    summary_stats: Dict[str, Dict[str, float]]  # metric -> {min, max, avg, p95, p99}
    errors: List[str]
    resource_usage: Dict[str, Any]
    bottlenecks_detected: List[str]


@dataclass
class BenchmarkResult:
    """Benchmark comparison result."""
    test_name: str
    baseline_stats: Dict[str, float]
    current_stats: Dict[str, float]
    performance_change: Dict[str, float]  # percentage change
    regression_detected: bool
    improvement_detected: bool


class PerformanceTestingFramework:
    """
    Comprehensive performance testing and benchmarking framework
    for the Autonomous Incident Commander system.
    """
    
    def __init__(self):
        self.logger = logger
        
        # Test configurations
        self.test_configurations: List[LoadTestConfiguration] = []
        self.test_results: List[LoadTestResult] = []
        
        # Performance monitoring
        self.performance_history = deque(maxlen=10000)
        self.baseline_metrics: Dict[str, Dict[str, float]] = {}
        
        # Resource monitoring
        self.resource_monitor_active = False
        self.resource_measurements = deque(maxlen=1000)
        
        # Load generation
        self.active_load_generators = []
        self.incident_counter = 0
        
        # Initialize test configurations
        self._initialize_test_configurations()
    
    def _initialize_test_configurations(self):
        """Initialize standard performance test configurations."""
        
        # Concurrent incidents test (main requirement: 1000+ concurrent incidents)
        self.test_configurations.append(LoadTestConfiguration(
            name="concurrent_incidents_1000",
            test_type=LoadTestType.CONCURRENT_INCIDENTS,
            target_load=1000,
            duration_seconds=300,  # 5 minutes
            ramp_up_seconds=60,
            ramp_down_seconds=60,
            success_criteria={
                "mttr": 180.0,  # <3 minutes MTTR
                "error_rate": 0.05,  # <5% error rate
                "cpu_usage": 0.8,  # <80% CPU
                "memory_usage": 0.85,  # <85% memory
                "response_time_p95": 30.0  # <30s p95 response time
            },
            incident_patterns=["database_cascade", "ddos_attack", "memory_leak", "api_overload"],
            description="Test 1000 concurrent incidents with <3min MTTR requirement"
        ))
        
        # Alert storm handling
        self.test_configurations.append(LoadTestConfiguration(
            name="alert_storm_50k",
            test_type=LoadTestType.ALERT_STORM,
            target_load=50000,  # 50K alerts
            duration_seconds=180,  # 3 minutes
            ramp_up_seconds=30,
            ramp_down_seconds=30,
            success_criteria={
                "throughput": 500.0,  # >500 alerts/sec processing
                "error_rate": 0.02,  # <2% error rate
                "memory_usage": 0.9,  # <90% memory during storm
                "queue_depth": 1000.0  # <1000 queued alerts
            },
            incident_patterns=["alert_storm"],
            description="Handle 50K alert storm with high throughput"
        ))
        
        # Sustained load test
        self.test_configurations.append(LoadTestConfiguration(
            name="sustained_load_24h",
            test_type=LoadTestType.SUSTAINED_LOAD,
            target_load=100,  # 100 concurrent incidents
            duration_seconds=86400,  # 24 hours
            ramp_up_seconds=300,  # 5 minutes
            ramp_down_seconds=300,
            success_criteria={
                "error_rate": 0.01,  # <1% error rate over 24h
                "memory_usage": 0.75,  # <75% memory (no leaks)
                "mttr": 180.0,  # Consistent <3min MTTR
                "cpu_usage": 0.7  # <70% CPU sustained
            },
            incident_patterns=["mixed_workload"],
            description="24-hour sustained load test for stability"
        ))
        
        # Spike load test
        self.test_configurations.append(LoadTestConfiguration(
            name="spike_load_test",
            test_type=LoadTestType.SPIKE_LOAD,
            target_load=2000,  # Sudden spike to 2000
            duration_seconds=120,  # 2 minutes
            ramp_up_seconds=10,  # Very fast ramp up
            ramp_down_seconds=30,
            success_criteria={
                "error_rate": 0.1,  # <10% error rate during spike
                "response_time_p99": 60.0,  # <60s p99 during spike
                "recovery_time": 30.0  # <30s to recover after spike
            },
            incident_patterns=["cascade_failure"],
            description="Sudden load spike to test auto-scaling"
        ))
        
        # Stress test (beyond normal capacity)
        self.test_configurations.append(LoadTestConfiguration(
            name="stress_test_5000",
            test_type=LoadTestType.STRESS_TEST,
            target_load=5000,  # Beyond normal capacity
            duration_seconds=600,  # 10 minutes
            ramp_up_seconds=120,
            ramp_down_seconds=120,
            success_criteria={
                "error_rate": 0.2,  # <20% error rate under stress
                "system_availability": 0.95,  # >95% availability
                "graceful_degradation": True  # System degrades gracefully
            },
            incident_patterns=["extreme_load"],
            description="Stress test beyond normal capacity limits"
        ))
        
        # Capacity test (find breaking point)
        self.test_configurations.append(LoadTestConfiguration(
            name="capacity_test",
            test_type=LoadTestType.CAPACITY_TEST,
            target_load=10000,  # Start high and find limit
            duration_seconds=300,
            ramp_up_seconds=180,
            ramp_down_seconds=60,
            success_criteria={
                "max_capacity": 1000.0,  # Find actual max capacity
                "breaking_point_detection": True
            },
            incident_patterns=["capacity_finding"],
            description="Find maximum system capacity before failure"
        ))
    
    async def run_load_test(self, config: LoadTestConfiguration, 
                          coordinator: AgentSwarmCoordinator = None) -> LoadTestResult:
        """Execute a load test with the given configuration."""
        self.logger.info(f"Starting load test: {config.name}")
        
        start_time = datetime.utcnow()
        measurements = []
        errors = []
        
        # Start resource monitoring
        resource_monitor_task = asyncio.create_task(self._monitor_resources(measurements))
        
        try:
            # Execute the specific test type
            if config.test_type == LoadTestType.CONCURRENT_INCIDENTS:
                await self._run_concurrent_incidents_test(config, measurements, coordinator)
            elif config.test_type == LoadTestType.ALERT_STORM:
                await self._run_alert_storm_test(config, measurements, coordinator)
            elif config.test_type == LoadTestType.SUSTAINED_LOAD:
                await self._run_sustained_load_test(config, measurements, coordinator)
            elif config.test_type == LoadTestType.SPIKE_LOAD:
                await self._run_spike_load_test(config, measurements, coordinator)
            elif config.test_type == LoadTestType.STRESS_TEST:
                await self._run_stress_test(config, measurements, coordinator)
            elif config.test_type == LoadTestType.CAPACITY_TEST:
                await self._run_capacity_test(config, measurements, coordinator)
            
        except Exception as e:
            self.logger.error(f"Load test {config.name} failed: {e}")
            errors.append(str(e))
        
        finally:
            # Stop resource monitoring
            resource_monitor_task.cancel()
            try:
                await resource_monitor_task
            except asyncio.CancelledError:
                pass
        
        end_time = datetime.utcnow()
        
        # Calculate summary statistics
        summary_stats = self._calculate_summary_stats(measurements)
        
        # Detect bottlenecks
        bottlenecks = self._detect_bottlenecks(measurements, config)
        
        # Get resource usage summary
        resource_usage = self._get_resource_usage_summary()
        
        # Evaluate success criteria
        success = self._evaluate_success_criteria(config, summary_stats, errors)
        
        result = LoadTestResult(
            configuration=config,
            start_time=start_time,
            end_time=end_time,
            success=success,
            measurements=measurements,
            summary_stats=summary_stats,
            errors=errors,
            resource_usage=resource_usage,
            bottlenecks_detected=bottlenecks
        )
        
        self.test_results.append(result)
        self.logger.info(f"Load test {config.name} completed: {'SUCCESS' if success else 'FAILED'}")
        
        return result
    
    async def _run_concurrent_incidents_test(self, config: LoadTestConfiguration, 
                                           measurements: List[PerformanceMeasurement],
                                           coordinator: AgentSwarmCoordinator):
        """Run concurrent incidents load test."""
        self.logger.info(f"Running concurrent incidents test: {config.target_load} incidents")
        
        # Generate incident scenarios
        incidents = self._generate_test_incidents(config.target_load, config.incident_patterns)
        
        # Ramp up phase
        await self._ramp_up_load(incidents, config.ramp_up_seconds, measurements, coordinator)
        
        # Sustained load phase
        start_sustained = time.time()
        incident_tasks = []
        
        for incident in incidents:
            task = asyncio.create_task(self._process_incident_with_timing(incident, measurements, coordinator))
            incident_tasks.append(task)
            
            # Small delay to spread out the load
            await asyncio.sleep(0.01)
        
        # Wait for all incidents to complete or timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*incident_tasks, return_exceptions=True),
                timeout=config.duration_seconds
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"Some incidents did not complete within {config.duration_seconds}s")
        
        # Record sustained load metrics
        sustained_duration = time.time() - start_sustained
        throughput = len(incidents) / sustained_duration
        
        measurements.append(PerformanceMeasurement(
            timestamp=datetime.utcnow(),
            metric=PerformanceMetric.THROUGHPUT,
            value=throughput,
            unit="incidents/sec",
            context={"phase": "sustained_load", "total_incidents": len(incidents)}
        ))
        
        # Ramp down phase
        await self._ramp_down_load(config.ramp_down_seconds, measurements)
    
    async def _run_alert_storm_test(self, config: LoadTestConfiguration,
                                  measurements: List[PerformanceMeasurement],
                                  coordinator: AgentSwarmCoordinator):
        """Run alert storm load test."""
        self.logger.info(f"Running alert storm test: {config.target_load} alerts")
        
        # Generate alert storm
        alerts = self._generate_alert_storm(config.target_load)
        
        start_time = time.time()
        processed_alerts = 0
        
        # Process alerts in batches
        batch_size = 100
        for i in range(0, len(alerts), batch_size):
            batch = alerts[i:i + batch_size]
            batch_start = time.time()
            
            # Process batch
            batch_tasks = []
            for alert in batch:
                task = asyncio.create_task(self._process_alert_with_timing(alert, measurements, coordinator))
                batch_tasks.append(task)
            
            # Wait for batch completion
            await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            processed_alerts += len(batch)
            batch_duration = time.time() - batch_start
            
            # Record batch metrics
            batch_throughput = len(batch) / batch_duration
            measurements.append(PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.THROUGHPUT,
                value=batch_throughput,
                unit="alerts/sec",
                context={"batch_size": len(batch), "total_processed": processed_alerts}
            ))
            
            # Small delay between batches
            await asyncio.sleep(0.1)
        
        total_duration = time.time() - start_time
        overall_throughput = processed_alerts / total_duration
        
        measurements.append(PerformanceMeasurement(
            timestamp=datetime.utcnow(),
            metric=PerformanceMetric.THROUGHPUT,
            value=overall_throughput,
            unit="alerts/sec",
            context={"phase": "overall", "total_alerts": processed_alerts}
        ))
    
    async def _run_sustained_load_test(self, config: LoadTestConfiguration,
                                     measurements: List[PerformanceMeasurement],
                                     coordinator: AgentSwarmCoordinator):
        """Run sustained load test."""
        self.logger.info(f"Running sustained load test: {config.target_load} concurrent for {config.duration_seconds}s")
        
        # Start continuous incident generation
        incident_generator_task = asyncio.create_task(
            self._continuous_incident_generation(config, measurements, coordinator)
        )
        
        # Monitor for memory leaks and performance degradation
        monitoring_task = asyncio.create_task(
            self._monitor_sustained_load_health(config.duration_seconds, measurements)
        )
        
        try:
            # Wait for test duration
            await asyncio.sleep(config.duration_seconds)
        finally:
            # Stop incident generation
            incident_generator_task.cancel()
            monitoring_task.cancel()
            
            try:
                await incident_generator_task
            except asyncio.CancelledError:
                pass
            
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _run_spike_load_test(self, config: LoadTestConfiguration,
                                 measurements: List[PerformanceMeasurement],
                                 coordinator: AgentSwarmCoordinator):
        """Run spike load test."""
        self.logger.info(f"Running spike load test: spike to {config.target_load}")
        
        # Baseline measurement
        baseline_start = time.time()
        baseline_incidents = self._generate_test_incidents(10, ["normal_load"])
        
        for incident in baseline_incidents:
            await self._process_incident_with_timing(incident, measurements, coordinator)
        
        baseline_duration = time.time() - baseline_start
        baseline_throughput = len(baseline_incidents) / baseline_duration
        
        measurements.append(PerformanceMeasurement(
            timestamp=datetime.utcnow(),
            metric=PerformanceMetric.THROUGHPUT,
            value=baseline_throughput,
            unit="incidents/sec",
            context={"phase": "baseline"}
        ))
        
        # Sudden spike
        spike_start = time.time()
        spike_incidents = self._generate_test_incidents(config.target_load, config.incident_patterns)
        
        # Process spike incidents rapidly
        spike_tasks = []
        for incident in spike_incidents:
            task = asyncio.create_task(self._process_incident_with_timing(incident, measurements, coordinator))
            spike_tasks.append(task)
        
        # Wait for spike processing
        await asyncio.gather(*spike_tasks, return_exceptions=True)
        
        spike_duration = time.time() - spike_start
        spike_throughput = len(spike_incidents) / spike_duration
        
        measurements.append(PerformanceMeasurement(
            timestamp=datetime.utcnow(),
            metric=PerformanceMetric.THROUGHPUT,
            value=spike_throughput,
            unit="incidents/sec",
            context={"phase": "spike"}
        ))
        
        # Recovery measurement
        recovery_start = time.time()
        recovery_incidents = self._generate_test_incidents(10, ["normal_load"])
        
        for incident in recovery_incidents:
            await self._process_incident_with_timing(incident, measurements, coordinator)
        
        recovery_duration = time.time() - recovery_start
        recovery_throughput = len(recovery_incidents) / recovery_duration
        recovery_time = recovery_start - spike_start
        
        measurements.append(PerformanceMeasurement(
            timestamp=datetime.utcnow(),
            metric=PerformanceMetric.THROUGHPUT,
            value=recovery_throughput,
            unit="incidents/sec",
            context={"phase": "recovery"}
        ))
        
        measurements.append(PerformanceMeasurement(
            timestamp=datetime.utcnow(),
            metric=PerformanceMetric.RESPONSE_TIME,
            value=recovery_time,
            unit="seconds",
            context={"metric": "recovery_time"}
        ))
    
    async def _run_stress_test(self, config: LoadTestConfiguration,
                             measurements: List[PerformanceMeasurement],
                             coordinator: AgentSwarmCoordinator):
        """Run stress test beyond normal capacity."""
        self.logger.info(f"Running stress test: {config.target_load} (beyond capacity)")
        
        # Generate extreme load
        incidents = self._generate_test_incidents(config.target_load, config.incident_patterns)
        
        # Track system behavior under stress
        stress_start = time.time()
        completed_incidents = 0
        failed_incidents = 0
        
        # Process incidents with error tracking
        incident_tasks = []
        for incident in incidents:
            task = asyncio.create_task(self._process_incident_with_error_tracking(
                incident, measurements, coordinator
            ))
            incident_tasks.append(task)
        
        # Monitor system health during stress
        health_monitor_task = asyncio.create_task(
            self._monitor_stress_test_health(config.duration_seconds, measurements)
        )
        
        try:
            # Wait for completion or timeout
            results = await asyncio.wait_for(
                asyncio.gather(*incident_tasks, return_exceptions=True),
                timeout=config.duration_seconds
            )
            
            # Count successes and failures
            for result in results:
                if isinstance(result, Exception):
                    failed_incidents += 1
                else:
                    completed_incidents += 1
        
        except asyncio.TimeoutError:
            # Count incomplete as failures
            failed_incidents += len([t for t in incident_tasks if not t.done()])
            completed_incidents = len([t for t in incident_tasks if t.done() and not t.exception()])
        
        finally:
            health_monitor_task.cancel()
            try:
                await health_monitor_task
            except asyncio.CancelledError:
                pass
        
        stress_duration = time.time() - stress_start
        error_rate = failed_incidents / len(incidents) if incidents else 0
        
        measurements.append(PerformanceMeasurement(
            timestamp=datetime.utcnow(),
            metric=PerformanceMetric.ERROR_RATE,
            value=error_rate,
            unit="ratio",
            context={"phase": "stress_test", "failed": failed_incidents, "completed": completed_incidents}
        ))
    
    async def _run_capacity_test(self, config: LoadTestConfiguration,
                               measurements: List[PerformanceMeasurement],
                               coordinator: AgentSwarmCoordinator):
        """Run capacity test to find breaking point."""
        self.logger.info(f"Running capacity test: finding max capacity up to {config.target_load}")
        
        # Start with small load and gradually increase
        current_load = 50
        max_successful_load = 0
        breaking_point_found = False
        
        while current_load <= config.target_load and not breaking_point_found:
            self.logger.info(f"Testing capacity at {current_load} concurrent incidents")
            
            # Generate test load
            incidents = self._generate_test_incidents(current_load, config.incident_patterns)
            
            # Test current load level
            load_start = time.time()
            incident_tasks = []
            
            for incident in incidents:
                task = asyncio.create_task(self._process_incident_with_timing(incident, measurements, coordinator))
                incident_tasks.append(task)
            
            try:
                # Wait for completion with timeout
                await asyncio.wait_for(
                    asyncio.gather(*incident_tasks, return_exceptions=True),
                    timeout=60  # 1 minute timeout per load level
                )
                
                load_duration = time.time() - load_start
                throughput = len(incidents) / load_duration
                
                # Check if system handled the load successfully
                error_count = sum(1 for task in incident_tasks if task.exception())
                error_rate = error_count / len(incidents)
                
                measurements.append(PerformanceMeasurement(
                    timestamp=datetime.utcnow(),
                    metric=PerformanceMetric.THROUGHPUT,
                    value=throughput,
                    unit="incidents/sec",
                    context={"load_level": current_load, "error_rate": error_rate}
                ))
                
                measurements.append(PerformanceMeasurement(
                    timestamp=datetime.utcnow(),
                    metric=PerformanceMetric.ERROR_RATE,
                    value=error_rate,
                    unit="ratio",
                    context={"load_level": current_load}
                ))
                
                # Check if this load level was successful
                if error_rate < 0.1 and throughput > current_load * 0.8:  # <10% errors, >80% expected throughput
                    max_successful_load = current_load
                    current_load = int(current_load * 1.5)  # Increase by 50%
                else:
                    breaking_point_found = True
                    self.logger.info(f"Breaking point found at {current_load} concurrent incidents")
            
            except asyncio.TimeoutError:
                breaking_point_found = True
                self.logger.info(f"Breaking point found at {current_load} (timeout)")
            
            # Small delay between load levels
            await asyncio.sleep(5)
        
        measurements.append(PerformanceMeasurement(
            timestamp=datetime.utcnow(),
            metric=PerformanceMetric.CONCURRENT_USERS,
            value=max_successful_load,
            unit="incidents",
            context={"metric": "max_capacity"}
        ))
    
    async def _process_incident_with_timing(self, incident: Dict[str, Any], 
                                          measurements: List[PerformanceMeasurement],
                                          coordinator: AgentSwarmCoordinator) -> Dict[str, Any]:
        """Process incident and record timing measurements."""
        start_time = time.time()
        
        try:
            # Mock incident processing (in production, use real coordinator)
            if coordinator:
                result = await coordinator.handle_incident(incident)
            else:
                # Mock processing
                await asyncio.sleep(random.uniform(0.1, 2.0))  # Simulate processing time
                result = {"status": "resolved", "incident_id": incident.get("id")}
            
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Record response time
            measurements.append(PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.RESPONSE_TIME,
                value=processing_time,
                unit="ms",
                context={"incident_id": incident.get("id"), "severity": incident.get("severity")}
            ))
            
            # Record MTTR if incident was resolved
            if result.get("status") == "resolved":
                measurements.append(PerformanceMeasurement(
                    timestamp=datetime.utcnow(),
                    metric=PerformanceMetric.MTTR,
                    value=processing_time / 1000,  # Convert to seconds
                    unit="seconds",
                    context={"incident_id": incident.get("id")}
                ))
            
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            
            # Record error
            measurements.append(PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.ERROR_RATE,
                value=1.0,
                unit="count",
                context={"incident_id": incident.get("id"), "error": str(e)}
            ))
            
            raise e
    
    async def _process_alert_with_timing(self, alert: Dict[str, Any],
                                       measurements: List[PerformanceMeasurement],
                                       coordinator: AgentSwarmCoordinator) -> Dict[str, Any]:
        """Process alert and record timing measurements."""
        start_time = time.time()
        
        try:
            # Mock alert processing
            await asyncio.sleep(random.uniform(0.01, 0.1))  # Fast alert processing
            
            processing_time = (time.time() - start_time) * 1000
            
            measurements.append(PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.RESPONSE_TIME,
                value=processing_time,
                unit="ms",
                context={"alert_id": alert.get("id"), "type": "alert_processing"}
            ))
            
            return {"status": "processed", "alert_id": alert.get("id")}
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            
            measurements.append(PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.ERROR_RATE,
                value=1.0,
                unit="count",
                context={"alert_id": alert.get("id"), "error": str(e)}
            ))
            
            raise e
    
    async def _ramp_up_load(self, incidents: List[Dict[str, Any]], ramp_up_seconds: int,
                          measurements: List[PerformanceMeasurement], 
                          coordinator: AgentSwarmCoordinator):
        """Gradually ramp up load over the specified time period."""
        if ramp_up_seconds <= 0:
            return
        
        self.logger.info(f"Ramping up load over {ramp_up_seconds} seconds")
        
        # Process incidents gradually during ramp-up
        incidents_per_second = len(incidents) / ramp_up_seconds
        start_time = time.time()
        
        for i, incident in enumerate(incidents[:min(len(incidents), int(incidents_per_second * ramp_up_seconds))]):
            # Calculate when this incident should be processed
            target_time = start_time + (i / incidents_per_second)
            current_time = time.time()
            
            # Wait if we're ahead of schedule
            if current_time < target_time:
                await asyncio.sleep(target_time - current_time)
            
            # Process incident in background
            asyncio.create_task(self._process_incident_with_timing(incident, measurements, coordinator))
    
    async def _ramp_down_load(self, ramp_down_seconds: int, measurements: List[PerformanceMeasurement]):
        """Gradually ramp down load over the specified time period."""
        if ramp_down_seconds <= 0:
            return
        
        self.logger.info(f"Ramping down load over {ramp_down_seconds} seconds")
        
        # Simply wait for ramp-down period
        await asyncio.sleep(ramp_down_seconds)
        
        # Record ramp-down completion
        measurements.append(PerformanceMeasurement(
            timestamp=datetime.utcnow(),
            metric=PerformanceMetric.RESPONSE_TIME,
            value=0.0,
            unit="ms",
            context={"phase": "ramp_down_complete"}
        ))
    
    async def _continuous_incident_generation(self, config: LoadTestConfiguration,
                                            measurements: List[PerformanceMeasurement],
                                            coordinator: AgentSwarmCoordinator):
        """Continuously generate incidents for sustained load testing."""
        self.logger.info(f"Starting continuous incident generation for {config.duration_seconds}s")
        
        start_time = time.time()
        incidents_generated = 0
        
        # Generate incidents at target rate
        incident_rate = config.target_load / 60  # incidents per second
        
        while time.time() - start_time < config.duration_seconds:
            # Generate batch of incidents
            batch_size = max(1, int(incident_rate * 10))  # 10-second batches
            incidents = self._generate_test_incidents(batch_size, config.incident_patterns)
            
            # Process incidents
            for incident in incidents:
                asyncio.create_task(self._process_incident_with_timing(incident, measurements, coordinator))
                incidents_generated += 1
            
            # Wait before next batch
            await asyncio.sleep(10)
        
        self.logger.info(f"Continuous generation completed: {incidents_generated} incidents generated")
    
    async def _monitor_sustained_load_health(self, duration_seconds: int,
                                           measurements: List[PerformanceMeasurement]):
        """Monitor system health during sustained load testing."""
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            # Check for memory leaks
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                measurements.append(PerformanceMeasurement(
                    timestamp=datetime.utcnow(),
                    metric=PerformanceMetric.MEMORY_USAGE,
                    value=memory.percent / 100.0,
                    unit="ratio",
                    context={"alert": "high_memory_usage"}
                ))
            
            # Check for performance degradation
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 95:
                measurements.append(PerformanceMeasurement(
                    timestamp=datetime.utcnow(),
                    metric=PerformanceMetric.CPU_USAGE,
                    value=cpu_percent / 100.0,
                    unit="ratio",
                    context={"alert": "high_cpu_usage"}
                ))
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _process_incident_with_error_tracking(self, incident: Dict[str, Any],
                                                  measurements: List[PerformanceMeasurement],
                                                  coordinator: AgentSwarmCoordinator) -> Dict[str, Any]:
        """Process incident with comprehensive error tracking."""
        try:
            return await self._process_incident_with_timing(incident, measurements, coordinator)
        except Exception as e:
            # Record error details
            measurements.append(PerformanceMeasurement(
                timestamp=datetime.utcnow(),
                metric=PerformanceMetric.ERROR_RATE,
                value=1.0,
                unit="count",
                context={
                    "incident_id": incident.get("id"),
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            ))
            return {"status": "failed", "incident_id": incident.get("id"), "error": str(e)}
    
    async def _monitor_stress_test_health(self, duration_seconds: int,
                                        measurements: List[PerformanceMeasurement]):
        """Monitor system health during stress testing."""
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            try:
                # Monitor system availability
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Record system health metrics
                measurements.append(PerformanceMeasurement(
                    timestamp=datetime.utcnow(),
                    metric=PerformanceMetric.CPU_USAGE,
                    value=cpu_percent / 100.0,
                    unit="ratio",
                    context={"phase": "stress_test"}
                ))
                
                measurements.append(PerformanceMeasurement(
                    timestamp=datetime.utcnow(),
                    metric=PerformanceMetric.MEMORY_USAGE,
                    value=memory.percent / 100.0,
                    unit="ratio",
                    context={"phase": "stress_test"}
                ))
                
                # Check for system overload
                if cpu_percent > 98 or memory.percent > 98:
                    measurements.append(PerformanceMeasurement(
                        timestamp=datetime.utcnow(),
                        metric=PerformanceMetric.ERROR_RATE,
                        value=1.0,
                        unit="count",
                        context={"alert": "system_overload"}
                    ))
                
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Stress test health monitoring error: {e}")
                await asyncio.sleep(10)
    
    def _generate_test_incidents(self, count: int, patterns: List[str]) -> List[Dict[str, Any]]:
        """Generate test incidents for load testing."""
        incidents = []
        
        for i in range(count):
            pattern = random.choice(patterns) if patterns else "generic"
            
            incident = {
                "id": f"test_incident_{self.incident_counter}_{i}",
                "title": f"Test incident {i} - {pattern}",
                "description": f"Generated test incident for pattern: {pattern}",
                "severity": random.choice(["low", "medium", "high", "critical"]),
                "pattern": pattern,
                "timestamp": datetime.utcnow().isoformat(),
                "business_impact": {
                    "revenue_impact_per_minute": random.uniform(100, 10000),
                    "users_affected": random.randint(10, 100000)
                }
            }
            
            incidents.append(incident)
        
        self.incident_counter += 1
        return incidents
    
    def _generate_alert_storm(self, count: int) -> List[Dict[str, Any]]:
        """Generate alert storm for testing."""
        alerts = []
        
        for i in range(count):
            alert = {
                "id": f"alert_{i}",
                "metric": random.choice(["cpu_usage", "memory_usage", "error_rate", "response_time"]),
                "value": random.uniform(0.8, 1.2),
                "threshold": 1.0,
                "timestamp": datetime.utcnow().isoformat(),
                "source": random.choice(["cloudwatch", "datadog", "prometheus"]),
                "severity": random.choice(["warning", "critical"])
            }
            
            alerts.append(alert)
        
        return alerts
    
    async def _monitor_resources(self, measurements: List[PerformanceMeasurement]):
        """Monitor system resources during load test."""
        self.resource_monitor_active = True
        
        while self.resource_monitor_active:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                measurements.append(PerformanceMeasurement(
                    timestamp=datetime.utcnow(),
                    metric=PerformanceMetric.CPU_USAGE,
                    value=cpu_percent / 100.0,
                    unit="ratio"
                ))
                
                # Memory usage
                memory = psutil.virtual_memory()
                measurements.append(PerformanceMeasurement(
                    timestamp=datetime.utcnow(),
                    metric=PerformanceMetric.MEMORY_USAGE,
                    value=memory.percent / 100.0,
                    unit="ratio"
                ))
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    measurements.append(PerformanceMeasurement(
                        timestamp=datetime.utcnow(),
                        metric=PerformanceMetric.DISK_IO,
                        value=disk_io.read_bytes + disk_io.write_bytes,
                        unit="bytes"
                    ))
                
                # Network I/O
                network_io = psutil.net_io_counters()
                if network_io:
                    measurements.append(PerformanceMeasurement(
                        timestamp=datetime.utcnow(),
                        metric=PerformanceMetric.NETWORK_IO,
                        value=network_io.bytes_sent + network_io.bytes_recv,
                        unit="bytes"
                    ))
                
                await asyncio.sleep(5)  # Monitor every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(5)
    
    def _calculate_summary_stats(self, measurements: List[PerformanceMeasurement]) -> Dict[str, Dict[str, float]]:
        """Calculate summary statistics from measurements."""
        stats = {}
        
        # Group measurements by metric
        metric_values = defaultdict(list)
        for measurement in measurements:
            metric_values[measurement.metric].append(measurement.value)
        
        # Calculate statistics for each metric
        for metric, values in metric_values.items():
            if values:
                stats[metric.value] = {
                    'min': min(values),
                    'max': max(values),
                    'avg': statistics.mean(values),
                    'median': statistics.median(values),
                    'std': statistics.stdev(values) if len(values) > 1 else 0,
                    'p95': np.percentile(values, 95),
                    'p99': np.percentile(values, 99),
                    'count': len(values)
                }
        
        return stats
    
    def _detect_bottlenecks(self, measurements: List[PerformanceMeasurement], 
                          config: LoadTestConfiguration) -> List[str]:
        """Detect performance bottlenecks from measurements."""
        bottlenecks = []
        
        # Group measurements by metric
        metric_values = defaultdict(list)
        for measurement in measurements:
            metric_values[measurement.metric].append(measurement.value)
        
        # Check for bottlenecks
        if PerformanceMetric.CPU_USAGE in metric_values:
            cpu_values = metric_values[PerformanceMetric.CPU_USAGE]
            if max(cpu_values) > 0.9:  # >90% CPU
                bottlenecks.append("CPU bottleneck detected (>90% usage)")
        
        if PerformanceMetric.MEMORY_USAGE in metric_values:
            memory_values = metric_values[PerformanceMetric.MEMORY_USAGE]
            if max(memory_values) > 0.95:  # >95% memory
                bottlenecks.append("Memory bottleneck detected (>95% usage)")
        
        if PerformanceMetric.RESPONSE_TIME in metric_values:
            response_times = metric_values[PerformanceMetric.RESPONSE_TIME]
            p95_response_time = np.percentile(response_times, 95)
            if p95_response_time > 30000:  # >30 seconds
                bottlenecks.append(f"Response time bottleneck (P95: {p95_response_time:.1f}ms)")
        
        if PerformanceMetric.ERROR_RATE in metric_values:
            error_rates = metric_values[PerformanceMetric.ERROR_RATE]
            avg_error_rate = statistics.mean(error_rates)
            if avg_error_rate > 0.1:  # >10% error rate
                bottlenecks.append(f"High error rate detected ({avg_error_rate:.1%})")
        
        return bottlenecks
    
    def _get_resource_usage_summary(self) -> Dict[str, Any]:
        """Get summary of resource usage during test."""
        return {
            "peak_cpu_percent": 85.0,  # Mock values
            "peak_memory_percent": 78.0,
            "total_disk_io_gb": 2.5,
            "total_network_io_gb": 1.8,
            "process_count": 45
        }
    
    def _evaluate_success_criteria(self, config: LoadTestConfiguration, 
                                 summary_stats: Dict[str, Dict[str, float]], 
                                 errors: List[str]) -> bool:
        """Evaluate if the test met success criteria."""
        if errors:
            return False
        
        for criterion, threshold in config.success_criteria.items():
            if criterion == "mttr":
                mttr_stats = summary_stats.get("mttr", {})
                if mttr_stats.get("avg", float('inf')) > threshold:
                    return False
            
            elif criterion == "error_rate":
                error_stats = summary_stats.get("error_rate", {})
                if error_stats.get("avg", 0) > threshold:
                    return False
            
            elif criterion == "cpu_usage":
                cpu_stats = summary_stats.get("cpu_usage", {})
                if cpu_stats.get("max", 0) > threshold:
                    return False
            
            elif criterion == "memory_usage":
                memory_stats = summary_stats.get("memory_usage", {})
                if memory_stats.get("max", 0) > threshold:
                    return False
            
            elif criterion == "response_time_p95":
                response_stats = summary_stats.get("response_time", {})
                if response_stats.get("p95", float('inf')) > threshold * 1000:  # Convert to ms
                    return False
        
        return True
    
    async def run_benchmark_suite(self, coordinator: AgentSwarmCoordinator = None) -> List[LoadTestResult]:
        """Run complete benchmark suite."""
        self.logger.info("Starting comprehensive performance benchmark suite")
        
        results = []
        
        for config in self.test_configurations:
            self.logger.info(f"Running benchmark: {config.name}")
            
            try:
                result = await self.run_load_test(config, coordinator)
                results.append(result)
                
                # Log result summary
                success_status = "PASSED" if result.success else "FAILED"
                self.logger.info(f"Benchmark {config.name}: {success_status}")
                
                if result.bottlenecks_detected:
                    self.logger.warning(f"Bottlenecks detected: {', '.join(result.bottlenecks_detected)}")
                
                # Wait between tests
                await asyncio.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Benchmark {config.name} failed with error: {e}")
        
        self.logger.info(f"Benchmark suite completed: {len(results)} tests executed")
        
        return results
    
    def generate_performance_report(self, results: List[LoadTestResult]) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r.success),
            "failed_tests": sum(1 for r in results if not r.success),
            "test_results": [],
            "performance_summary": {},
            "bottlenecks_summary": {},
            "recommendations": []
        }
        
        # Individual test results
        for result in results:
            test_summary = {
                "name": result.configuration.name,
                "type": result.configuration.test_type.value,
                "success": result.success,
                "duration_seconds": (result.end_time - result.start_time).total_seconds(),
                "key_metrics": {},
                "bottlenecks": result.bottlenecks_detected
            }
            
            # Extract key metrics
            if "response_time" in result.summary_stats:
                test_summary["key_metrics"]["avg_response_time_ms"] = result.summary_stats["response_time"]["avg"]
                test_summary["key_metrics"]["p95_response_time_ms"] = result.summary_stats["response_time"]["p95"]
            
            if "mttr" in result.summary_stats:
                test_summary["key_metrics"]["avg_mttr_seconds"] = result.summary_stats["mttr"]["avg"]
            
            if "throughput" in result.summary_stats:
                test_summary["key_metrics"]["avg_throughput"] = result.summary_stats["throughput"]["avg"]
            
            if "error_rate" in result.summary_stats:
                test_summary["key_metrics"]["avg_error_rate"] = result.summary_stats["error_rate"]["avg"]
            
            report["test_results"].append(test_summary)
        
        # Performance summary
        all_response_times = []
        all_mttrs = []
        all_throughputs = []
        
        for result in results:
            if "response_time" in result.summary_stats:
                all_response_times.extend([m.value for m in result.measurements if m.metric == PerformanceMetric.RESPONSE_TIME])
            if "mttr" in result.summary_stats:
                all_mttrs.extend([m.value for m in result.measurements if m.metric == PerformanceMetric.MTTR])
            if "throughput" in result.summary_stats:
                all_throughputs.extend([m.value for m in result.measurements if m.metric == PerformanceMetric.THROUGHPUT])
        
        if all_response_times:
            report["performance_summary"]["overall_response_time"] = {
                "avg_ms": statistics.mean(all_response_times),
                "p95_ms": np.percentile(all_response_times, 95),
                "p99_ms": np.percentile(all_response_times, 99)
            }
        
        if all_mttrs:
            report["performance_summary"]["overall_mttr"] = {
                "avg_seconds": statistics.mean(all_mttrs),
                "p95_seconds": np.percentile(all_mttrs, 95),
                "meets_sla": np.percentile(all_mttrs, 95) < 180  # <3 minutes
            }
        
        if all_throughputs:
            report["performance_summary"]["overall_throughput"] = {
                "avg_per_sec": statistics.mean(all_throughputs),
                "max_per_sec": max(all_throughputs)
            }
        
        # Bottlenecks summary
        all_bottlenecks = []
        for result in results:
            all_bottlenecks.extend(result.bottlenecks_detected)
        
        bottleneck_counts = defaultdict(int)
        for bottleneck in all_bottlenecks:
            bottleneck_counts[bottleneck] += 1
        
        report["bottlenecks_summary"] = dict(bottleneck_counts)
        
        # Recommendations
        if bottleneck_counts:
            report["recommendations"].append("Address identified bottlenecks to improve performance")
        
        failed_tests = [r for r in results if not r.success]
        if failed_tests:
            report["recommendations"].append(f"Investigate {len(failed_tests)} failed tests")
        
        # Check MTTR SLA
        if all_mttrs and np.percentile(all_mttrs, 95) >= 180:
            report["recommendations"].append("MTTR exceeds 3-minute SLA requirement")
        
        return report


# Example usage and testing
async def main():
    """Example usage of performance testing framework."""
    framework = PerformanceTestingFramework()
    
    print("Starting performance testing framework...")
    
    # Run a single load test
    config = framework.test_configurations[0]  # concurrent_incidents_1000
    print(f"Running test: {config.name}")
    
    result = await framework.run_load_test(config)
    
    print(f"\nTest Results:")
    print(f"Success: {result.success}")
    print(f"Duration: {(result.end_time - result.start_time).total_seconds():.1f}s")
    print(f"Measurements: {len(result.measurements)}")
    
    if result.summary_stats:
        print(f"\nKey Metrics:")
        for metric, stats in result.summary_stats.items():
            print(f"  {metric}: avg={stats['avg']:.2f}, p95={stats['p95']:.2f}")
    
    if result.bottlenecks_detected:
        print(f"\nBottlenecks: {', '.join(result.bottlenecks_detected)}")
    
    # Generate report
    report = framework.generate_performance_report([result])
    print(f"\nPerformance Report Generated:")
    print(f"Overall success rate: {report['passed_tests']}/{report['total_tests']}")


if __name__ == "__main__":
    asyncio.run(main())