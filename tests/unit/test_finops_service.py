"""Tests for FinOps dashboard and guardrail logic."""

import pytest

from src.services.finops import FinOpsService
from src.services.cost_optimizer import CostMetrics


class _StubCostOptimizer:
    def __init__(self, metrics: CostMetrics, recommendations):
        self._metrics = metrics
        self._recommendations = recommendations

    async def get_cost_metrics(self) -> CostMetrics:
        return self._metrics

    async def get_cost_recommendations(self):
        return self._recommendations


@pytest.mark.asyncio
async def test_finops_dashboard_reports_guardrail_status(monkeypatch):
    metrics = CostMetrics(
        current_hourly_cost=125.0,
        projected_daily_cost=2600.0,
        cost_by_service={
            "detection": 950.0,
            "prediction": 600.0,
            "communication": 320.0,
        },
        cost_by_model={"claude-3-sonnet": 1400.0},
        cost_savings_achieved=480.0,
        optimization_actions=["Switched detection agent to economy model"],
        lambda_warm_cost=0.08,
        scaling_cost=28.0,
    )
    recommendations = [
        {
            "type": "model",
            "recommendation": "Downgrade advisory bot to haiku tier",
            "potential_savings": 180.0,
        }
    ]

    async def _fake_get_cost_optimizer():
        return _StubCostOptimizer(metrics, recommendations)

    monkeypatch.setattr("src.services.finops.get_cost_optimizer", _fake_get_cost_optimizer)

    service = FinOpsService()
    await service.register_budget(
        tenant="payments",
        daily_limit=1700.0,
        weekly_limit=20000.0,
        capabilities=["detection", "prediction"],
    )

    dashboard = await service.get_dashboard()

    assert dashboard["current_costs"]["hourly"] == pytest.approx(125.0)
    assert dashboard["spend_by_capability"]["detection"] == 950.0
    assert dashboard["optimization_suggestions"] == recommendations

    guardrails = {g["tenant"]: g for g in dashboard["guardrails"]}
    assert "payments" in guardrails
    assert guardrails["payments"]["status"] in {"approaching", "within"}
    assert guardrails["payments"]["current_daily_spend"] == pytest.approx(1550.0)


@pytest.mark.asyncio
async def test_guardrails_endpoint_uses_cached_metrics(monkeypatch):
    metrics = CostMetrics(
        current_hourly_cost=90.0,
        projected_daily_cost=1800.0,
        cost_by_service={"communication": 400.0},
        cost_by_model={},
        cost_savings_achieved=120.0,
        optimization_actions=[],
        lambda_warm_cost=0.04,
        scaling_cost=12.0,
    )

    async def _fake_get_cost_optimizer():
        return _StubCostOptimizer(metrics, [])

    monkeypatch.setattr("src.services.finops.get_cost_optimizer", _fake_get_cost_optimizer)

    service = FinOpsService()
    await service.get_dashboard()  # populate cache & evaluate
    guardrails = await service.get_guardrails()

    assert isinstance(guardrails, list)
    assert all("tenant" in guardrail for guardrail in guardrails)
