"""
Showcase API router for unified system capability demonstration.

Provides comprehensive endpoints for demonstrating all system capabilities
including Amazon Q, Nova Act, Strands, business impact, and performance metrics.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from src.utils.logging import get_logger
from src.api.dependencies import get_services
from src.api.middleware.auth import verify_demo_access, verify_api_key
from src.services.container import ServiceContainer

logger = get_logger("showcase_router")

router = APIRouter(
    prefix="/showcase",
    tags=["showcase"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)


@router.get("/full-demo")
async def full_showcase_endpoint(
    incident_id: Optional[str] = None,
    services: ServiceContainer = Depends(get_services),
    authenticated: bool = Depends(verify_demo_access)
):
    """
    Unified showcase endpoint that demonstrates all system capabilities.
    
    Aggregates Amazon Q, Nova Act, Strands, business impact, and all other capabilities
    into a single comprehensive demonstration response.
    """
    try:
        from src.services.showcase_controller import get_showcase_controller
        from src.models.showcase import serialize_showcase_response
        
        showcase_controller = get_showcase_controller()
        
        # Generate comprehensive showcase
        if incident_id:
            showcase_response = await showcase_controller.generate_full_showcase(incident_id)
        else:
            # Create demo incident for showcase
            demo_incident_data = {
                "title": "Comprehensive System Capability Demonstration",
                "description": "Multi-agent autonomous incident resolution showcase with all integrations",
                "severity": "high",
                "service_tier": "tier_1",
                "affected_users": 25000,
                "revenue_impact_per_minute": 1500.0,
                "tags": {"demo": "true", "showcase": "comprehensive", "complexity": "high"}
            }
            
            showcase_response = await showcase_controller.generate_demo_showcase(demo_incident_data)
        
        # Serialize response for API
        serialized_response = serialize_showcase_response(showcase_response)
        
        return {
            "showcase_response": serialized_response,
            "integration_status": "operational",
            "capabilities_demonstrated": [
                "Multi-agent coordination",
                "Amazon Q intelligent analysis", 
                "Nova Act action planning",
                "Strands SDK orchestration",
                "Business impact calculation",
                "Predictive prevention",
                "Real-time monitoring",
                "Automated documentation"
            ],
            "performance_metrics": {
                "response_time_seconds": showcase_response.execution_time,
                "agents_coordinated": len(showcase_response.agent_responses),
                "integrations_active": len([svc for svc in showcase_response.integration_status.values() if svc.get("operational", False)]),
                "business_value_demonstrated": f"${showcase_response.business_impact.cost_savings:,.2f} savings"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate full showcase: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integration-status")
async def get_integration_status(
    services: ServiceContainer = Depends(get_services),
    authenticated: bool = Depends(verify_api_key)
):
    """
    Get comprehensive integration status for all system components.
    
    Validates all AWS service integrations and system health.
    """
    try:
        from src.services.showcase_controller import get_showcase_controller
        
        showcase_controller = get_showcase_controller()
        integration_status = await showcase_controller.get_integration_status()
        
        return {
            "integration_status": integration_status,
            "system_health": {
                "overall_status": "operational" if integration_status.overall_health > 0.8 else "degraded",
                "health_score": f"{integration_status.overall_health:.1%}",
                "operational_services": len([svc for svc in integration_status.service_status.values() if svc.is_operational]),
                "total_services": len(integration_status.service_status)
            },
            "service_details": {
                service_name: {
                    "operational": status.is_operational,
                    "response_time_ms": status.response_time * 1000,
                    "error_rate": f"{status.error_rate:.1%}",
                    "last_check": status.last_health_check.isoformat()
                }
                for service_name, status in integration_status.service_status.items()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get integration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demo-scenario")
async def execute_demo_scenario(
    scenario_data: Dict[str, Any],
    services: ServiceContainer = Depends(get_services)
):
    """
    Execute a predefined demo scenario with controlled outcomes.
    
    Provides deterministic demo execution for consistent presentation.
    """
    try:
        from src.services.showcase_controller import get_showcase_controller
        from src.models.showcase import DemoScenario
        
        showcase_controller = get_showcase_controller()
        
        # Create demo scenario
        scenario = DemoScenario(
            scenario_type=scenario_data["scenario_type"],
            title=scenario_data["title"],
            description=scenario_data["description"],
            severity=scenario_data.get("severity", "high"),
            expected_duration_minutes=scenario_data.get("expected_duration_minutes", 3),
            custom_parameters=scenario_data.get("custom_parameters", {})
        )
        
        # Execute scenario
        demo_result = await showcase_controller.execute_demo_scenario(scenario)
        
        return {
            "demo_execution": {
                "scenario_id": demo_result.scenario_id,
                "incident_id": demo_result.incident_id,
                "execution_status": demo_result.status,
                "estimated_completion": demo_result.estimated_completion_time.isoformat(),
                "controlled_execution": demo_result.controlled_execution,
                "performance_guarantee": f"{demo_result.completion_guarantee_minutes} minutes"
            },
            "real_time_features": {
                "mttr_tracking": True,
                "cost_accumulation": True,
                "agent_coordination": True,
                "business_impact": True
            },
            "monitoring_endpoints": {
                "real_time_status": f"/showcase/demo-status/{demo_result.scenario_id}",
                "performance_metrics": f"/showcase/demo-metrics/{demo_result.scenario_id}"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to execute demo scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demo-status/{scenario_id}")
async def get_demo_status(
    scenario_id: str,
    services: ServiceContainer = Depends(get_services)
):
    """
    Get real-time status of executing demo scenario.
    
    Provides live updates on demo progress and metrics.
    """
    try:
        from src.services.showcase_controller import get_showcase_controller
        
        showcase_controller = get_showcase_controller()
        demo_status = showcase_controller.get_demo_status(scenario_id)
        
        if not demo_status:
            raise HTTPException(status_code=404, detail="Demo scenario not found")
        
        return {
            "demo_status": demo_status,
            "real_time_metrics": {
                "current_phase": demo_status.current_phase,
                "elapsed_time_seconds": demo_status.elapsed_time_seconds,
                "completion_percentage": demo_status.completion_percentage,
                "cost_accumulated": f"${demo_status.cost_accumulated:,.2f}",
                "agents_active": len(demo_status.active_agents)
            },
            "performance_tracking": {
                "mttr_progress": f"{demo_status.mttr_seconds} seconds",
                "sla_compliance": demo_status.sla_compliance,
                "business_impact": f"${demo_status.business_impact_prevented:,.2f} impact prevented"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get demo status for {scenario_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def list_system_capabilities(services: ServiceContainer = Depends(get_services)):
    """
    List all system capabilities available for demonstration.
    
    Provides comprehensive overview of system features and integrations.
    """
    try:
        from src.services.showcase_controller import get_showcase_controller
        
        showcase_controller = get_showcase_controller()
        capabilities = await showcase_controller.get_system_capabilities()
        
        return {
            "system_capabilities": capabilities,
            "capability_categories": {
                "core_agents": [
                    "Detection Agent - Anomaly detection and monitoring",
                    "Diagnosis Agent - Root cause analysis",
                    "Prediction Agent - Predictive prevention",
                    "Resolution Agent - Automated remediation",
                    "Communication Agent - Stakeholder notifications"
                ],
                "ai_integrations": [
                    "Amazon Q - Intelligent analysis and documentation",
                    "Nova Act - Advanced action planning",
                    "Titan Embeddings - Semantic search and RAG"
                ],
                "orchestration": [
                    "Strands SDK - Agent fabric and coordination",
                    "Byzantine Consensus - Fault-tolerant decision making",
                    "Circuit Breakers - Resilience and fault tolerance"
                ],
                "business_intelligence": [
                    "Business Impact Calculator - ROI and cost analysis",
                    "Performance Optimizer - Resource optimization",
                    "Cost Optimizer - Intelligent cost management"
                ],
                "monitoring_observability": [
                    "Real-time Monitoring - System health and metrics",
                    "3D Visualization - Interactive system visualization",
                    "Chaos Engineering - Resilience testing"
                ]
            },
            "integration_readiness": {
                "production_ready": capabilities.production_ready_count,
                "development_mode": capabilities.development_mode_count,
                "total_capabilities": capabilities.total_capabilities
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list system capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-summary")
async def get_performance_summary(services: ServiceContainer = Depends(get_services)):
    """
    Get comprehensive system performance summary.
    
    Aggregates performance metrics across all system components.
    """
    try:
        from src.services.showcase_controller import get_showcase_controller
        
        showcase_controller = get_showcase_controller()
        performance_summary = await showcase_controller.get_performance_summary()
        
        return {
            "performance_summary": performance_summary,
            "key_metrics": {
                "average_mttr_seconds": performance_summary.average_mttr_seconds,
                "success_rate": f"{performance_summary.success_rate:.1%}",
                "cost_savings_per_incident": f"${performance_summary.average_cost_savings:,.2f}",
                "system_availability": f"{performance_summary.system_availability:.2%}"
            },
            "performance_trends": {
                "mttr_trend": performance_summary.mttr_trend,
                "success_rate_trend": performance_summary.success_rate_trend,
                "cost_efficiency_trend": performance_summary.cost_efficiency_trend
            },
            "benchmark_comparison": {
                "industry_average_mttr": "30+ minutes",
                "our_average_mttr": f"{performance_summary.average_mttr_seconds / 60:.1f} minutes",
                "improvement_factor": f"{(30 * 60) / performance_summary.average_mttr_seconds:.1f}x faster",
                "cost_advantage": f"{performance_summary.cost_advantage_percentage:.1f}% cost reduction"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))