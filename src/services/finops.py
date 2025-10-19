"""FinOps visibility, guardrails, and optimization support."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional

from src.services.cost_optimizer import get_cost_optimizer, CostMetrics


@dataclass
class BudgetGuardrail:
    """Budget constraints for a tenant or capability grouping."""

    tenant: str
    daily_limit: float
    weekly_limit: float
    capabilities: List[str] = field(default_factory=list)
    current_daily_spend: float = 0.0
    current_weekly_projection: float = 0.0
    status: str = "unknown"
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    last_evaluated: Optional[datetime] = None

    def evaluate(self, metrics: CostMetrics) -> None:
        """Update spend and status using cost metrics."""
        relevant_daily = self._calculate_relevant_cost(metrics.cost_by_service)
        
        # Calculate capability share for projected weekly cost
        total_daily = getattr(metrics.cost_by_service, 'total', None) or sum(
            getattr(metrics.cost_by_service, attr, 0) 
            for attr in dir(metrics.cost_by_service) 
            if not attr.startswith('_') and isinstance(getattr(metrics.cost_by_service, attr), (int, float))
        )
        
        if total_daily > 0:
            share = relevant_daily / total_daily
        else:
            share = 0
            
        projected_weekly = metrics.projected_daily_cost * 7 * share
        self.current_daily_spend = relevant_daily
        self.current_weekly_projection = projected_weekly
        self.last_evaluated = datetime.utcnow()

        self.alerts.clear()
        daily_ratio = relevant_daily / self.daily_limit if self.daily_limit else 0.0
        weekly_ratio = projected_weekly / self.weekly_limit if self.weekly_limit else 0.0

        severity = max(daily_ratio, weekly_ratio)
        if severity >= 1.05:
            self.status = "breached"
            self.alerts.append({
                "level": "critical",
                "message": f"{self.tenant} exceeded budget by {(severity - 1) * 100:.1f}%"
            })
        elif severity >= 0.9:
            self.status = "approaching"
            self.alerts.append({
                "level": "warning",
                "message": f"{self.tenant} within 10% of budget limits"
            })
        else:
            self.status = "within"

    def _calculate_relevant_cost(self, cost_by_service: Dict[str, float]) -> float:
        if not self.capabilities:
            return sum(cost_by_service.values())
        return sum(cost_by_service.get(capability, 0.0) for capability in self.capabilities)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant": self.tenant,
            "daily_limit": self.daily_limit,
            "weekly_limit": self.weekly_limit,
            "capabilities": self.capabilities,
            "current_daily_spend": self.current_daily_spend,
            "current_weekly_projection": self.current_weekly_projection,
            "status": self.status,
            "alerts": self.alerts,
            "last_evaluated": self.last_evaluated.isoformat() if self.last_evaluated else None,
        }


class FinOpsService:
    """Coordinates FinOps dashboards, guardrails, and recommendations."""

    def __init__(self) -> None:
        self._budgets: Dict[str, BudgetGuardrail] = {
            "platform": BudgetGuardrail(
                tenant="platform",
                daily_limit=5000.0,
                weekly_limit=30000.0,
                capabilities=["orchestrator", "infrastructure"],
            ),
            "ml-ops": BudgetGuardrail(
                tenant="ml-ops",
                daily_limit=3500.0,
                weekly_limit=20000.0,
                capabilities=["prediction", "diagnosis", "ai_models"],
            ),
            "communications": BudgetGuardrail(
                tenant="communications",
                daily_limit=1500.0,
                weekly_limit=9000.0,
                capabilities=["communication", "status_updates"],
            ),
        }
        self._cost_history: deque = deque(maxlen=24)
        self._last_metrics: Optional[CostMetrics] = None

    async def register_budget(
        self,
        tenant: str,
        daily_limit: float,
        weekly_limit: float,
        capabilities: Optional[List[str]] = None
    ) -> BudgetGuardrail:
        guardrail = BudgetGuardrail(
            tenant=tenant,
            daily_limit=daily_limit,
            weekly_limit=weekly_limit,
            capabilities=capabilities or [],
        )
        self._budgets[tenant] = guardrail
        return guardrail

    async def get_dashboard(self) -> Dict[str, Any]:
        cost_optimizer = await get_cost_optimizer()
        metrics = await cost_optimizer.get_cost_metrics()
        recommendations = await cost_optimizer.get_cost_recommendations()

        self._evaluate_guardrails(metrics)
        trend = self._calculate_trend(metrics.current_hourly_cost)

        dashboard = {
            "timestamp": datetime.utcnow().isoformat(),
            "current_costs": {
                "hourly": metrics.current_hourly_cost,
                "projected_daily": metrics.projected_daily_cost,
                "lambda_warm": metrics.lambda_warm_cost,
                "scaling": metrics.scaling_cost,
            },
            "spend_by_capability": metrics.cost_by_service,
            "spend_by_model": metrics.cost_by_model,
            "guardrails": [guardrail.to_dict() for guardrail in self._budgets.values()],
            "optimization_suggestions": recommendations,
            "cost_savings": metrics.cost_savings_achieved,
            "trend": trend,
        }

        return dashboard

    async def get_guardrails(self) -> List[Dict[str, Any]]:
        metrics = self._last_metrics
        if metrics is None:
            cost_optimizer = await get_cost_optimizer()
            metrics = await cost_optimizer.get_cost_metrics()
            self._evaluate_guardrails(metrics)
        return [guardrail.to_dict() for guardrail in self._budgets.values()]

    def _evaluate_guardrails(self, metrics: CostMetrics) -> None:
        for guardrail in self._budgets.values():
            guardrail.evaluate(metrics)
        self._last_metrics = metrics

    def _calculate_trend(self, current_hourly_cost: float) -> Dict[str, Any]:
        timestamp = datetime.utcnow()
        if self._cost_history:
            last_cost = self._cost_history[-1][1]
            delta = current_hourly_cost - last_cost
        else:
            delta = 0.0
        self._cost_history.append((timestamp, current_hourly_cost))

        direction = "stable"
        if delta > 5:
            direction = "rising"
        elif delta < -5:
            direction = "falling"

        return {
            "direction": direction,
            "delta_per_hour": delta,
            "history": [
                {"timestamp": ts.isoformat(), "hourly_cost": cost}
                for ts, cost in list(self._cost_history)
            ],
        }


_finops_service: Optional[FinOpsService] = None


async def get_finops_service() -> FinOpsService:
    global _finops_service
    if _finops_service is None:
        _finops_service = FinOpsService()
    return _finops_service
