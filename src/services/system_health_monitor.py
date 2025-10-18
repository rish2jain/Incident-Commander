"""
Comprehensive System Health Monitoring for the Incident Commander.

This module monitors the health of the incident response system itself,
detecting meta-incidents and triggering automated recovery procedures.
"""

import asyncio
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum

from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
from src.models.agent import AgentStatus, AgentType
from src.services.aws import AWSServiceFactory
from src.utils.logging import get_logger
from src.utils.constants import PERFORMANCE_TARGETS


logger = get_logger("system_health_monitor")


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILING = "failing"


class MetricType(Enum):
    """Types of health metrics."""
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    RESOURCE = "resource"
    AGENT = "agent"
    CONSENSUS = "consensus"
    EXTERNAL = "external"


@dataclass
class HealthMetric:
    """Individual health metric."""
    name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    metric_type: MetricType
    timestamp: datetime
    status: HealthStatus
    details: Dict[str, Any]


@dataclass
class SystemHealthSnapshot:
    """Complete system health snapshot."""
    timestamp: datetime
    overall_status: HealthStatus
    metrics: List[HealthMetric]
    active_agents: Dict[str, AgentStatus]
    performance_summary: Dict[str, float]
    resource_utilization: Dict[str, float]
    external_dependencies: Dict[str, HealthStatus]
    meta_incidents: List[str]


@dataclass
class MetaIncident:
    """Meta-incident affecting the incident response system."""
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    affected_components: List[str]
    detected_at: datetime
    root_cause: Optional[str]
    recovery_actions: List[str]
    status: str


class SystemHealthMonitor:
    """Comprehensive system health monitoring and meta-incident detection."""
    
    def __init__(self, aws_factory: AWSServiceFactory):
        """Initialize system health monitor."""
        self.aws_factory = aws_factory
        
        # Health monitoring configuration
        self.monitoring_interval = timedelta(seconds=30)
        self.metric_retention_period = timedelta(hours=24)
        self.degradation_threshold = 0.8  # 80% of normal performance
        self.critical_threshold = 0.6     # 60% of normal performance
        
        # Health data storage
        self.health_history: deque = deque(maxlen=2880)  # 24 hours at 30s intervals
        self.current_metrics: Dict[str, HealthMetric] = {}
        self.meta_incidents: Dict[str, MetaIncident] = {}
        self.recovery_actions_taken: List[Dict[str, Any]] = []
        
        # Performance baselines
        self.performance_baselines: Dict[str, float] = {}
        self.baseline_calculation_window = timedelta(hours=1)
        
        # External dependency tracking
        self.external_dependencies = {
            "aws_bedrock": {"endpoint": "bedrock", "timeout": 5},
            "aws_dynamodb": {"endpoint": "dynamodb", "timeout": 3},
            "aws_kinesis": {"endpoint": "kinesis", "timeout": 3},
            "opensearch": {"endpoint": "opensearch", "timeout": 5},
            "redis": {"endpoint": "redis", "timeout": 2}
        }
        
        # Agent health tracking
        self.agent_health_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=120))  # 1 hour at 30s intervals
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        logger.info("Initialized System Health Monitor")
    
    async def start_monitoring(self):
        """Start continuous system health monitoring."""
        if self.is_monitoring:
            logger.warning("System health monitoring already running")
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Started system health monitoring")
    
    async def stop_monitoring(self):
        """Stop system health monitoring."""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped system health monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        try:
            while self.is_monitoring:
                start_time = time.time()
                
                # Collect health metrics
                health_snapshot = await self._collect_health_metrics()
                
                # Store snapshot
                self.health_history.append(health_snapshot)
                
                # Detect meta-incidents
                await self._detect_meta_incidents(health_snapshot)
                
                # Trigger recovery actions if needed
                await self._trigger_recovery_actions(health_snapshot)
                
                # Update performance baselines
                await self._update_performance_baselines(health_snapshot)
                
                # Calculate sleep time to maintain interval
                elapsed = time.time() - start_time
                sleep_time = max(0, self.monitoring_interval.total_seconds() - elapsed)
                
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                
        except asyncio.CancelledError:
            logger.info("System health monitoring cancelled")
        except Exception as e:
            logger.error(f"System health monitoring error: {e}")
            # Continue monitoring despite errors
            if self.is_monitoring:
                await asyncio.sleep(self.monitoring_interval.total_seconds())
                await self._monitoring_loop()
    
    async def _collect_health_metrics(self) -> SystemHealthSnapshot:
        """Collect comprehensive system health metrics."""
        timestamp = datetime.utcnow()
        metrics = []
        
        # Collect performance metrics
        performance_metrics = await self._collect_performance_metrics()
        metrics.extend(performance_metrics)
        
        # Collect resource utilization metrics
        resource_metrics = await self._collect_resource_metrics()
        metrics.extend(resource_metrics)
        
        # Collect agent health metrics
        agent_metrics = await self._collect_agent_health_metrics()
        metrics.extend(agent_metrics)
        
        # Collect external dependency metrics
        external_metrics = await self._collect_external_dependency_metrics()
        metrics.extend(external_metrics)
        
        # Collect consensus engine metrics
        consensus_metrics = await self._collect_consensus_metrics()
        metrics.extend(consensus_metrics)
        
        # Determine overall system status
        overall_status = self._calculate_overall_status(metrics)
        
        # Create health snapshot
        snapshot = SystemHealthSnapshot(
            timestamp=timestamp,
            overall_status=overall_status,
            metrics=metrics,
            active_agents=await self._get_active_agents_status(),
            performance_summary=self._calculate_performance_summary(performance_metrics),
            resource_utilization=self._calculate_resource_summary(resource_metrics),
            external_dependencies=self._calculate_external_dependencies_summary(external_metrics),
            meta_incidents=list(self.meta_incidents.keys())
        )
        
        return snapshot
    
    async def _collect_performance_metrics(self) -> List[HealthMetric]:
        """Collect system performance metrics."""
        metrics = []
        
        # Agent response times
        for agent_type in ["detection", "diagnosis", "prediction", "resolution", "communication"]:
            target_time = PERFORMANCE_TARGETS.get(agent_type, {}).get("target", 60)
            max_time = PERFORMANCE_TARGETS.get(agent_type, {}).get("max", 120)
            
            # Get recent response times from agent history
            recent_times = self._get_recent_agent_response_times(agent_type)
            if recent_times:
                avg_response_time = sum(recent_times) / len(recent_times)
                
                status = HealthStatus.HEALTHY
                if avg_response_time > max_time:
                    status = HealthStatus.CRITICAL
                elif avg_response_time > target_time * 1.5:
                    status = HealthStatus.DEGRADED
                
                metrics.append(HealthMetric(
                    name=f"{agent_type}_response_time",
                    value=avg_response_time,
                    threshold_warning=target_time * 1.5,
                    threshold_critical=max_time,
                    metric_type=MetricType.PERFORMANCE,
                    timestamp=datetime.utcnow(),
                    status=status,
                    details={"recent_samples": len(recent_times), "target": target_time}
                ))
        
        # Consensus decision time
        consensus_times = self._get_recent_consensus_times()
        if consensus_times:
            avg_consensus_time = sum(consensus_times) / len(consensus_times)
            
            status = HealthStatus.HEALTHY
            if avg_consensus_time > 30:  # 30 seconds threshold
                status = HealthStatus.CRITICAL
            elif avg_consensus_time > 15:
                status = HealthStatus.DEGRADED
            
            metrics.append(HealthMetric(
                name="consensus_decision_time",
                value=avg_consensus_time,
                threshold_warning=15.0,
                threshold_critical=30.0,
                metric_type=MetricType.PERFORMANCE,
                timestamp=datetime.utcnow(),
                status=status,
                details={"recent_samples": len(consensus_times)}
            ))
        
        # API response times
        api_response_time = await self._measure_api_response_time()
        status = HealthStatus.HEALTHY
        if api_response_time > 2.0:
            status = HealthStatus.CRITICAL
        elif api_response_time > 1.0:
            status = HealthStatus.DEGRADED
        
        metrics.append(HealthMetric(
            name="api_response_time",
            value=api_response_time,
            threshold_warning=1.0,
            threshold_critical=2.0,
            metric_type=MetricType.PERFORMANCE,
            timestamp=datetime.utcnow(),
            status=status,
            details={"endpoint": "/system/health"}
        ))
        
        return metrics
    
    async def _collect_resource_metrics(self) -> List[HealthMetric]:
        """Collect system resource utilization metrics."""
        metrics = []
        
        # CPU utilization
        cpu_percent = psutil.cpu_percent(interval=1)
        status = HealthStatus.HEALTHY
        if cpu_percent > 90:
            status = HealthStatus.CRITICAL
        elif cpu_percent > 75:
            status = HealthStatus.DEGRADED
        
        metrics.append(HealthMetric(
            name="cpu_utilization",
            value=cpu_percent,
            threshold_warning=75.0,
            threshold_critical=90.0,
            metric_type=MetricType.RESOURCE,
            timestamp=datetime.utcnow(),
            status=status,
            details={"cores": psutil.cpu_count()}
        ))
        
        # Memory utilization
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        status = HealthStatus.HEALTHY
        if memory_percent > 90:
            status = HealthStatus.CRITICAL
        elif memory_percent > 80:
            status = HealthStatus.DEGRADED
        
        metrics.append(HealthMetric(
            name="memory_utilization",
            value=memory_percent,
            threshold_warning=80.0,
            threshold_critical=90.0,
            metric_type=MetricType.RESOURCE,
            timestamp=datetime.utcnow(),
            status=status,
            details={"total_gb": memory.total / (1024**3), "available_gb": memory.available / (1024**3)}
        ))
        
        # Disk utilization
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        status = HealthStatus.HEALTHY
        if disk_percent > 90:
            status = HealthStatus.CRITICAL
        elif disk_percent > 80:
            status = HealthStatus.DEGRADED
        
        metrics.append(HealthMetric(
            name="disk_utilization",
            value=disk_percent,
            threshold_warning=80.0,
            threshold_critical=90.0,
            metric_type=MetricType.RESOURCE,
            timestamp=datetime.utcnow(),
            status=status,
            details={"total_gb": disk.total / (1024**3), "free_gb": disk.free / (1024**3)}
        ))
        
        return metrics
    
    async def _collect_agent_health_metrics(self) -> List[HealthMetric]:
        """Collect agent health metrics."""
        metrics = []
        
        # Get agent status from swarm coordinator
        try:
            from src.orchestrator.swarm_coordinator import get_swarm_coordinator
            coordinator = get_swarm_coordinator()
            
            agent_statuses = await coordinator.get_agent_health_status()
            
            for agent_name, agent_status in agent_statuses.items():
                # Agent availability
                is_healthy = agent_status.get("status") == "healthy"
                
                metrics.append(HealthMetric(
                    name=f"{agent_name}_availability",
                    value=1.0 if is_healthy else 0.0,
                    threshold_warning=1.0,
                    threshold_critical=0.0,
                    metric_type=MetricType.AGENT,
                    timestamp=datetime.utcnow(),
                    status=HealthStatus.HEALTHY if is_healthy else HealthStatus.CRITICAL,
                    details=agent_status
                ))
                
                # Agent error rate
                error_count = agent_status.get("error_count", 0)
                processing_count = agent_status.get("processing_count", 1)
                error_rate = error_count / max(processing_count, 1)
                
                status = HealthStatus.HEALTHY
                if error_rate > 0.2:  # 20% error rate
                    status = HealthStatus.CRITICAL
                elif error_rate > 0.1:  # 10% error rate
                    status = HealthStatus.DEGRADED
                
                metrics.append(HealthMetric(
                    name=f"{agent_name}_error_rate",
                    value=error_rate,
                    threshold_warning=0.1,
                    threshold_critical=0.2,
                    metric_type=MetricType.AGENT,
                    timestamp=datetime.utcnow(),
                    status=status,
                    details={"error_count": error_count, "processing_count": processing_count}
                ))
        
        except Exception as e:
            logger.error(f"Error collecting agent health metrics: {e}")
        
        return metrics
    
    async def _collect_external_dependency_metrics(self) -> List[HealthMetric]:
        """Collect external dependency health metrics."""
        metrics = []
        
        for dep_name, dep_config in self.external_dependencies.items():
            try:
                # Test dependency connectivity
                start_time = time.time()
                is_available = await self._test_dependency_connectivity(dep_name, dep_config)
                response_time = time.time() - start_time
                
                # Availability metric
                metrics.append(HealthMetric(
                    name=f"{dep_name}_availability",
                    value=1.0 if is_available else 0.0,
                    threshold_warning=1.0,
                    threshold_critical=0.0,
                    metric_type=MetricType.EXTERNAL,
                    timestamp=datetime.utcnow(),
                    status=HealthStatus.HEALTHY if is_available else HealthStatus.CRITICAL,
                    details={"endpoint": dep_config["endpoint"]}
                ))
                
                # Response time metric
                if is_available:
                    timeout = dep_config["timeout"]
                    status = HealthStatus.HEALTHY
                    if response_time > timeout:
                        status = HealthStatus.CRITICAL
                    elif response_time > timeout * 0.8:
                        status = HealthStatus.DEGRADED
                    
                    metrics.append(HealthMetric(
                        name=f"{dep_name}_response_time",
                        value=response_time,
                        threshold_warning=timeout * 0.8,
                        threshold_critical=timeout,
                        metric_type=MetricType.EXTERNAL,
                        timestamp=datetime.utcnow(),
                        status=status,
                        details={"timeout": timeout}
                    ))
            
            except Exception as e:
                logger.error(f"Error testing dependency {dep_name}: {e}")
                metrics.append(HealthMetric(
                    name=f"{dep_name}_availability",
                    value=0.0,
                    threshold_warning=1.0,
                    threshold_critical=0.0,
                    metric_type=MetricType.EXTERNAL,
                    timestamp=datetime.utcnow(),
                    status=HealthStatus.CRITICAL,
                    details={"error": str(e)}
                ))
        
        return metrics
    
    async def _collect_consensus_metrics(self) -> List[HealthMetric]:
        """Collect consensus engine health metrics."""
        metrics = []
        
        try:
            from src.services.consensus import get_consensus_engine
            consensus_engine = get_consensus_engine()
            
            stats = consensus_engine.get_consensus_statistics()
            
            # Consensus success rate
            success_rate = 1.0 - stats.get("escalation_rate", 0.0)
            status = HealthStatus.HEALTHY
            if success_rate < 0.7:
                status = HealthStatus.CRITICAL
            elif success_rate < 0.8:
                status = HealthStatus.DEGRADED
            
            metrics.append(HealthMetric(
                name="consensus_success_rate",
                value=success_rate,
                threshold_warning=0.8,
                threshold_critical=0.7,
                metric_type=MetricType.CONSENSUS,
                timestamp=datetime.utcnow(),
                status=status,
                details=stats
            ))
            
            # Conflict rate
            conflict_rate = stats.get("conflict_rate", 0.0)
            status = HealthStatus.HEALTHY
            if conflict_rate > 0.3:
                status = HealthStatus.CRITICAL
            elif conflict_rate > 0.2:
                status = HealthStatus.DEGRADED
            
            metrics.append(HealthMetric(
                name="consensus_conflict_rate",
                value=conflict_rate,
                threshold_warning=0.2,
                threshold_critical=0.3,
                metric_type=MetricType.CONSENSUS,
                timestamp=datetime.utcnow(),
                status=status,
                details={"total_decisions": stats.get("total_decisions", 0)}
            ))
        
        except Exception as e:
            logger.error(f"Error collecting consensus metrics: {e}")
        
        return metrics
    
    async def _detect_meta_incidents(self, health_snapshot: SystemHealthSnapshot):
        """Detect meta-incidents affecting the incident response system."""
        current_time = datetime.utcnow()
        
        # Check for system-wide degradation
        critical_metrics = [m for m in health_snapshot.metrics if m.status == HealthStatus.CRITICAL]
        degraded_metrics = [m for m in health_snapshot.metrics if m.status == HealthStatus.DEGRADED]
        
        # Meta-incident: Multiple agents failing
        failing_agents = [m for m in critical_metrics if m.metric_type == MetricType.AGENT and "availability" in m.name]
        if len(failing_agents) >= 2:
            incident_id = f"meta_agent_failure_{int(current_time.timestamp())}"
            if incident_id not in self.meta_incidents:
                meta_incident = MetaIncident(
                    id=incident_id,
                    title="Multiple Agent Failure",
                    description=f"{len(failing_agents)} agents are currently failing",
                    severity=IncidentSeverity.CRITICAL,
                    affected_components=[m.name.replace("_availability", "") for m in failing_agents],
                    detected_at=current_time,
                    root_cause=None,
                    recovery_actions=["restart_agents", "check_dependencies"],
                    status="active"
                )
                self.meta_incidents[incident_id] = meta_incident
                logger.critical(f"Meta-incident detected: {meta_incident.title}")
        
        # Meta-incident: Resource exhaustion
        resource_critical = [m for m in critical_metrics if m.metric_type == MetricType.RESOURCE]
        if len(resource_critical) >= 2:
            incident_id = f"meta_resource_exhaustion_{int(current_time.timestamp())}"
            if incident_id not in self.meta_incidents:
                meta_incident = MetaIncident(
                    id=incident_id,
                    title="System Resource Exhaustion",
                    description=f"Multiple system resources are critically low: {[m.name for m in resource_critical]}",
                    severity=IncidentSeverity.HIGH,
                    affected_components=[m.name for m in resource_critical],
                    detected_at=current_time,
                    root_cause=None,
                    recovery_actions=["scale_resources", "cleanup_processes"],
                    status="active"
                )
                self.meta_incidents[incident_id] = meta_incident
                logger.error(f"Meta-incident detected: {meta_incident.title}")
        
        # Meta-incident: External dependency failures
        external_failures = [m for m in critical_metrics if m.metric_type == MetricType.EXTERNAL and "availability" in m.name]
        if len(external_failures) >= 2:
            incident_id = f"meta_dependency_failure_{int(current_time.timestamp())}"
            if incident_id not in self.meta_incidents:
                meta_incident = MetaIncident(
                    id=incident_id,
                    title="Multiple External Dependency Failures",
                    description=f"Multiple external dependencies are failing: {[m.name for m in external_failures]}",
                    severity=IncidentSeverity.HIGH,
                    affected_components=[m.name.replace("_availability", "") for m in external_failures],
                    detected_at=current_time,
                    root_cause=None,
                    recovery_actions=["check_network", "verify_credentials", "contact_vendors"],
                    status="active"
                )
                self.meta_incidents[incident_id] = meta_incident
                logger.error(f"Meta-incident detected: {meta_incident.title}")
        
        # Meta-incident: Consensus system failure
        consensus_failures = [m for m in critical_metrics if m.metric_type == MetricType.CONSENSUS]
        if consensus_failures:
            incident_id = f"meta_consensus_failure_{int(current_time.timestamp())}"
            if incident_id not in self.meta_incidents:
                meta_incident = MetaIncident(
                    id=incident_id,
                    title="Consensus System Failure",
                    description="Consensus engine is failing to reach decisions",
                    severity=IncidentSeverity.CRITICAL,
                    affected_components=["consensus_engine"],
                    detected_at=current_time,
                    root_cause=None,
                    recovery_actions=["restart_consensus_engine", "check_agent_health"],
                    status="active"
                )
                self.meta_incidents[incident_id] = meta_incident
                logger.critical(f"Meta-incident detected: {meta_incident.title}")
    
    async def _trigger_recovery_actions(self, health_snapshot: SystemHealthSnapshot):
        """Trigger automated recovery actions based on health status."""
        current_time = datetime.utcnow()
        
        for meta_incident in self.meta_incidents.values():
            if meta_incident.status != "active":
                continue
            
            # Execute recovery actions
            for action in meta_incident.recovery_actions:
                if not await self._has_recent_recovery_action(action, timedelta(minutes=10)):
                    success = await self._execute_recovery_action(action, meta_incident)
                    
                    self.recovery_actions_taken.append({
                        "action": action,
                        "meta_incident_id": meta_incident.id,
                        "timestamp": current_time,
                        "success": success
                    })
                    
                    logger.info(f"Executed recovery action '{action}' for meta-incident {meta_incident.id}: {'SUCCESS' if success else 'FAILED'}")
    
    async def _execute_recovery_action(self, action: str, meta_incident: MetaIncident) -> bool:
        """Execute a specific recovery action."""
        try:
            if action == "restart_agents":
                return await self._restart_failing_agents(meta_incident.affected_components)
            elif action == "scale_resources":
                return await self._scale_system_resources()
            elif action == "cleanup_processes":
                return await self._cleanup_system_processes()
            elif action == "check_dependencies":
                return await self._check_and_repair_dependencies()
            elif action == "restart_consensus_engine":
                return await self._restart_consensus_engine()
            else:
                logger.warning(f"Unknown recovery action: {action}")
                return False
        
        except Exception as e:
            logger.error(f"Recovery action '{action}' failed: {e}")
            return False
    
    async def _restart_failing_agents(self, agent_names: List[str]) -> bool:
        """Restart failing agents."""
        try:
            from src.orchestrator.swarm_coordinator import get_swarm_coordinator
            coordinator = get_swarm_coordinator()
            
            for agent_name in agent_names:
                await coordinator.restart_agent(agent_name)
            
            return True
        except Exception as e:
            logger.error(f"Failed to restart agents: {e}")
            return False
    
    async def _scale_system_resources(self) -> bool:
        """Scale system resources (placeholder for actual implementation)."""
        # In a real implementation, this would trigger auto-scaling
        logger.info("Resource scaling triggered (placeholder)")
        return True
    
    async def _cleanup_system_processes(self) -> bool:
        """Clean up system processes to free resources."""
        try:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear old health history if memory is low
            if len(self.health_history) > 1440:  # Keep last 12 hours
                while len(self.health_history) > 1440:
                    self.health_history.popleft()
            
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup processes: {e}")
            return False
    
    async def _check_and_repair_dependencies(self) -> bool:
        """Check and attempt to repair external dependencies."""
        try:
            # Test all dependencies and log results
            for dep_name, dep_config in self.external_dependencies.items():
                is_available = await self._test_dependency_connectivity(dep_name, dep_config)
                logger.info(f"Dependency {dep_name}: {'AVAILABLE' if is_available else 'UNAVAILABLE'}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to check dependencies: {e}")
            return False
    
    async def _restart_consensus_engine(self) -> bool:
        """Restart the consensus engine."""
        try:
            # In a real implementation, this would restart the consensus service
            logger.info("Consensus engine restart triggered (placeholder)")
            return True
        except Exception as e:
            logger.error(f"Failed to restart consensus engine: {e}")
            return False
    
    # Helper methods
    
    def _calculate_overall_status(self, metrics: List[HealthMetric]) -> HealthStatus:
        """Calculate overall system health status."""
        if not metrics:
            return HealthStatus.HEALTHY
        
        critical_count = sum(1 for m in metrics if m.status == HealthStatus.CRITICAL)
        degraded_count = sum(1 for m in metrics if m.status == HealthStatus.DEGRADED)
        
        if critical_count > 0:
            return HealthStatus.CRITICAL
        elif degraded_count >= 3:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def _calculate_performance_summary(self, metrics: List[HealthMetric]) -> Dict[str, float]:
        """Calculate performance summary from metrics."""
        summary = {}
        for metric in metrics:
            if metric.metric_type == MetricType.PERFORMANCE:
                summary[metric.name] = metric.value
        return summary
    
    def _calculate_resource_summary(self, metrics: List[HealthMetric]) -> Dict[str, float]:
        """Calculate resource utilization summary."""
        summary = {}
        for metric in metrics:
            if metric.metric_type == MetricType.RESOURCE:
                summary[metric.name] = metric.value
        return summary
    
    def _calculate_external_dependencies_summary(self, metrics: List[HealthMetric]) -> Dict[str, HealthStatus]:
        """Calculate external dependencies status summary."""
        summary = {}
        for metric in metrics:
            if metric.metric_type == MetricType.EXTERNAL and "availability" in metric.name:
                dep_name = metric.name.replace("_availability", "")
                summary[dep_name] = metric.status
        return summary
    
    async def _get_active_agents_status(self) -> Dict[str, AgentStatus]:
        """Get status of all active agents."""
        try:
            from src.orchestrator.swarm_coordinator import get_swarm_coordinator
            coordinator = get_swarm_coordinator()
            return await coordinator.get_agent_health_status()
        except Exception as e:
            logger.error(f"Failed to get agent status: {e}")
            return {}
    
    def _get_recent_agent_response_times(self, agent_type: str) -> List[float]:
        """Get recent response times for an agent type."""
        # Placeholder - in real implementation would get from agent metrics
        return []
    
    def _get_recent_consensus_times(self) -> List[float]:
        """Get recent consensus decision times."""
        # Placeholder - in real implementation would get from consensus engine
        return []
    
    async def _measure_api_response_time(self) -> float:
        """Measure API response time."""
        try:
            start_time = time.time()
            # Simulate API call - in real implementation would call actual endpoint
            await asyncio.sleep(0.1)
            return time.time() - start_time
        except Exception:
            return 5.0  # Return high value on error
    
    async def _test_dependency_connectivity(self, dep_name: str, dep_config: Dict[str, Any]) -> bool:
        """Test connectivity to an external dependency."""
        try:
            # Simulate dependency test - in real implementation would test actual connectivity
            await asyncio.sleep(0.1)
            return True
        except Exception:
            return False
    
    async def _has_recent_recovery_action(self, action: str, time_window: timedelta) -> bool:
        """Check if a recovery action was recently executed."""
        cutoff_time = datetime.utcnow() - time_window
        return any(
            ra["action"] == action and ra["timestamp"] > cutoff_time
            for ra in self.recovery_actions_taken
        )
    
    async def _update_performance_baselines(self, health_snapshot: SystemHealthSnapshot):
        """Update performance baselines based on recent healthy periods."""
        # Placeholder for baseline calculation logic
        pass
    
    def get_current_health_status(self) -> Dict[str, Any]:
        """Get current system health status."""
        if not self.health_history:
            return {"status": "unknown", "message": "No health data available"}
        
        latest_snapshot = self.health_history[-1]
        
        return {
            "overall_status": latest_snapshot.overall_status.value,
            "timestamp": latest_snapshot.timestamp.isoformat(),
            "metrics_count": len(latest_snapshot.metrics),
            "active_agents": len(latest_snapshot.active_agents),
            "meta_incidents": len(latest_snapshot.meta_incidents),
            "performance_summary": latest_snapshot.performance_summary,
            "resource_utilization": latest_snapshot.resource_utilization,
            "external_dependencies": {k: v.value for k, v in latest_snapshot.external_dependencies.items()}
        }
    
    def get_meta_incidents(self) -> List[Dict[str, Any]]:
        """Get all active meta-incidents."""
        return [asdict(incident) for incident in self.meta_incidents.values()]


# Global system health monitor instance
system_health_monitor: Optional[SystemHealthMonitor] = None


def get_system_health_monitor(aws_factory: AWSServiceFactory) -> SystemHealthMonitor:
    """Get or create global system health monitor instance."""
    global system_health_monitor
    if system_health_monitor is None:
        system_health_monitor = SystemHealthMonitor(aws_factory)
    return system_health_monitor