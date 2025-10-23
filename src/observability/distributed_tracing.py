"""
Distributed tracing with OpenTelemetry and AWS X-Ray.

Provides comprehensive distributed tracing across all agents and services
for debugging, performance analysis, and incident investigation.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Dict, Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aws_lambda import AwsLambdaInstrumentor
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

from src.utils.logging import get_logger


logger = get_logger("observability.tracing")


class DistributedTracer:
    """
    Distributed tracing manager using OpenTelemetry.

    Features:
    - Automatic instrumentation for AWS services
    - Custom span creation and management
    - Trace context propagation
    - Integration with AWS X-Ray
    - Performance metrics collection
    """

    def __init__(
        self,
        service_name: str = "incident-commander",
        service_version: str = "2.0.0",
        environment: str = "production",
        enable_auto_instrumentation: bool = True,
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment

        # Configure resource
        resource = Resource.create(
            {
                "service.name": service_name,
                "service.version": service_version,
                "deployment.environment": environment,
            }
        )

        # Set up tracer provider
        provider = TracerProvider(resource=resource)

        # Add OTLP exporter (can be configured to send to X-Ray, Jaeger, etc.)
        otlp_exporter = OTLPSpanExporter(
            # endpoint="http://localhost:4317",  # Configure as needed
            insecure=True,
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

        # Set global tracer provider
        trace.set_tracer_provider(provider)

        # Get tracer
        self.tracer = trace.get_tracer(__name__)

        # Auto-instrumentation
        if enable_auto_instrumentation:
            self._setup_auto_instrumentation()

        logger.info(
            f"Distributed tracing initialized",
            extra={
                "service": service_name,
                "version": service_version,
                "environment": environment,
            },
        )

    def _setup_auto_instrumentation(self) -> None:
        """Set up automatic instrumentation for common libraries."""
        try:
            # Instrument boto3/botocore for AWS SDK calls
            BotocoreInstrumentor().instrument()

            # Instrument requests library
            RequestsInstrumentor().instrument()

            # Instrument AWS Lambda (if running in Lambda)
            try:
                AwsLambdaInstrumentor().instrument()
            except Exception:
                pass  # Not running in Lambda

            logger.info("Auto-instrumentation enabled")

        except Exception as e:
            logger.warning(f"Failed to set up auto-instrumentation: {e}")

    @contextmanager
    def span(
        self,
        name: str,
        *,
        attributes: Optional[Dict[str, Any]] = None,
        parent: Optional[trace.Span] = None,
    ):
        """
        Create a synchronous span context manager.

        Args:
            name: Span name
            attributes: Optional span attributes
            parent: Optional parent span

        Yields:
            The created span
        """
        with self.tracer.start_as_current_span(
            name,
            context=trace.set_span_in_context(parent) if parent else None,
        ) as span:
            if attributes:
                span.set_attributes(attributes)

            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    @asynccontextmanager
    async def async_span(
        self,
        name: str,
        *,
        attributes: Optional[Dict[str, Any]] = None,
        parent: Optional[trace.Span] = None,
    ):
        """
        Create an asynchronous span context manager.

        Args:
            name: Span name
            attributes: Optional span attributes
            parent: Optional parent span

        Yields:
            The created span
        """
        with self.tracer.start_as_current_span(
            name,
            context=trace.set_span_in_context(parent) if parent else None,
        ) as span:
            if attributes:
                span.set_attributes(attributes)

            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def trace_incident_processing(self, incident_id: str):
        """Create a span for incident processing."""
        return self.span(
            "process_incident",
            attributes={
                "incident.id": incident_id,
                "component": "orchestrator",
            },
        )

    def trace_agent_execution(self, agent_name: str, incident_id: str):
        """Create a span for agent execution."""
        return self.span(
            f"agent.{agent_name}",
            attributes={
                "agent.name": agent_name,
                "incident.id": incident_id,
                "component": "agent",
            },
        )

    def trace_consensus(
        self, proposal_id: str, method: str, participating_agents: int
    ):
        """Create a span for consensus execution."""
        return self.span(
            "consensus.reach_consensus",
            attributes={
                "consensus.proposal_id": proposal_id,
                "consensus.method": method,
                "consensus.participating_agents": participating_agents,
                "component": "consensus",
            },
        )

    def trace_aws_service_call(self, service_name: str, operation: str):
        """Create a span for AWS service calls."""
        return self.span(
            f"aws.{service_name}.{operation}",
            attributes={
                "aws.service": service_name,
                "aws.operation": operation,
                "component": "aws",
            },
        )

    def get_current_span(self) -> Optional[trace.Span]:
        """Get the current active span."""
        return trace.get_current_span()

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the current span."""
        span = self.get_current_span()
        if span:
            span.add_event(name, attributes=attributes or {})


# Global tracer instance
_tracer: Optional[DistributedTracer] = None


def get_tracer(
    service_name: str = "incident-commander",
    service_version: str = "2.0.0",
    environment: str = "production",
) -> DistributedTracer:
    """Get the global distributed tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = DistributedTracer(
            service_name=service_name,
            service_version=service_version,
            environment=environment,
        )
    return _tracer
