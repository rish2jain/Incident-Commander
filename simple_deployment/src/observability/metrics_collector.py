"""
Comprehensive metrics collection using CloudWatch and Prometheus.

Tracks system performance, business metrics, and operational KPIs
for monitoring and alerting.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import aioboto3
from prometheus_client import Counter, Gauge, Histogram, Summary

from src.utils.logging import get_logger


logger = get_logger("observability.metrics")


class MetricType(Enum):
    """Metric types."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """A metric value with metadata."""

    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    dimensions: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


class MetricsCollector:
    """
    Comprehensive metrics collector for observability.

    Features:
    - CloudWatch metrics publishing
    - Prometheus metrics exposure
    - Business KPI tracking
    - Performance monitoring
    - Real-time alerting support
    """

    def __init__(
        self,
        namespace: str = "IncidentCommander",
        region: str = "us-east-1",
        enable_cloudwatch: bool = True,
        enable_prometheus: bool = True,
    ):
        self.namespace = namespace
        self.region = region
        self.enable_cloudwatch = enable_cloudwatch
        self.enable_prometheus = enable_prometheus

        # AWS session
        self._session = aioboto3.Session()

        # Prometheus metrics
        if enable_prometheus:
            self._setup_prometheus_metrics()

        # Metric buffer for batch publishing
        self._metric_buffer: List[MetricValue] = []
        self._buffer_size = 20
        self._flush_interval = 60  # seconds

        # Background task
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info(
            "MetricsCollector initialized",
            extra={
                "namespace": namespace,
                "cloudwatch": enable_cloudwatch,
                "prometheus": enable_prometheus,
            },
        )

    def _setup_prometheus_metrics(self) -> None:
        """Set up Prometheus metrics."""
        # Incident metrics
        self.incidents_total = Counter(
            "incidents_total",
            "Total number of incidents processed",
            ["severity", "status"],
        )

        self.incident_processing_duration = Histogram(
            "incident_processing_duration_seconds",
            "Time spent processing incidents",
            ["phase"],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
        )

        # Agent metrics
        self.agent_executions = Counter(
            "agent_executions_total",
            "Total number of agent executions",
            ["agent_name", "status"],
        )

        self.agent_latency = Summary(
            "agent_latency_seconds",
            "Agent execution latency",
            ["agent_name"],
        )

        # Consensus metrics
        self.consensus_decisions = Counter(
            "consensus_decisions_total",
            "Total number of consensus decisions",
            ["method", "result"],
        )

        self.consensus_confidence = Gauge(
            "consensus_confidence",
            "Current consensus confidence score",
            ["proposal_id"],
        )

        # Business metrics
        self.business_impact_cost = Gauge(
            "business_impact_cost_dollars",
            "Estimated business impact cost",
            ["incident_id"],
        )

        self.mttr_seconds = Histogram(
            "mttr_seconds",
            "Mean Time To Resolution",
            buckets=(60, 180, 300, 600, 1800, 3600),
        )

        # System metrics
        self.active_incidents = Gauge(
            "active_incidents",
            "Number of active incidents",
        )

        self.circuit_breaker_state = Gauge(
            "circuit_breaker_state",
            "Circuit breaker state (0=closed, 1=open, 2=half-open)",
            ["service"],
        )

    async def start(self) -> None:
        """Start the metrics collector background tasks."""
        if self._running:
            return

        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
        logger.info("MetricsCollector started")

    async def stop(self) -> None:
        """Stop the metrics collector background tasks."""
        if not self._running:
            return

        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Flush remaining metrics
        await self.flush()
        logger.info("MetricsCollector stopped")

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "Count",
        dimensions: Optional[Dict[str, str]] = None,
        metric_type: MetricType = MetricType.GAUGE,
    ) -> None:
        """Record a custom metric."""
        metric = MetricValue(
            name=name,
            value=value,
            unit=unit,
            dimensions=dimensions or {},
            metric_type=metric_type,
        )

        self._metric_buffer.append(metric)

        # Flush if buffer is full
        if len(self._metric_buffer) >= self._buffer_size:
            asyncio.create_task(self.flush())

    def record_incident_processed(
        self, incident_id: str, severity: str, duration_seconds: float
    ) -> None:
        """Record an incident being processed."""
        if self.enable_prometheus:
            self.incidents_total.labels(severity=severity, status="processed").inc()
            self.incident_processing_duration.labels(phase="total").observe(
                duration_seconds
            )

        self.record_metric(
            "IncidentsProcessed",
            1,
            unit="Count",
            dimensions={"Severity": severity},
            metric_type=MetricType.COUNTER,
        )

        self.record_metric(
            "IncidentDuration",
            duration_seconds,
            unit="Seconds",
            dimensions={"IncidentId": incident_id},
        )

    def record_agent_execution(
        self, agent_name: str, duration_seconds: float, success: bool
    ) -> None:
        """Record an agent execution."""
        status = "success" if success else "failure"

        if self.enable_prometheus:
            self.agent_executions.labels(agent_name=agent_name, status=status).inc()
            self.agent_latency.labels(agent_name=agent_name).observe(duration_seconds)

        self.record_metric(
            "AgentExecutions",
            1,
            unit="Count",
            dimensions={"AgentName": agent_name, "Status": status},
            metric_type=MetricType.COUNTER,
        )

        self.record_metric(
            "AgentLatency",
            duration_seconds,
            unit="Seconds",
            dimensions={"AgentName": agent_name},
        )

    def record_consensus_decision(
        self,
        method: str,
        confidence: float,
        participating_agents: int,
        duration_seconds: float,
    ) -> None:
        """Record a consensus decision."""
        if self.enable_prometheus:
            self.consensus_decisions.labels(method=method, result="reached").inc()

        self.record_metric(
            "ConsensusDecisions",
            1,
            unit="Count",
            dimensions={"Method": method},
            metric_type=MetricType.COUNTER,
        )

        self.record_metric(
            "ConsensusConfidence",
            confidence,
            unit="None",
            dimensions={"Method": method},
        )

        self.record_metric(
            "ConsensusLatency",
            duration_seconds,
            unit="Seconds",
            dimensions={"Method": method},
        )

    def record_business_impact(self, incident_id: str, cost_dollars: float) -> None:
        """Record business impact metrics."""
        if self.enable_prometheus:
            self.business_impact_cost.labels(incident_id=incident_id).set(cost_dollars)

        self.record_metric(
            "BusinessImpactCost",
            cost_dollars,
            unit="None",
            dimensions={"IncidentId": incident_id},
        )

    def record_mttr(self, resolution_time_seconds: float) -> None:
        """Record Mean Time To Resolution."""
        if self.enable_prometheus:
            self.mttr_seconds.observe(resolution_time_seconds)

        self.record_metric(
            "MTTR",
            resolution_time_seconds,
            unit="Seconds",
        )

    def set_active_incidents(self, count: int) -> None:
        """Set the number of active incidents."""
        if self.enable_prometheus:
            self.active_incidents.set(count)

        self.record_metric(
            "ActiveIncidents",
            count,
            unit="Count",
        )

    def set_circuit_breaker_state(self, service: str, state: str) -> None:
        """Set circuit breaker state."""
        state_values = {"closed": 0, "open": 1, "half_open": 2}
        state_value = state_values.get(state, 0)

        if self.enable_prometheus:
            self.circuit_breaker_state.labels(service=service).set(state_value)

        self.record_metric(
            "CircuitBreakerState",
            state_value,
            unit="None",
            dimensions={"Service": service},
        )

    async def flush(self) -> None:
        """Flush metrics buffer to CloudWatch."""
        if not self._metric_buffer or not self.enable_cloudwatch:
            return

        metrics_to_publish = self._metric_buffer[:]
        self._metric_buffer.clear()

        try:
            await self._publish_to_cloudwatch(metrics_to_publish)
        except Exception as e:
            logger.error(f"Failed to publish metrics to CloudWatch: {e}", exc_info=True)

    async def _publish_to_cloudwatch(self, metrics: List[MetricValue]) -> None:
        """Publish metrics to CloudWatch."""
        if not metrics:
            return

        metric_data = []
        for metric in metrics:
            data_point = {
                "MetricName": metric.name,
                "Value": metric.value,
                "Unit": metric.unit,
                "Timestamp": metric.timestamp,
            }

            if metric.dimensions:
                data_point["Dimensions"] = [
                    {"Name": k, "Value": v} for k, v in metric.dimensions.items()
                ]

            metric_data.append(data_point)

        try:
            async with self._session.client(
                "cloudwatch", region_name=self.region
            ) as client:
                # CloudWatch accepts max 20 metrics per call
                for i in range(0, len(metric_data), 20):
                    batch = metric_data[i : i + 20]
                    await client.put_metric_data(
                        Namespace=self.namespace,
                        MetricData=batch,
                    )

            logger.debug(f"Published {len(metrics)} metrics to CloudWatch")

        except Exception as e:
            logger.error(f"Failed to publish metrics: {e}", exc_info=True)
            raise

    async def _flush_loop(self) -> None:
        """Background task to periodically flush metrics."""
        while self._running:
            try:
                await asyncio.sleep(self._flush_interval)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in flush loop: {e}", exc_info=True)


# Global metrics collector instance
_collector: Optional[MetricsCollector] = None


def get_metrics_collector(
    namespace: str = "IncidentCommander",
    region: str = "us-east-1",
) -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _collector
    if _collector is None:
        _collector = MetricsCollector(namespace=namespace, region=region)
    return _collector
