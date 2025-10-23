"""Tests for distributed architecture scaffolding."""

from src.platform.distributed import EventDefinition, EventRouter, ServiceDescriptor, ServiceRegistry


def test_service_registry_adjacency_map():
    registry = ServiceRegistry()
    registry.register_all(
        [
            ServiceDescriptor(
                name="detection-service",
                version="1.0.0",
                description="",
                owner="sre",
                api_endpoint="/detection",
            ),
            ServiceDescriptor(
                name="diagnosis-service",
                version="1.0.0",
                description="",
                owner="sre",
                api_endpoint="/diagnosis",
                dependencies=["detection-service"],
            ),
        ]
    )

    adjacency = registry.adjacency_map()
    assert adjacency["diagnosis-service"] == ["detection-service"]


def test_event_router_rules():
    router = EventRouter("incident-bus")
    router.add_event(
        EventDefinition(
            name="IncidentDetected",
            source="incident-commander",
            detail_type="DetectionCompleted",
            target_service="diagnosis-service",
            schema_ref="arn:aws:schemas:::schema/incident-detection",
        )
    )
    rules = router.to_eventbridge_rules()
    assert rules[0]["EventBusName"] == "incident-bus"
    assert rules[0]["Targets"][0]["Id"] == "target-diagnosis-service"

