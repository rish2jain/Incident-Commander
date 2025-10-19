"""Tests for operator control panel functionality."""

from types import SimpleNamespace

from src.services.operator_controls import OperatorControlService


def test_operator_settings_defaults():
    service = OperatorControlService()
    settings = service.get_settings()
    assert settings["autonomy_mode"] == "advisory"
    assert settings["global_dry_run"] is False


def test_operator_evaluation_respects_threshold_override():
    service = OperatorControlService()
    decision = SimpleNamespace(final_confidence=0.55, selected_action="scale_up")

    evaluation = service.evaluate_decision("inc-1", decision)
    assert evaluation["requires_manual"] is True

    service.set_autonomy_mode("execute", confidence_threshold=0.5)
    evaluation = service.evaluate_decision("inc-1", decision)
    assert evaluation["requires_manual"] is False


def test_operator_dry_run_controls():
    service = OperatorControlService()
    decision = SimpleNamespace(final_confidence=0.9, selected_action="restart")

    service.set_incident_dry_run("inc-2", True)
    assert service.is_dry_run("inc-2") is True
    assert service.can_execute_actions("inc-2", decision) is False

    service.set_incident_dry_run("inc-2", False)
    assert service.is_dry_run("inc-2") is False


def test_operator_scenario_builder_returns_template():
    service = OperatorControlService()
    scenario = service.build_scenario("api_throttle", {"severity": "medium"})

    assert scenario["scenario_name"] == "api_throttle"
    assert scenario["severity"] == "medium"
    assert "generated_at" in scenario
