import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.filterwarnings(
    "ignore:.*:pydantic.warnings.PydanticDeprecatedSince20"
)


class StubCoordinator:
    """Minimal coordinator stub for API contract tests."""

    def __init__(self):
        self.agents = {
            "primary_detection": {"is_healthy": True, "processing_count": 1},
            "primary_resolution": {"is_healthy": True, "processing_count": 0},
        }
        self.processing_states = {}

    async def health_check(self) -> bool:
        return True

    def get_agent_health_status(self):
        return self.agents

    def get_processing_metrics(self):
        return {
            "total_incidents": 5,
            "successful_incidents": 5,
            "failed_incidents": 0,
            "average_processing_time": 4.2,
            "success_rate": 1.0,
            "active_incidents": 0,
            "registered_agents": len(self.agents),
            "consensus_stats": {"rounds": 3}
        }


class StubHealthMonitor:
    monitoring_interval = timedelta(seconds=30)
    metric_retention_period = timedelta(hours=24)
    is_monitoring = True

    def get_current_health_status(self):
        return {
            "overall_status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_count": 10,
            "active_agents": 2,
            "meta_incidents": 0,
            "performance_summary": {"mttr_seconds": 240},
            "resource_utilization": {"cpu": 0.42}
        }

    async def stop_monitoring(self):
        self.is_monitoring = False


class StubMetaHandler:
    def get_active_meta_incidents(self):
        return []

    def get_meta_incident_statistics(self):
        return {
            "active_meta_incidents": 0,
            "total_resolution_attempts": 0,
            "successful_resolution_attempts": 0,
            "auto_resolution_success_rate": 0,
            "auto_resolution_enabled": True
        }


@pytest.fixture
def client(monkeypatch):
    import src.main as main

    # Replace lifespan with a no-op context manager
    @asynccontextmanager
    async def noop_lifespan(_app):
        yield

    original_lifespan = main.app.router.lifespan_context
    main.app.router.lifespan_context = noop_lifespan

    # Reset global state
    main._background_tasks.clear()
    main.process_start_time = datetime.utcnow() - timedelta(minutes=5)
    main.aws_factory = None
    main.coordinator_instance = StubCoordinator()
    main.health_monitor_instance = StubHealthMonitor()
    main.meta_incident_handler_instance = StubMetaHandler()
    main.byzantine_consensus_instance = object()

    # Patch circuit breaker and rate limiter status providers
    monkeypatch.setattr(
        main.circuit_breaker_manager,
        "get_health_dashboard",
        lambda: {
            "timestamp": datetime.utcnow().isoformat(),
            "total_circuit_breakers": 2,
            "healthy_services": 2,
            "degraded_services": 0,
            "unhealthy_services": 0,
            "services": {}
        }
    )

    monkeypatch.setattr(
        main.bedrock_rate_limiter,
        "get_status",
        lambda: {
            "queue_length": 0,
            "models": {
                "sonnet": {"tokens_available": 1000},
                "haiku": {"tokens_available": 2000}
            }
        }
    )

    monkeypatch.setattr(
        main.external_service_rate_limiter,
        "get_service_status",
        lambda service: {"service": service, "status": "healthy", "queue_length": 0}
    )

    client = TestClient(main.app)
    try:
        yield client
    finally:
        client.close()
        main.app.router.lifespan_context = original_lifespan


def test_health_endpoint_reports_runtime_status(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["environment"] == "development"
    assert data["services"]["message_bus"] == "healthy"
    assert data["services"]["agents"] == "healthy"
    assert data["uptime_seconds"] > 0


def test_system_status_returns_metrics(client):
    response = client.get("/status")
    assert response.status_code == 200
    data = response.json()

    assert data["system"]["background_tasks"] == 0
    assert data["metrics"]["total_incidents"] == 5
    assert data["infrastructure"]["circuit_breakers"]["healthy_services"] == 2
    assert data["infrastructure"]["rate_limiters"]["bedrock"]["queue_length"] == 0
