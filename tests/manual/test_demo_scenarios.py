"""Scenario coverage checks for hackathon demo flows."""

from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.services.demo_controller import DemoController, DemoScenarioType


pytestmark = pytest.mark.manual


@pytest.fixture(scope="module")
def demo_controller() -> DemoController:
    return DemoController()


def _validate_config(config: Dict[str, Any]) -> None:
    required_keys = {
        "title",
        "description",
        "severity",
        "service_tier",
        "affected_users",
        "revenue_impact_per_minute",
        "estimated_phases",
        "sla_target_minutes",
        "traditional_mttr_minutes",
    }

    missing = required_keys.difference(config.keys())
    assert not missing, f"Scenario config missing keys: {missing}"

    phases = config["estimated_phases"]
    assert set(phases.keys()) >= {"detecting", "diagnosing", "predicting", "resolving", "communicating"}
    assert all(phase_value > 0 for phase_value in phases.values())


def test_demo_controller_includes_all_scenarios(demo_controller: DemoController) -> None:
    configs = demo_controller.scenario_configs

    expected = set(DemoScenarioType)
    assert expected.issubset(configs.keys())

    for scenario_type in expected:
        config = configs[scenario_type]
        _validate_config(config)


def test_demo_scenarios_endpoint_lists_every_scenario() -> None:
    client = TestClient(app)

    response = client.get("/demo/scenarios")
    assert response.status_code == 200

    payload = response.json()
    available = payload["available_scenarios"]
    expected = {scenario.value for scenario in DemoScenarioType}
    assert expected.issubset(available.keys())

    for name, details in available.items():
        assert details["name"], f"Scenario {name} missing display name"
        assert details["description"], f"Scenario {name} missing description"
        assert "business_impact" in details
        assert "estimated_duration" in details


def test_run_scenarios_endpoint_metadata(monkeypatch) -> None:
    client = TestClient(app)

    async def fake_trigger_incident(incident_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "incident_id": "test-incident",
            "status": "processing",
            "estimated_completion_minutes": 3,
            "cost_per_minute": incident_data.get("revenue_impact_per_minute", 0.0),
        }

    monkeypatch.setattr("src.main.trigger_incident", fake_trigger_incident)

    for scenario in DemoScenarioType:
        response = client.post(f"/demo/scenarios/{scenario.value}")
        assert response.status_code == 200

        payload = response.json()
        assert payload["scenario"] == scenario.value
        assert payload["status"] == "started"
        assert "incident_id" in payload
        assert payload["demo_features"]["agent_coordination"] is True
