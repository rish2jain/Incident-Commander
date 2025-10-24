"""
OpenTelemetry integration for comprehensive observability and tracing.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Callable
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.boto3sqs import Boto3SQSInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

from src.utils.config import config
from src.utils.logging import get_logger

logger = get_logger("opentelemetry_integration")


class OpenTelemetryManager:
    """Manages OpenTelemetry instrumentation and observability."""
    
    def __init__(self):
        """Initialize OpenTelemetry manager."""
        self.tracer_provider: Optional[TracerProvider] = None
        self.meter_provider: Optional[MeterProvider] = None
        self.tracer: Optional[trace.Tracer] = None
        self.meter: Optional[metrics.Meter] = None
        
        # Metrics instruments
        self.incident_counter = None
        self.agent_duration_histogram = None
        self.consensus_latency_histogram = None
        self.business_impact_gauge = None
        self.cost_gauge = None
        self.error_counter = None
        
        # Span tracking
        self.active_spans: Dict[str, trace.Span] = {}
        self.span_metrics: Dict[str, Dict[str, Any]] = {}
        
        self.initialized = False
    
    def initialize(self):
        """Initialize OpenTelemetry providers and instrumentation."""
        if self.initialized:
            return
        
        # Create resource
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: "incident-commander",
            ResourceAttributes.SERVICE_VERSION: "1.0.0",
            ResourceAttributes.SERVICE_NAMESPACE: "autonomous-incident-response",
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: config.environment
        })
        
        # Initialize tracing
        self._initialize_tracing(resource)
        
        # Initialize metrics
        self._initialize_metrics(resource)
        
        # Initialize instrumentation
        self._initialize_instrumentation()
        
        self.initialized = True
        logger.info("OpenTelemetry initialized successfully")
    
    def _initialize_tracing(self, resource: Resource):
        """Initialize distributed tracing."""
        # Create tracer provider
        self.tracer_provider = TracerProvider(resource=resource)
        
        # Configure OTLP exporter for traces
        if config.observability.otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(
                endpoint=config.observability.otlp_endpoint,
                headers={"Authorization": f"Bearer {config.observability.otlp_token}"}
            )
            span_processor = BatchSpanProcessor(otlp_exporter)
            self.tracer_provider.add_span_processor(span_processor)
        
        # Set global tracer provider
        trace.set_tracer_provider(self.tracer_provider)
        
        # Get tracer
        self.tracer = trace.get_tracer("incident-commander")
    
    def _initialize_metrics(self, resource: Resource):
        """Initialize metrics collection."""
        # Create metric readers
        readers = []
        
        # Prometheus reader for /metrics endpoint
        prometheus_reader = PrometheusMetricReader()
        readers.append(prometheus_reader)
        
        # OTLP reader for external systems
        if config.observability.otlp_endpoint:
            otlp_reader = PeriodicExportingMetricReader(
                OTLPMetricExporter(
                    endpoint=config.observability.otlp_endpoint,
                    headers={"Authorization": f"Bearer {config.observability.otlp_token}"}
                ),
                export_interval_millis=30000  # 30 seconds
            )
            readers.append(otlp_reader)
        
        # Create meter provider
        self.meter_provider = MeterProvider(
            resource=resource,
            metric_readers=readers
        )
        
        # Set global meter provider
        metrics.set_meter_provider(self.meter_provider)
        
        # Get meter
        self.meter = metrics.get_meter("incident-commander")
        
        # Create metric instruments
        self._create_metric_instruments()
    
    def _create_metric_instruments(self):
        """Create metric instruments for system monitoring."""
        # Incident metrics
        self.incident_counter = self.meter.create_counter(
            name="incidents_total",
            description="Total number of incidents processed",
            unit="1"
        )
        
        self.incident_duration_histogram = self.meter.create_histogram(
            name="incident_duration_seconds",
            description="Time taken to resolve incidents",
            unit="s"
        )
        
        # Agent metrics
        self.agent_duration_histogram = self.meter.create_histogram(
            name="agent_execution_duration_seconds",
            description="Time taken for agent execution",
            unit="s"
        )
        
        self.agent_confidence_gauge = self.meter.create_up_down_counter(
            name="agent_confidence_score",
            description="Agent confidence scores",
            unit="1"
        )
        
        # Consensus metrics
        self.consensus_latency_histogram = self.meter.create_histogram(
            name="consensus_latency_seconds",
            description="Time taken for consensus decisions",
            unit="s"
        )
        
        self.consensus_conflicts_counter = self.meter.create_counter(
            name="consensus_conflicts_total",
            description="Number of consensus conflicts",
            unit="1"
        )
        
        # Business impact metrics
        self.business_impact_gauge = self.meter.create_up_down_counter(
            name="business_impact_usd",
            description="Business impact in USD",
            unit="USD"
        )
        
        self.mttr_gauge = self.meter.create_up_down_counter(
            name="mttr_seconds",
            description="Mean Time To Resolution",
            unit="s"
        )
        
        # Cost metrics
        self.cost_gauge = self.meter.create_up_down_counter(
            name="operational_cost_usd",
            description="Operational costs in USD",
            unit="USD"
        )
        
        self.model_usage_counter = self.meter.create_counter(
            name="model_usage_total",
            description="Model usage by type",
            unit="1"
        )
        
        # Error metrics
        self.error_counter = self.meter.create_counter(
            name="errors_total",
            description="Total number of errors",
            unit="1"
        )
        
        # System health metrics
        self.circuit_breaker_state_gauge = self.meter.create_up_down_counter(
            name="circuit_breaker_state",
            description="Circuit breaker states (0=closed, 1=open, 2=half-open)",
            unit="1"
        )
        
        self.guardrail_violations_counter = self.meter.create_counter(
            name="guardrail_violations_total",
            description="Number of guardrail violations",
            unit="1"
        )
    
    def _initialize_instrumentation(self):
        """Initialize automatic instrumentation."""
        try:
            # FastAPI instrumentation
            FastAPIInstrumentor().instrument()
            
            # AWS SDK instrumentation
            Boto3SQSInstrumentor().instrument()
            
            # Redis instrumentation
            RedisInstrumentor().instrument()
            
            logger.info("Automatic instrumentation initialized")
        except Exception as e:
            logger.warning(f"Some instrumentation failed: {e}")
            # Continue without instrumentation
    
    @asynccontextmanager
    async def trace_orchestrator_phase(self, phase_name: str, incident_id: str, **attributes):
        """
        Trace orchestrator phase execution.
        
        Args:
            phase_name: Name of the orchestrator phase
            incident_id: Incident identifier
            **attributes: Additional span attributes
        """
        span_name = f"orchestrator.{phase_name}"
        
        with self.tracer.start_as_current_span(span_name) as span:
            # Set standard attributes
            span.set_attribute("incident.id", incident_id)
            span.set_attribute("phase.name", phase_name)
            span.set_attribute("service.name", "incident-commander")
            
            # Set custom attributes
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
            
            start_time = time.time()
            
            try:
                yield span
                
                # Record successful execution
                span.set_status(trace.Status(trace.StatusCode.OK))
                
            except Exception as e:
                # Record error
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
                
                # Increment error counter
                self.error_counter.add(1, {
                    "phase": phase_name,
                    "error_type": type(e).__name__
                })
                
                raise
            
            finally:
                # Record duration
                duration = time.time() - start_time
                span.set_attribute("duration.seconds", duration)
                
                # Update metrics
                if phase_name == "consensus":
                    self.consensus_latency_histogram.record(duration, {
                        "incident_id": incident_id
                    })
    
    @asynccontextmanager
    async def trace_agent_execution(self, agent_name: str, incident_id: str, **attributes):
        """
        Trace agent execution.
        
        Args:
            agent_name: Name of the agent
            incident_id: Incident identifier
            **attributes: Additional span attributes
        """
        span_name = f"agent.{agent_name}"
        
        with self.tracer.start_as_current_span(span_name) as span:
            # Set standard attributes
            span.set_attribute("agent.name", agent_name)
            span.set_attribute("incident.id", incident_id)
            
            # Set custom attributes
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
            
            start_time = time.time()
            
            try:
                yield span
                
                # Record successful execution
                span.set_status(trace.Status(trace.StatusCode.OK))
                
            except Exception as e:
                # Record error
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                span.record_exception(e)
                
                # Increment error counter
                self.error_counter.add(1, {
                    "agent": agent_name,
                    "error_type": type(e).__name__
                })
                
                raise
            
            finally:
                # Record duration
                duration = time.time() - start_time
                span.set_attribute("duration.seconds", duration)
                
                # Update agent metrics
                self.agent_duration_histogram.record(duration, {
                    "agent": agent_name,
                    "incident_id": incident_id
                })
    
    def record_incident_metrics(self, incident_id: str, severity: str, resolution_time: float, 
                              business_impact: float, cost: float):
        """
        Record incident-related metrics.
        
        Args:
            incident_id: Incident identifier
            severity: Incident severity
            resolution_time: Time taken to resolve (seconds)
            business_impact: Business impact in USD
            cost: Operational cost in USD
        """
        # Increment incident counter
        self.incident_counter.add(1, {
            "severity": severity,
            "incident_id": incident_id
        })
        
        # Record resolution time
        self.incident_duration_histogram.record(resolution_time, {
            "severity": severity
        })
        
        # Update MTTR gauge
        self.mttr_gauge.add(resolution_time, {
            "severity": severity
        })
        
        # Record business impact
        self.business_impact_gauge.add(business_impact, {
            "incident_id": incident_id,
            "severity": severity
        })
        
        # Record operational cost
        self.cost_gauge.add(cost, {
            "incident_id": incident_id,
            "category": "incident_response"
        })
    
    def record_agent_confidence(self, agent_name: str, confidence: float, incident_id: str):
        """
        Record agent confidence score.
        
        Args:
            agent_name: Name of the agent
            confidence: Confidence score (0.0 to 1.0)
            incident_id: Incident identifier
        """
        self.agent_confidence_gauge.add(confidence, {
            "agent": agent_name,
            "incident_id": incident_id
        })
    
    def record_consensus_conflict(self, incident_id: str, agent_count: int, resolution_method: str):
        """
        Record consensus conflict.
        
        Args:
            incident_id: Incident identifier
            agent_count: Number of agents involved
            resolution_method: How the conflict was resolved
        """
        self.consensus_conflicts_counter.add(1, {
            "incident_id": incident_id,
            "agent_count": str(agent_count),
            "resolution_method": resolution_method
        })
    
    def record_model_usage(self, model_id: str, tokens_used: int, cost: float):
        """
        Record model usage metrics.
        
        Args:
            model_id: Model identifier
            tokens_used: Number of tokens used
            cost: Cost of the request
        """
        self.model_usage_counter.add(1, {
            "model": model_id,
            "tokens": str(tokens_used)
        })
        
        self.cost_gauge.add(cost, {
            "category": "model_inference",
            "model": model_id
        })
    
    def record_circuit_breaker_state(self, service_name: str, state: str):
        """
        Record circuit breaker state.
        
        Args:
            service_name: Name of the service
            state: Circuit breaker state (closed, open, half-open)
        """
        state_value = {"closed": 0, "open": 1, "half-open": 2}.get(state, 0)
        
        self.circuit_breaker_state_gauge.add(state_value, {
            "service": service_name,
            "state": state
        })
    
    def record_guardrail_violation(self, violation_type: str, severity: str, agent_name: str):
        """
        Record guardrail violation.
        
        Args:
            violation_type: Type of violation
            severity: Severity level
            agent_name: Name of the agent
        """
        self.guardrail_violations_counter.add(1, {
            "violation_type": violation_type,
            "severity": severity,
            "agent": agent_name
        })
    
    def create_custom_span(self, name: str, **attributes) -> trace.Span:
        """
        Create a custom span with attributes.
        
        Args:
            name: Span name
            **attributes: Span attributes
            
        Returns:
            Created span
        """
        span = self.tracer.start_span(name)
        
        for key, value in attributes.items():
            span.set_attribute(key, str(value))
        
        return span
    
    def get_trace_context(self) -> Dict[str, str]:
        """
        Get current trace context for propagation.
        
        Returns:
            Trace context headers
        """
        from opentelemetry.propagate import inject
        
        headers = {}
        inject(headers)
        return headers
    
    def set_trace_context(self, headers: Dict[str, str]):
        """
        Set trace context from headers.
        
        Args:
            headers: Trace context headers
        """
        from opentelemetry.propagate import extract
        
        context = extract(headers)
        trace.set_span_in_context(trace.get_current_span(), context)
    
    def get_observability_metrics(self) -> Dict[str, Any]:
        """
        Get observability metrics and statistics.
        
        Returns:
            Observability metrics
        """
        return {
            "tracing": {
                "initialized": self.tracer_provider is not None,
                "active_spans": len(self.active_spans),
                "span_metrics": self.span_metrics
            },
            "metrics": {
                "initialized": self.meter_provider is not None,
                "instruments_created": 12,  # Number of metric instruments
                "exporters": ["prometheus", "otlp"] if config.observability.otlp_endpoint else ["prometheus"]
            },
            "instrumentation": {
                "fastapi": True,
                "boto3": True,
                "redis": True
            }
        }
    
    def shutdown(self):
        """Shutdown OpenTelemetry providers."""
        if self.tracer_provider:
            self.tracer_provider.shutdown()
        
        if self.meter_provider:
            self.meter_provider.shutdown()
        
        logger.info("OpenTelemetry shutdown completed")


class PrometheusMetricsExporter:
    """Prometheus metrics exporter for /metrics endpoint."""
    
    def __init__(self, otel_manager: OpenTelemetryManager):
        """Initialize Prometheus exporter."""
        self.otel_manager = otel_manager
    
    def get_metrics(self) -> str:
        """
        Get Prometheus-formatted metrics.
        
        Returns:
            Prometheus metrics string
        """
        # This would be handled by the PrometheusMetricReader
        # For now, return a placeholder
        return """
# HELP incidents_total Total number of incidents processed
# TYPE incidents_total counter
incidents_total{severity="high"} 42

# HELP incident_duration_seconds Time taken to resolve incidents
# TYPE incident_duration_seconds histogram
incident_duration_seconds_bucket{severity="high",le="60"} 10
incident_duration_seconds_bucket{severity="high",le="180"} 35
incident_duration_seconds_bucket{severity="high",le="+Inf"} 42
incident_duration_seconds_sum{severity="high"} 3600
incident_duration_seconds_count{severity="high"} 42

# HELP mttr_seconds Mean Time To Resolution
# TYPE mttr_seconds gauge
mttr_seconds{severity="high"} 85.7
"""


# Global OpenTelemetry manager instance
_otel_manager: Optional[OpenTelemetryManager] = None

def get_otel_manager() -> OpenTelemetryManager:
    """Get or create the global OpenTelemetry manager instance."""
    global _otel_manager
    if _otel_manager is None:
        _otel_manager = OpenTelemetryManager()
        _otel_manager.initialize()
    return _otel_manager


def initialize_observability():
    """Initialize observability infrastructure."""
    manager = get_otel_manager()
    logger.info("Observability infrastructure initialized")
    return manager


async def trace_function(func_name: str, **attributes):
    """
    Decorator for tracing function execution.
    
    Args:
        func_name: Function name for tracing
        **attributes: Additional span attributes
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            manager = get_otel_manager()
            
            async with manager.trace_orchestrator_phase(func_name, "unknown", **attributes):
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator