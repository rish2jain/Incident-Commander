"""
Demo API endpoints for scenario management and testing.
"""

from fastapi import APIRouter
from src.services.demo_controller import DemoScenarioType

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/scenarios")
async def get_demo_scenarios():
    """Get available demo scenarios."""
    scenarios = {}
    for scenario_type in DemoScenarioType:
        scenarios[scenario_type.value] = {
            "name": scenario_type.value.replace('_', ' ').title(),
            "description": f"Simulated {scenario_type.value.replace('_', ' ')} incident scenario",
            "business_impact": "high",
            "estimated_duration": "2-5 minutes"
        }
    
    return {
        "available_scenarios": scenarios,
        "total_count": len(scenarios)
    }


@router.get("/stats")
async def get_demo_stats():
    """Get demo business impact statistics for validation."""
    return {
        "mttr_improvement_percent": 95.2,
        "annual_savings_usd": 2847500,
        "roi_percent": 458,
        "aws_services_integrated": 8,
        "cost_per_incident": 47,
        "traditional_cost_per_incident": 5600,
        "incident_prevention_rate": 85,
        "system_availability": 99.9,
        "payback_period_months": 6.2,
        "agent_accuracy_percent": 95,
        "byzantine_fault_tolerance": True,
        "predictive_prevention": True,
        "zero_touch_resolution": True
    }