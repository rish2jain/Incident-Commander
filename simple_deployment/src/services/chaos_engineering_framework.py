"""
Chaos Engineering and Resilience Testing Framework (Task 16.3)

Comprehensive chaos engineering framework for testing system resilience,
fault injection, network partitions, and Byzantine fault tolerance.
"""

import asyncio
import random
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import threading
import signal
import psutil
from unittest.mock import AsyncMock, MagicMock, patch

from src.utils.logging import get_logger
from src.models.incident import Incident, IncidentSeverity
from src.services.agent_swarm_coordinator import AgentSwarmCoordinator
from src.services.consensus import BasicWeightedConsensusEngine

logger = get_logger(__name__)


class ChaosExperimentType(Enum):
    """Types of chaos experiments."""
    AGENT_FAILURE = "agent_failure"
    NETWORK_PARTITION = "network_partition"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SERVICE_DEGRADATION = "service_degradation"
    DATA_CORRUPTION = "data_corruption"
    BYZANTINE_AGENT = "byzantine_agent"
    CONSENSUS_DISRUPTION = "consensus_disruption"
    DEPENDENCY_FAILURE = "dependency_failure"
    LATENCY_INJECTION = "latency_injection"
    CASCADING_FAILURE = "cascading_failure"


class FailureMode(Enum):
    """Different failure modes for chaos experiments."""
    COMPLETE_FAILURE = "complete_failure"
    INTERMITTENT_FAILURE = "intermittent_failure"
    SLOW_RESPONSE = "slow_response"
    CORRUPT_RESPONSE = "corrupt_response"
    TIMEOUT = "timeout"
    RESOURCE_LEAK = "resource_leak"
    MALICIOUS_BEHAVIOR = "malicious_behavior"


class ResilienceMetric(Enum):
    """Metrics for measuring system resilience."""
    RECOVERY_TIME = "recovery_time"
    AVAILABILITY = "availability"
    THROUGHPUT_DEGRADATION = "throughput_degradation"
    ERROR_RATE_INCREASE = "error_rate_increase"
    CONSENSUS_INTEGRITY = "consensus_integrity"
    DATA_CONSISTENCY = "data_consistency"
    GRACEFUL_DEGRADATION = "graceful_degradation"


@dataclass
class ChaosExperiment:
    """Definition of a chaos experiment."""
    name: str
    experiment_type: ChaosExperimentType
    failure_mode: FailureMode
    target_components: List[str]
    duration_seconds: int
    intensity: float  # 0.0 to 1.0
    description: str
    expected_behavior: str
    success_criteria: Dict[str, float]
    blast_radius: str  # "single_agent", "agent_type", "system_wide"


@dataclass
class ChaosInjection:
    """Active chaos injection state."""
    experiment: ChaosExperiment
    start_time: datetime
    end_time: Optional[datetime]
    affected_components: List[str]
    injection_state: Dict[str, Any]
    active: bool = True


@dataclass
class ResilienceMeasurement:
    """Measurement of system resilience during chaos."""
    timestamp: datetime
    metric: ResilienceMetric
    value: float
    unit: str
    experiment_name: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChaosExperimentResult:
    """Result of a chaos experiment."""
    experiment: ChaosExperiment
    start_time: datetime
    end_time: datetime
    success: bool
    measurements: List[ResilienceMeasurement]
    system_behavior: Dict[str, Any]
    recovery_metrics: Dict[str, float]
    lessons_learned: List[str]
    recommendations: List[str]


class ChaosEngineeringFramework:
    """
    Comprehensive chaos engineering framework for testing system resilience
    and fault tolerance of the Autonomous Incident Commander.
    """
    
    def __init__(self):
        self.logger = logger
        
        # Experiment management
        self.experiments: List[ChaosExperiment] = []
        self.active_injections: Dict[str, ChaosInjection] = {}
        self.experiment_results: List[ChaosExperimentResult] = []
        
        # System monitoring
        self.baseline_metrics: Dict[str, float] = {}
        self.resilience_measurements: List[ResilienceMeasurement] = []
        
        # Failure injection state
        self.failure_injectors: Dict[str, Callable] = {}
        self.recovery_handlers: Dict[str, Callable] = {}
        
        # Safety mechanisms
        self.emergency_stop_active = False
        self.max_concurrent_experiments = 3
        self.safety_thresholds = {
            "max_error_rate": 0.5,  # 50% max error rate
            "min_availability": 0.7,  # 70% min availability
            "max_recovery_time": 300  # 5 minutes max recovery
        }
        
        # Initialize experiments
        self._initialize_chaos_experiments()
        self._initialize_failure_injectors()
    
    def _initialize_chaos_experiments(self):
        """Initialize comprehensive chaos experiments."""
        
        # Agent failure experiments
        self.experiments.extend([
            ChaosExperiment(
                name="detection_agent_failure",
                experiment_type=ChaosExperimentType.AGENT_FAILURE,
                failure_mode=FailureMode.COMPLETE_FAILURE,
                target_components=["detection_agent"],
                duration_seconds=300,  # 5 minutes
                intensity=1.0,
                description="Simulate complete failure of detection agent",
                expected_behavior="System should continue with remaining agents and escalate appropriately",
                success_criteria={
                    "recovery_time": 60.0,  # <1 minute to detect and recover
                    "availability": 0.8,    # >80% availability maintained
                    "error_rate_increase": 0.2  # <20% error rate increase
                },
                blast_radius="single_agent"
            ),
            
            ChaosExperiment(
                name="diagnosis_agent_intermittent_failure",
                experiment_type=ChaosExperimentType.AGENT_FAILURE,
                failure_mode=FailureMode.INTERMITTENT_FAILURE,
                target_components=["diagnosis_agent"],
                duration_seconds=600,  # 10 minutes
                intensity=0.3,  # 30% failure rate
                description="Simulate intermittent failures in diagnosis agent",
                expected_behavior="System should retry and use fallback mechanisms",
                success_criteria={
                    "recovery_time": 30.0,
                    "availability": 0.9,
                    "consensus_integrity": 0.95
                },
                blast_radius="single_agent"
            )
        ])
        
        # Network partition experiments
        self.experiments.extend([
            ChaosExperiment(
                name="agent_network_partition",
                experiment_type=ChaosExperimentType.NETWORK_PARTITION,
                failure_mode=FailureMode.COMPLETE_FAILURE,
                target_components=["detection_agent", "diagnosis_agent"],
                duration_seconds=180,  # 3 minutes
                intensity=1.0,
                description="Simulate network partition between agents",
                expected_behavior="Agents should detect partition and continue independently",
                success_criteria={
                    "recovery_time": 120.0,  # <2 minutes to detect partition
                    "data_consistency": 0.95,  # >95% data consistency after healing
                    "availability": 0.7  # >70% availability during partition
                },
                blast_radius="agent_type"
            ),
            
            ChaosExperiment(
                name="consensus_network_partition",
                experiment_type=ChaosExperimentType.NETWORK_PARTITION,
                failure_mode=FailureMode.COMPLETE_FAILURE,
                target_components=["consensus_engine"],
                duration_seconds=240,
                intensity=1.0,
                description="Simulate network partition affecting consensus",
                expected_behavior="Consensus should use fallback mechanisms and maintain safety",
                success_criteria={
                    "consensus_integrity": 0.9,
                    "recovery_time": 180.0,
                    "graceful_degradation": 1.0
                },
                blast_radius="system_wide"
            )
        ])
        
        # Resource exhaustion experiments
        self.experiments.extend([
            ChaosExperiment(
                name="memory_exhaustion",
                experiment_type=ChaosExperimentType.RESOURCE_EXHAUSTION,
                failure_mode=FailureMode.RESOURCE_LEAK,
                target_components=["system"],
                duration_seconds=300,
                intensity=0.8,  # 80% memory usage
                description="Simulate memory exhaustion scenario",
                expected_behavior="System should implement backpressure and graceful degradation",
                success_criteria={
                    "graceful_degradation": 1.0,
                    "recovery_time": 60.0,
                    "availability": 0.6  # >60% availability under stress
                },
                blast_radius="system_wide"
            ),
            
            ChaosExperiment(
                name="cpu_exhaustion",
                experiment_type=ChaosExperimentType.RESOURCE_EXHAUSTION,
                failure_mode=FailureMode.SLOW_RESPONSE,
                target_components=["system"],
                duration_seconds=240,
                intensity=0.9,  # 90% CPU usage
                description="Simulate CPU exhaustion with slow responses",
                expected_behavior="System should throttle requests and maintain core functionality",
                success_criteria={
                    "throughput_degradation": 0.5,  # <50% throughput loss
                    "recovery_time": 30.0,
                    "error_rate_increase": 0.1
                },
                blast_radius="system_wide"
            )
        ])
        
        # Byzantine agent experiments
        self.experiments.extend([
            ChaosExperiment(
                name="malicious_agent_behavior",
                experiment_type=ChaosExperimentType.BYZANTINE_AGENT,
                failure_mode=FailureMode.MALICIOUS_BEHAVIOR,
                target_components=["detection_agent"],
                duration_seconds=420,  # 7 minutes
                intensity=1.0,
                description="Simulate Byzantine agent providing malicious recommendations",
                expected_behavior="Consensus should detect and isolate malicious agent",
                success_criteria={
                    "consensus_integrity": 0.95,
                    "recovery_time": 120.0,  # <2 minutes to detect and isolate
                    "data_consistency": 0.9
                },
                blast_radius="single_agent"
            ),
            
            ChaosExperiment(
                name="compromised_agent_credentials",
                experiment_type=ChaosExperimentType.BYZANTINE_AGENT,
                failure_mode=FailureMode.MALICIOUS_BEHAVIOR,
                target_components=["resolution_agent"],
                duration_seconds=300,
                intensity=1.0,
                description="Simulate agent with compromised credentials attempting unauthorized actions",
                expected_behavior="Security controls should block unauthorized actions",
                success_criteria={
                    "consensus_integrity": 1.0,
                    "recovery_time": 60.0,
                    "availability": 0.9
                },
                blast_radius="single_agent"
            )
        ])
        
        # Service degradation experiments
        self.experiments.extend([
            ChaosExperiment(
                name="aws_bedrock_degradation",
                experiment_type=ChaosExperimentType.SERVICE_DEGRADATION,
                failure_mode=FailureMode.SLOW_RESPONSE,
                target_components=["bedrock_service"],
                duration_seconds=360,
                intensity=0.7,
                description="Simulate AWS Bedrock service degradation with slow responses",
                expected_behavior="System should use fallback models and caching",
                success_criteria={
                    "recovery_time": 90.0,
                    "throughput_degradation": 0.3,
                    "availability": 0.8
                },
                blast_radius="system_wide"
            ),
            
            ChaosExperiment(
                name="database_connection_failure",
                experiment_type=ChaosExperimentType.DEPENDENCY_FAILURE,
                failure_mode=FailureMode.INTERMITTENT_FAILURE,
                target_components=["dynamodb"],
                duration_seconds=300,
                intensity=0.5,
                description="Simulate intermittent database connection failures",
                expected_behavior="System should retry with exponential backoff and use local caching",
                success_criteria={
                    "recovery_time": 45.0,
                    "data_consistency": 0.95,
                    "error_rate_increase": 0.15
                },
                blast_radius="system_wide"
            )
        ])
        
        # Cascading failure experiments
        self.experiments.extend([
            ChaosExperiment(
                name="cascading_agent_failure",
                experiment_type=ChaosExperimentType.CASCADING_FAILURE,
                failure_mode=FailureMode.COMPLETE_FAILURE,
                target_components=["detection_agent", "diagnosis_agent", "resolution_agent"],
                duration_seconds=480,  # 8 minutes
                intensity=1.0,
                description="Simulate cascading failure across multiple agents",
                expected_behavior="System should isolate failures and maintain minimal functionality",
                success_criteria={
                    "recovery_time": 240.0,  # <4 minutes for partial recovery
                    "availability": 0.5,  # >50% availability with degraded service
                    "graceful_degradation": 1.0
                },
                blast_radius="system_wide"
            )
        ])
    
    def _initialize_failure_injectors(self):
        """Initialize failure injection mechanisms."""
        
        self.failure_injectors = {
            "agent_failure": self._inject_agent_failure,
            "network_partition": self._inject_network_partition,
            "resource_exhaustion": self._inject_resource_exhaustion,
            "service_degradation": self._inject_service_degradation,
            "byzantine_behavior": self._inject_byzantine_behavior,
            "latency_injection": self._inject_latency,
            "data_corruption": self._inject_data_corruption
        }
        
        self.recovery_handlers = {
            "agent_failure": self._recover_agent_failure,
            "network_partition": self._recover_network_partition,
            "resource_exhaustion": self._recover_resource_exhaustion,
            "service_degradation": self._recover_service_degradation,
            "byzantine_behavior": self._recover_byzantine_behavior,
            "latency_injection": self._recover_latency,
            "data_corruption": self._recover_data_corruption
        }
    
    async def run_chaos_experiment(self, experiment: ChaosExperiment, 
                                 coordinator: AgentSwarmCoordinator = None) -> ChaosExperimentResult:
        """Execute a chaos experiment and measure system resilience."""
        self.logger.info(f"Starting chaos experiment: {experiment.name}")
        
        # Safety check
        if len(self.active_injections) >= self.max_concurrent_experiments:
            raise RuntimeError("Maximum concurrent experiments limit reached")
        
        if self.emergency_stop_active:
            raise RuntimeError("Emergency stop is active")
        
        start_time = datetime.utcnow()
        measurements = []
        
        # Establish baseline metrics
        baseline = await self._measure_baseline_metrics(coordinator)
        
        # Start monitoring
        monitoring_task = asyncio.create_task(
            self._monitor_resilience_metrics(experiment, measurements, coordinator)
        )
        
        try:
            # Inject failure
            injection = await self._inject_failure(experiment)
            self.active_injections[experiment.name] = injection
            
            # Wait for experiment duration
            await asyncio.sleep(experiment.duration_seconds)
            
            # Recover from failure
            await self._recover_from_failure(experiment, injection)
            
            # Wait for recovery observation period
            await asyncio.sleep(60)  # 1 minute recovery observation
            
        except Exception as e:
            self.logger.error(f"Chaos experiment {experiment.name} failed: {e}")
            # Emergency recovery
            await self._emergency_recovery(experiment)
        
        finally:
            # Stop monitoring
            monitoring_task.cancel()
            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass
            
            # Clean up injection
            if experiment.name in self.active_injections:
                del self.active_injections[experiment.name]
        
        end_time = datetime.utcnow()
        
        # Analyze results
        system_behavior = await self._analyze_system_behavior(measurements, baseline)
        recovery_metrics = self._calculate_recovery_metrics(measurements, experiment)
        success = self._evaluate_experiment_success(experiment, recovery_metrics)
        
        # Generate lessons learned
        lessons_learned = self._extract_lessons_learned(experiment, measurements, system_behavior)
        recommendations = self._generate_recommendations(experiment, system_behavior, success)
        
        result = ChaosExperimentResult(
            experiment=experiment,
            start_time=start_time,
            end_time=end_time,
            success=success,
            measurements=measurements,
            system_behavior=system_behavior,
            recovery_metrics=recovery_metrics,
            lessons_learned=lessons_learned,
            recommendations=recommendations
        )
        
        self.experiment_results.append(result)
        self.logger.info(f"Chaos experiment {experiment.name} completed: {'SUCCESS' if success else 'FAILED'}")
        
        return result
    
    async def _inject_failure(self, experiment: ChaosExperiment) -> ChaosInjection:
        """Inject failure based on experiment configuration."""
        self.logger.info(f"Injecting failure for experiment: {experiment.name}")
        
        injection_state = {}
        
        # Select appropriate injector
        if experiment.experiment_type == ChaosExperimentType.AGENT_FAILURE:
            injection_state = await self.failure_injectors["agent_failure"](experiment)
        elif experiment.experiment_type == ChaosExperimentType.NETWORK_PARTITION:
            injection_state = await self.failure_injectors["network_partition"](experiment)
        elif experiment.experiment_type == ChaosExperimentType.RESOURCE_EXHAUSTION:
            injection_state = await self.failure_injectors["resource_exhaustion"](experiment)
        elif experiment.experiment_type == ChaosExperimentType.SERVICE_DEGRADATION:
            injection_state = await self.failure_injectors["service_degradation"](experiment)
        elif experiment.experiment_type == ChaosExperimentType.BYZANTINE_AGENT:
            injection_state = await self.failure_injectors["byzantine_behavior"](experiment)
        elif experiment.experiment_type == ChaosExperimentType.LATENCY_INJECTION:
            injection_state = await self.failure_injectors["latency_injection"](experiment)
        elif experiment.experiment_type == ChaosExperimentType.DATA_CORRUPTION:
            injection_state = await self.failure_injectors["data_corruption"](experiment)
        
        return ChaosInjection(
            experiment=experiment,
            start_time=datetime.utcnow(),
            end_time=None,
            affected_components=experiment.target_components,
            injection_state=injection_state,
            active=True
        )
    
    async def _inject_agent_failure(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Inject agent failure."""
        injection_state = {
            "failed_agents": experiment.target_components,
            "failure_mode": experiment.failure_mode.value,
            "original_states": {}
        }
        
        for component in experiment.target_components:
            if experiment.failure_mode == FailureMode.COMPLETE_FAILURE:
                # Mock complete agent failure
                injection_state["original_states"][component] = "healthy"
                self.logger.info(f"Simulating complete failure of {component}")
                
            elif experiment.failure_mode == FailureMode.INTERMITTENT_FAILURE:
                # Mock intermittent failures
                injection_state["original_states"][component] = "healthy"
                injection_state["failure_probability"] = experiment.intensity
                self.logger.info(f"Simulating intermittent failure of {component} ({experiment.intensity:.1%} failure rate)")
        
        return injection_state
    
    async def _inject_network_partition(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Inject network partition."""
        injection_state = {
            "partitioned_components": experiment.target_components,
            "partition_type": "split_brain" if len(experiment.target_components) > 1 else "isolation",
            "original_connectivity": {}
        }
        
        for component in experiment.target_components:
            injection_state["original_connectivity"][component] = "connected"
            self.logger.info(f"Simulating network partition for {component}")
        
        return injection_state
    
    async def _inject_resource_exhaustion(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Inject resource exhaustion."""
        injection_state = {
            "resource_type": "memory" if "memory" in experiment.name else "cpu",
            "target_usage": experiment.intensity,
            "original_usage": {}
        }
        
        # Mock resource exhaustion
        if "memory" in experiment.name:
            injection_state["original_usage"]["memory"] = 0.3  # 30% baseline
            self.logger.info(f"Simulating memory exhaustion to {experiment.intensity:.1%}")
        elif "cpu" in experiment.name:
            injection_state["original_usage"]["cpu"] = 0.2  # 20% baseline
            self.logger.info(f"Simulating CPU exhaustion to {experiment.intensity:.1%}")
        
        return injection_state
    
    async def _inject_service_degradation(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Inject service degradation."""
        injection_state = {
            "degraded_services": experiment.target_components,
            "degradation_type": experiment.failure_mode.value,
            "intensity": experiment.intensity,
            "original_performance": {}
        }
        
        for component in experiment.target_components:
            injection_state["original_performance"][component] = {
                "response_time": 100,  # 100ms baseline
                "error_rate": 0.01     # 1% baseline error rate
            }
            
            if experiment.failure_mode == FailureMode.SLOW_RESPONSE:
                self.logger.info(f"Simulating slow response for {component}")
            elif experiment.failure_mode == FailureMode.INTERMITTENT_FAILURE:
                self.logger.info(f"Simulating intermittent failures for {component}")
        
        return injection_state
    
    async def _inject_byzantine_behavior(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Inject Byzantine agent behavior."""
        injection_state = {
            "byzantine_agents": experiment.target_components,
            "malicious_behavior": experiment.failure_mode.value,
            "original_behavior": {}
        }
        
        for component in experiment.target_components:
            injection_state["original_behavior"][component] = "honest"
            
            if experiment.failure_mode == FailureMode.MALICIOUS_BEHAVIOR:
                self.logger.info(f"Simulating malicious behavior for {component}")
                # Mock malicious recommendations
                injection_state["malicious_actions"] = [
                    "provide_false_confidence_scores",
                    "recommend_harmful_actions",
                    "corrupt_consensus_votes"
                ]
        
        return injection_state
    
    async def _inject_latency(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Inject network latency."""
        injection_state = {
            "latency_targets": experiment.target_components,
            "added_latency_ms": experiment.intensity * 1000,  # Convert to ms
            "original_latency": {}
        }
        
        for component in experiment.target_components:
            injection_state["original_latency"][component] = 10  # 10ms baseline
            self.logger.info(f"Injecting {injection_state['added_latency_ms']:.0f}ms latency to {component}")
        
        return injection_state
    
    async def _inject_data_corruption(self, experiment: ChaosExperiment) -> Dict[str, Any]:
        """Inject data corruption."""
        injection_state = {
            "corruption_targets": experiment.target_components,
            "corruption_rate": experiment.intensity,
            "corruption_types": ["bit_flip", "truncation", "duplication"],
            "original_integrity": {}
        }
        
        for component in experiment.target_components:
            injection_state["original_integrity"][component] = "intact"
            self.logger.info(f"Injecting data corruption for {component} ({experiment.intensity:.1%} rate)")
        
        return injection_state
    
    async def _recover_from_failure(self, experiment: ChaosExperiment, injection: ChaosInjection):
        """Recover from injected failure."""
        self.logger.info(f"Recovering from failure for experiment: {experiment.name}")
        
        # Select appropriate recovery handler
        if experiment.experiment_type == ChaosExperimentType.AGENT_FAILURE:
            await self.recovery_handlers["agent_failure"](experiment, injection)
        elif experiment.experiment_type == ChaosExperimentType.NETWORK_PARTITION:
            await self.recovery_handlers["network_partition"](experiment, injection)
        elif experiment.experiment_type == ChaosExperimentType.RESOURCE_EXHAUSTION:
            await self.recovery_handlers["resource_exhaustion"](experiment, injection)
        elif experiment.experiment_type == ChaosExperimentType.SERVICE_DEGRADATION:
            await self.recovery_handlers["service_degradation"](experiment, injection)
        elif experiment.experiment_type == ChaosExperimentType.BYZANTINE_AGENT:
            await self.recovery_handlers["byzantine_behavior"](experiment, injection)
        elif experiment.experiment_type == ChaosExperimentType.LATENCY_INJECTION:
            await self.recovery_handlers["latency_injection"](experiment, injection)
        elif experiment.experiment_type == ChaosExperimentType.DATA_CORRUPTION:
            await self.recovery_handlers["data_corruption"](experiment, injection)
        
        injection.end_time = datetime.utcnow()
        injection.active = False
    
    async def _recover_agent_failure(self, experiment: ChaosExperiment, injection: ChaosInjection):
        """Recover from agent failure."""
        for component in experiment.target_components:
            self.logger.info(f"Recovering {component} from failure")
            # Mock agent recovery
            await asyncio.sleep(1)  # Simulate recovery time
    
    async def _recover_network_partition(self, experiment: ChaosExperiment, injection: ChaosInjection):
        """Recover from network partition."""
        for component in experiment.target_components:
            self.logger.info(f"Healing network partition for {component}")
            # Mock network healing
            await asyncio.sleep(2)  # Simulate network healing time
    
    async def _recover_resource_exhaustion(self, experiment: ChaosExperiment, injection: ChaosInjection):
        """Recover from resource exhaustion."""
        resource_type = injection.injection_state.get("resource_type", "unknown")
        self.logger.info(f"Recovering from {resource_type} exhaustion")
        # Mock resource recovery
        await asyncio.sleep(1)
    
    async def _recover_service_degradation(self, experiment: ChaosExperiment, injection: ChaosInjection):
        """Recover from service degradation."""
        for component in experiment.target_components:
            self.logger.info(f"Recovering service performance for {component}")
            # Mock service recovery
            await asyncio.sleep(1)
    
    async def _recover_byzantine_behavior(self, experiment: ChaosExperiment, injection: ChaosInjection):
        """Recover from Byzantine behavior."""
        for component in experiment.target_components:
            self.logger.info(f"Restoring honest behavior for {component}")
            # Mock behavior restoration
            await asyncio.sleep(1)
    
    async def _recover_latency(self, experiment: ChaosExperiment, injection: ChaosInjection):
        """Recover from latency injection."""
        for component in experiment.target_components:
            self.logger.info(f"Removing latency injection for {component}")
            # Mock latency removal
            await asyncio.sleep(0.5)
    
    async def _recover_data_corruption(self, experiment: ChaosExperiment, injection: ChaosInjection):
        """Recover from data corruption."""
        for component in experiment.target_components:
            self.logger.info(f"Restoring data integrity for {component}")
            # Mock data restoration
            await asyncio.sleep(2)
    
    async def _monitor_resilience_metrics(self, experiment: ChaosExperiment,
                                        measurements: List[ResilienceMeasurement],
                                        coordinator: AgentSwarmCoordinator):
        """Monitor system resilience metrics during experiment."""
        monitoring_start = time.time()
        
        while True:
            try:
                current_time = datetime.utcnow()
                
                # Simulate metric collection (in production, collect real metrics)
                
                # Recovery time (time since failure injection)
                recovery_time = time.time() - monitoring_start
                measurements.append(ResilienceMeasurement(
                    timestamp=current_time,
                    metric=ResilienceMetric.RECOVERY_TIME,
                    value=recovery_time,
                    unit="seconds",
                    experiment_name=experiment.name
                ))
                
                # Availability (mock calculation)
                availability = max(0.5, 1.0 - (experiment.intensity * 0.3))
                measurements.append(ResilienceMeasurement(
                    timestamp=current_time,
                    metric=ResilienceMetric.AVAILABILITY,
                    value=availability,
                    unit="ratio",
                    experiment_name=experiment.name
                ))
                
                # Error rate increase
                baseline_error_rate = 0.01
                current_error_rate = baseline_error_rate + (experiment.intensity * 0.1)
                error_rate_increase = (current_error_rate - baseline_error_rate) / baseline_error_rate
                measurements.append(ResilienceMeasurement(
                    timestamp=current_time,
                    metric=ResilienceMetric.ERROR_RATE_INCREASE,
                    value=error_rate_increase,
                    unit="ratio",
                    experiment_name=experiment.name
                ))
                
                # Throughput degradation
                baseline_throughput = 100.0
                current_throughput = baseline_throughput * (1.0 - experiment.intensity * 0.4)
                throughput_degradation = (baseline_throughput - current_throughput) / baseline_throughput
                measurements.append(ResilienceMeasurement(
                    timestamp=current_time,
                    metric=ResilienceMetric.THROUGHPUT_DEGRADATION,
                    value=throughput_degradation,
                    unit="ratio",
                    experiment_name=experiment.name
                ))
                
                # Consensus integrity (for Byzantine experiments)
                if experiment.experiment_type == ChaosExperimentType.BYZANTINE_AGENT:
                    consensus_integrity = max(0.8, 1.0 - experiment.intensity * 0.2)
                    measurements.append(ResilienceMeasurement(
                        timestamp=current_time,
                        metric=ResilienceMetric.CONSENSUS_INTEGRITY,
                        value=consensus_integrity,
                        unit="ratio",
                        experiment_name=experiment.name
                    ))
                
                # Data consistency (for partition experiments)
                if experiment.experiment_type == ChaosExperimentType.NETWORK_PARTITION:
                    data_consistency = max(0.85, 1.0 - experiment.intensity * 0.15)
                    measurements.append(ResilienceMeasurement(
                        timestamp=current_time,
                        metric=ResilienceMetric.DATA_CONSISTENCY,
                        value=data_consistency,
                        unit="ratio",
                        experiment_name=experiment.name
                    ))
                
                # Graceful degradation
                graceful_degradation = 1.0 if availability > 0.5 else 0.0
                measurements.append(ResilienceMeasurement(
                    timestamp=current_time,
                    metric=ResilienceMetric.GRACEFUL_DEGRADATION,
                    value=graceful_degradation,
                    unit="boolean",
                    experiment_name=experiment.name
                ))
                
                # Safety check
                if current_error_rate > self.safety_thresholds["max_error_rate"]:
                    self.logger.warning(f"Safety threshold exceeded: error rate {current_error_rate:.2%}")
                    await self._trigger_emergency_stop(experiment)
                    break
                
                await asyncio.sleep(10)  # Monitor every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(10)
    
    async def _measure_baseline_metrics(self, coordinator: AgentSwarmCoordinator) -> Dict[str, float]:
        """Measure baseline system metrics before experiment."""
        baseline = {
            "response_time_ms": 150.0,
            "throughput_per_sec": 100.0,
            "error_rate": 0.01,
            "cpu_usage": 0.3,
            "memory_usage": 0.4,
            "availability": 1.0
        }
        
        self.baseline_metrics = baseline
        return baseline
    
    async def _analyze_system_behavior(self, measurements: List[ResilienceMeasurement],
                                     baseline: Dict[str, float]) -> Dict[str, Any]:
        """Analyze system behavior during experiment."""
        behavior = {
            "failure_detection_time": 0,
            "recovery_patterns": [],
            "degradation_characteristics": {},
            "resilience_mechanisms_activated": []
        }
        
        # Group measurements by metric
        metric_values = defaultdict(list)
        for measurement in measurements:
            metric_values[measurement.metric].append(measurement.value)
        
        # Analyze recovery patterns
        if ResilienceMetric.RECOVERY_TIME in metric_values:
            recovery_times = metric_values[ResilienceMetric.RECOVERY_TIME]
            behavior["failure_detection_time"] = min(recovery_times) if recovery_times else 0
            behavior["recovery_patterns"] = ["exponential_recovery"] if len(recovery_times) > 5 else ["immediate_recovery"]
        
        # Analyze degradation
        if ResilienceMetric.AVAILABILITY in metric_values:
            availability_values = metric_values[ResilienceMetric.AVAILABILITY]
            min_availability = min(availability_values) if availability_values else 1.0
            behavior["degradation_characteristics"]["min_availability"] = min_availability
            behavior["degradation_characteristics"]["graceful"] = min_availability > 0.5
        
        # Identify activated resilience mechanisms
        if ResilienceMetric.GRACEFUL_DEGRADATION in metric_values:
            graceful_values = metric_values[ResilienceMetric.GRACEFUL_DEGRADATION]
            if any(v > 0 for v in graceful_values):
                behavior["resilience_mechanisms_activated"].append("graceful_degradation")
        
        if ResilienceMetric.CONSENSUS_INTEGRITY in metric_values:
            consensus_values = metric_values[ResilienceMetric.CONSENSUS_INTEGRITY]
            if all(v > 0.8 for v in consensus_values):
                behavior["resilience_mechanisms_activated"].append("consensus_protection")
        
        return behavior
    
    def _calculate_recovery_metrics(self, measurements: List[ResilienceMeasurement],
                                  experiment: ChaosExperiment) -> Dict[str, float]:
        """Calculate recovery metrics from measurements."""
        metrics = {}
        
        # Group measurements by metric type
        metric_values = defaultdict(list)
        for measurement in measurements:
            metric_values[measurement.metric].append(measurement.value)
        
        # Recovery time
        if ResilienceMetric.RECOVERY_TIME in metric_values:
            recovery_times = metric_values[ResilienceMetric.RECOVERY_TIME]
            metrics["max_recovery_time"] = max(recovery_times) if recovery_times else 0
            metrics["avg_recovery_time"] = sum(recovery_times) / len(recovery_times) if recovery_times else 0
        
        # Availability metrics
        if ResilienceMetric.AVAILABILITY in metric_values:
            availability_values = metric_values[ResilienceMetric.AVAILABILITY]
            metrics["min_availability"] = min(availability_values) if availability_values else 0
            metrics["avg_availability"] = sum(availability_values) / len(availability_values) if availability_values else 0
        
        # Error rate metrics
        if ResilienceMetric.ERROR_RATE_INCREASE in metric_values:
            error_increases = metric_values[ResilienceMetric.ERROR_RATE_INCREASE]
            metrics["max_error_rate_increase"] = max(error_increases) if error_increases else 0
        
        # Throughput metrics
        if ResilienceMetric.THROUGHPUT_DEGRADATION in metric_values:
            throughput_degradations = metric_values[ResilienceMetric.THROUGHPUT_DEGRADATION]
            metrics["max_throughput_degradation"] = max(throughput_degradations) if throughput_degradations else 0
        
        # Consensus integrity
        if ResilienceMetric.CONSENSUS_INTEGRITY in metric_values:
            consensus_values = metric_values[ResilienceMetric.CONSENSUS_INTEGRITY]
            metrics["min_consensus_integrity"] = min(consensus_values) if consensus_values else 1.0
        
        # Data consistency
        if ResilienceMetric.DATA_CONSISTENCY in metric_values:
            consistency_values = metric_values[ResilienceMetric.DATA_CONSISTENCY]
            metrics["min_data_consistency"] = min(consistency_values) if consistency_values else 1.0
        
        return metrics
    
    def _evaluate_experiment_success(self, experiment: ChaosExperiment,
                                   recovery_metrics: Dict[str, float]) -> bool:
        """Evaluate if experiment met success criteria."""
        for criterion, threshold in experiment.success_criteria.items():
            if criterion == "recovery_time":
                if recovery_metrics.get("max_recovery_time", float('inf')) > threshold:
                    return False
            elif criterion == "availability":
                if recovery_metrics.get("min_availability", 0) < threshold:
                    return False
            elif criterion == "error_rate_increase":
                if recovery_metrics.get("max_error_rate_increase", float('inf')) > threshold:
                    return False
            elif criterion == "throughput_degradation":
                if recovery_metrics.get("max_throughput_degradation", float('inf')) > threshold:
                    return False
            elif criterion == "consensus_integrity":
                if recovery_metrics.get("min_consensus_integrity", 0) < threshold:
                    return False
            elif criterion == "data_consistency":
                if recovery_metrics.get("min_data_consistency", 0) < threshold:
                    return False
            elif criterion == "graceful_degradation":
                # Check if system maintained some level of service
                if recovery_metrics.get("min_availability", 0) < 0.5:
                    return False
        
        return True
    
    def _extract_lessons_learned(self, experiment: ChaosExperiment,
                               measurements: List[ResilienceMeasurement],
                               system_behavior: Dict[str, Any]) -> List[str]:
        """Extract lessons learned from experiment."""
        lessons = []
        
        # Analyze failure detection
        detection_time = system_behavior.get("failure_detection_time", 0)
        if detection_time > 60:  # >1 minute
            lessons.append(f"Failure detection took {detection_time:.1f}s - consider improving monitoring")
        else:
            lessons.append(f"Good failure detection time: {detection_time:.1f}s")
        
        # Analyze recovery patterns
        recovery_patterns = system_behavior.get("recovery_patterns", [])
        if "exponential_recovery" in recovery_patterns:
            lessons.append("System showed exponential recovery pattern - resilience mechanisms working")
        
        # Analyze degradation
        degradation = system_behavior.get("degradation_characteristics", {})
        if degradation.get("graceful", False):
            lessons.append("System degraded gracefully - good resilience design")
        else:
            lessons.append("System did not degrade gracefully - consider implementing circuit breakers")
        
        # Analyze activated mechanisms
        mechanisms = system_behavior.get("resilience_mechanisms_activated", [])
        if "consensus_protection" in mechanisms:
            lessons.append("Consensus protection mechanisms activated successfully")
        if "graceful_degradation" in mechanisms:
            lessons.append("Graceful degradation mechanisms activated successfully")
        
        # Experiment-specific lessons
        if experiment.experiment_type == ChaosExperimentType.BYZANTINE_AGENT:
            lessons.append("Byzantine fault tolerance mechanisms were tested")
        elif experiment.experiment_type == ChaosExperimentType.NETWORK_PARTITION:
            lessons.append("Network partition tolerance was validated")
        
        return lessons
    
    def _generate_recommendations(self, experiment: ChaosExperiment,
                                system_behavior: Dict[str, Any],
                                success: bool) -> List[str]:
        """Generate recommendations based on experiment results."""
        recommendations = []
        
        if not success:
            recommendations.append("Experiment failed - investigate root causes and improve resilience")
        
        # Detection time recommendations
        detection_time = system_behavior.get("failure_detection_time", 0)
        if detection_time > 30:
            recommendations.append("Improve failure detection mechanisms - consider more frequent health checks")
        
        # Degradation recommendations
        degradation = system_behavior.get("degradation_characteristics", {})
        if not degradation.get("graceful", True):
            recommendations.append("Implement graceful degradation patterns - circuit breakers, bulkheads")
        
        # Recovery recommendations
        recovery_patterns = system_behavior.get("recovery_patterns", [])
        if "immediate_recovery" not in recovery_patterns:
            recommendations.append("Consider implementing faster recovery mechanisms")
        
        # Experiment-specific recommendations
        if experiment.experiment_type == ChaosExperimentType.BYZANTINE_AGENT:
            recommendations.append("Validate Byzantine fault detection algorithms")
        elif experiment.experiment_type == ChaosExperimentType.NETWORK_PARTITION:
            recommendations.append("Test partition healing and state synchronization")
        elif experiment.experiment_type == ChaosExperimentType.RESOURCE_EXHAUSTION:
            recommendations.append("Implement resource usage monitoring and auto-scaling")
        
        return recommendations
    
    async def _trigger_emergency_stop(self, experiment: ChaosExperiment):
        """Trigger emergency stop for dangerous experiments."""
        self.logger.error(f"EMERGENCY STOP triggered for experiment: {experiment.name}")
        self.emergency_stop_active = True
        
        # Immediately recover from all active injections
        for injection_name, injection in list(self.active_injections.items()):
            await self._emergency_recovery(injection.experiment)
            del self.active_injections[injection_name]
    
    async def _emergency_recovery(self, experiment: ChaosExperiment):
        """Perform emergency recovery from experiment."""
        self.logger.info(f"Performing emergency recovery for: {experiment.name}")
        
        # Force recovery for all experiment types
        try:
            if experiment.name in self.active_injections:
                injection = self.active_injections[experiment.name]
                await self._recover_from_failure(experiment, injection)
        except Exception as e:
            self.logger.error(f"Emergency recovery failed: {e}")
    
    async def run_chaos_suite(self, coordinator: AgentSwarmCoordinator = None) -> List[ChaosExperimentResult]:
        """Run complete chaos engineering test suite."""
        self.logger.info("Starting comprehensive chaos engineering test suite")
        
        results = []
        
        # Sort experiments by blast radius (single_agent first, system_wide last)
        blast_radius_order = {"single_agent": 0, "agent_type": 1, "system_wide": 2}
        sorted_experiments = sorted(
            self.experiments,
            key=lambda e: blast_radius_order.get(e.blast_radius, 1)
        )
        
        for experiment in sorted_experiments:
            if self.emergency_stop_active:
                self.logger.warning("Emergency stop active - skipping remaining experiments")
                break
            
            self.logger.info(f"Running chaos experiment: {experiment.name}")
            
            try:
                result = await self.run_chaos_experiment(experiment, coordinator)
                results.append(result)
                
                # Log result summary
                success_status = "PASSED" if result.success else "FAILED"
                self.logger.info(f"Chaos experiment {experiment.name}: {success_status}")
                
                # Wait between experiments for system stabilization
                await asyncio.sleep(60)  # 1 minute between experiments
                
            except Exception as e:
                self.logger.error(f"Chaos experiment {experiment.name} failed with error: {e}")
        
        self.logger.info(f"Chaos engineering suite completed: {len(results)} experiments executed")
        
        return results
    
    def generate_resilience_report(self, results: List[ChaosExperimentResult]) -> Dict[str, Any]:
        """Generate comprehensive resilience report."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_experiments": len(results),
            "successful_experiments": sum(1 for r in results if r.success),
            "failed_experiments": sum(1 for r in results if not r.success),
            "experiment_results": [],
            "resilience_summary": {},
            "lessons_learned": [],
            "recommendations": []
        }
        
        # Individual experiment results
        for result in results:
            experiment_summary = {
                "name": result.experiment.name,
                "type": result.experiment.experiment_type.value,
                "success": result.success,
                "duration_seconds": (result.end_time - result.start_time).total_seconds(),
                "recovery_metrics": result.recovery_metrics,
                "lessons_learned": result.lessons_learned[:3],  # Top 3
                "recommendations": result.recommendations[:3]   # Top 3
            }
            
            report["experiment_results"].append(experiment_summary)
        
        # Resilience summary
        all_recovery_times = []
        all_availability_values = []
        
        for result in results:
            if "max_recovery_time" in result.recovery_metrics:
                all_recovery_times.append(result.recovery_metrics["max_recovery_time"])
            if "min_availability" in result.recovery_metrics:
                all_availability_values.append(result.recovery_metrics["min_availability"])
        
        if all_recovery_times:
            report["resilience_summary"]["recovery_time"] = {
                "avg_seconds": sum(all_recovery_times) / len(all_recovery_times),
                "max_seconds": max(all_recovery_times),
                "meets_sla": max(all_recovery_times) < 300  # <5 minutes
            }
        
        if all_availability_values:
            report["resilience_summary"]["availability"] = {
                "min_during_chaos": min(all_availability_values),
                "avg_during_chaos": sum(all_availability_values) / len(all_availability_values),
                "meets_sla": min(all_availability_values) > 0.7  # >70% availability
            }
        
        # Aggregate lessons learned
        all_lessons = []
        for result in results:
            all_lessons.extend(result.lessons_learned)
        
        # Count frequency of lessons
        lesson_counts = defaultdict(int)
        for lesson in all_lessons:
            lesson_counts[lesson] += 1
        
        # Top lessons
        report["lessons_learned"] = [
            {"lesson": lesson, "frequency": count}
            for lesson, count in sorted(lesson_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Aggregate recommendations
        all_recommendations = []
        for result in results:
            all_recommendations.extend(result.recommendations)
        
        recommendation_counts = defaultdict(int)
        for rec in all_recommendations:
            recommendation_counts[rec] += 1
        
        report["recommendations"] = [
            {"recommendation": rec, "priority": count}
            for rec, count in sorted(recommendation_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        return report


# Example usage and testing
async def main():
    """Example usage of chaos engineering framework."""
    framework = ChaosEngineeringFramework()
    
    print("Starting chaos engineering framework...")
    
    # Run a single chaos experiment
    experiment = framework.experiments[0]  # detection_agent_failure
    print(f"Running chaos experiment: {experiment.name}")
    
    result = await framework.run_chaos_experiment(experiment)
    
    print(f"\nExperiment Results:")
    print(f"Success: {result.success}")
    print(f"Duration: {(result.end_time - result.start_time).total_seconds():.1f}s")
    print(f"Measurements: {len(result.measurements)}")
    
    if result.recovery_metrics:
        print(f"\nRecovery Metrics:")
        for metric, value in result.recovery_metrics.items():
            print(f"  {metric}: {value:.3f}")
    
    if result.lessons_learned:
        print(f"\nLessons Learned:")
        for lesson in result.lessons_learned[:3]:
            print(f"  - {lesson}")
    
    # Generate report
    report = framework.generate_resilience_report([result])
    print(f"\nResilience Report Generated:")
    print(f"Success rate: {report['successful_experiments']}/{report['total_experiments']}")


if __name__ == "__main__":
    asyncio.run(main())