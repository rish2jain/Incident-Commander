"""
Model Routing API Router

FastAPI routes for model routing configuration, cost analysis, and optimization reporting.
Provides endpoints for intelligent model selection and cost management.

Requirements: 8.1, 8.2, 8.3, 8.4
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from src.services.model_router import get_model_router, RoutingRequest, RoutingStrategy, ModelTier
from src.services.model_cost_optimizer import get_cost_optimizer
from src.utils.logging import get_logger


logger = get_logger(__name__)

router = APIRouter(prefix="/model-routing", tags=["Model Routing"])


# Request/Response Models
class ModelRoutingRequest(BaseModel):
    """Request model for model routing."""
    task_type: str = Field(..., description="Type of task (detection, diagnosis, etc.)")
    incident_severity: str = Field(default="medium", description="Incident severity level")
    required_accuracy: float = Field(default=0.85, ge=0.0, le=1.0, description="Required accuracy score")
    max_latency_ms: Optional[int] = Field(default=None, description="Maximum acceptable latency in milliseconds")
    max_cost_per_1k_tokens: Optional[float] = Field(default=None, description="Maximum cost per 1k tokens")
    strategy: RoutingStrategy = Field(default=RoutingStrategy.BALANCED, description="Routing strategy")
    context_length: int = Field(default=1000, description="Expected context length in tokens")


class ModelRoutingResponse(BaseModel):
    """Response model for model routing."""
    selected_model: str
    model_id: str
    routing_reason: str
    estimated_cost: float
    estimated_latency_ms: int
    confidence_score: float
    fallback_models: List[str]
    tier: str
    accuracy_score: float


class ModelConfigUpdateRequest(BaseModel):
    """Request model for updating model configuration."""
    cost_per_1k_tokens: Optional[float] = Field(default=None, description="Cost per 1k tokens")
    accuracy_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Accuracy score")
    avg_response_time_ms: Optional[int] = Field(default=None, description="Average response time in ms")
    availability_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Availability score")


class CostBudgetRequest(BaseModel):
    """Request model for setting cost budget."""
    daily_limit: float = Field(..., gt=0, description="Daily cost limit in USD")
    weekly_limit: float = Field(..., gt=0, description="Weekly cost limit in USD")
    monthly_limit: float = Field(..., gt=0, description="Monthly cost limit in USD")


class UsageRecordRequest(BaseModel):
    """Request model for recording model usage."""
    model_name: str = Field(..., description="Name of the model used")
    task_type: str = Field(..., description="Type of task performed")
    tokens_used: int = Field(..., gt=0, description="Number of tokens used")
    actual_cost: float = Field(..., ge=0, description="Actual cost incurred")
    success: bool = Field(default=True, description="Whether the request was successful")
    actual_latency_ms: int = Field(..., gt=0, description="Actual latency in milliseconds")


class OptimizationApplicationRequest(BaseModel):
    """Request model for applying optimization."""
    optimization_index: int = Field(..., description="Index of optimization to apply")


# API Endpoints
@router.post("/route", response_model=ModelRoutingResponse)
async def route_model_request(
    request: ModelRoutingRequest,
    router_service = Depends(get_model_router)
) -> ModelRoutingResponse:
    """
    Route a request to the optimal model based on requirements.
    
    Returns the selected model with routing metadata and cost estimates.
    """
    try:
        # Convert request to internal format
        routing_request = RoutingRequest(
            task_type=request.task_type,
            incident_severity=request.incident_severity,
            required_accuracy=request.required_accuracy,
            max_latency_ms=request.max_latency_ms,
            max_cost_per_1k_tokens=request.max_cost_per_1k_tokens,
            strategy=request.strategy,
            context_length=request.context_length
        )
        
        # Get routing result
        result = await router_service.route_request(routing_request)
        
        # Convert to response format
        return ModelRoutingResponse(
            selected_model=result.selected_model,
            model_id=result.model_config.model_id,
            routing_reason=result.routing_reason,
            estimated_cost=result.estimated_cost,
            estimated_latency_ms=result.estimated_latency_ms,
            confidence_score=result.confidence_score,
            fallback_models=result.fallback_models,
            tier=result.model_config.tier.value,
            accuracy_score=result.model_config.accuracy_score
        )
        
    except Exception as e:
        logger.error(f"Model routing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Model routing failed: {str(e)}")


@router.get("/models")
async def get_available_models(
    router_service = Depends(get_model_router)
) -> Dict[str, Any]:
    """
    Get information about available models and their configurations.
    """
    try:
        models_info = {}
        
        for model_name, config in router_service.model_configs.items():
            models_info[model_name] = {
                "model_id": config.model_id,
                "cost_per_1k_tokens": config.cost_per_1k_tokens,
                "accuracy_score": config.accuracy_score,
                "avg_response_time_ms": config.avg_response_time_ms,
                "max_tokens": config.max_tokens,
                "tier": config.tier.value,
                "availability_score": config.availability_score,
                "last_health_check": config.last_health_check.isoformat() if config.last_health_check else None
            }
        
        return {
            "models": models_info,
            "total_models": len(models_info)
        }
        
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


@router.put("/models/{model_name}/config")
async def update_model_config(
    model_name: str,
    request: ModelConfigUpdateRequest,
    router_service = Depends(get_model_router)
) -> Dict[str, Any]:
    """
    Update configuration for a specific model.
    """
    try:
        # Prepare updates dictionary
        updates = {}
        if request.cost_per_1k_tokens is not None:
            updates["cost_per_1k_tokens"] = request.cost_per_1k_tokens
        if request.accuracy_score is not None:
            updates["accuracy_score"] = request.accuracy_score
        if request.avg_response_time_ms is not None:
            updates["avg_response_time_ms"] = request.avg_response_time_ms
        if request.availability_score is not None:
            updates["availability_score"] = request.availability_score
        
        if not updates:
            raise HTTPException(status_code=400, detail="No updates provided")
        
        # Apply updates
        await router_service.update_model_config(model_name, updates)
        
        return {
            "success": True,
            "model_name": model_name,
            "updates_applied": updates,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update model config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update model config: {str(e)}")


@router.get("/metrics")
async def get_routing_metrics(
    router_service = Depends(get_model_router)
) -> Dict[str, Any]:
    """
    Get model routing metrics and performance statistics.
    """
    try:
        # Get model metrics
        model_metrics = await router_service.get_model_metrics()
        
        # Get routing statistics
        routing_stats = await router_service.get_routing_statistics()
        
        # Format model metrics
        formatted_metrics = {}
        for model_name, metrics in model_metrics.items():
            formatted_metrics[model_name] = {
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": metrics.successful_requests / metrics.total_requests if metrics.total_requests > 0 else 0,
                "avg_response_time_ms": metrics.avg_response_time_ms,
                "total_cost": metrics.total_cost,
                "total_tokens": metrics.total_tokens,
                "avg_cost_per_token": metrics.total_cost / metrics.total_tokens if metrics.total_tokens > 0 else 0,
                "last_used": metrics.last_used.isoformat() if metrics.last_used else None,
                "error_rate": metrics.error_rate
            }
        
        return {
            "model_metrics": formatted_metrics,
            "routing_statistics": routing_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get routing metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get routing metrics: {str(e)}")


@router.post("/usage/record")
async def record_model_usage(
    request: UsageRecordRequest,
    router_service = Depends(get_model_router),
    cost_optimizer = Depends(get_cost_optimizer)
) -> Dict[str, Any]:
    """
    Record actual model usage for metrics and cost tracking.
    """
    try:
        # Record completion in router service
        await router_service.record_request_completion(
            model_name=request.model_name,
            success=request.success,
            actual_latency_ms=request.actual_latency_ms,
            actual_cost=request.actual_cost,
            tokens_used=request.tokens_used
        )
        
        # Record usage in cost optimizer
        await cost_optimizer.record_model_usage(
            model_name=request.model_name,
            task_type=request.task_type,
            tokens_used=request.tokens_used,
            actual_cost=request.actual_cost
        )
        
        return {
            "success": True,
            "message": "Usage recorded successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to record usage: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to record usage: {str(e)}")


@router.get("/cost/analysis")
async def get_cost_analysis(
    cost_optimizer = Depends(get_cost_optimizer)
) -> Dict[str, Any]:
    """
    Get comprehensive cost analysis and optimization recommendations.
    """
    try:
        # Get cost report
        cost_report = await cost_optimizer.get_cost_report()
        
        return {
            "cost_analysis": cost_report,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cost analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cost analysis: {str(e)}")


@router.post("/cost/budget")
async def set_cost_budget(
    request: CostBudgetRequest,
    cost_optimizer = Depends(get_cost_optimizer)
) -> Dict[str, Any]:
    """
    Set cost budget limits for monitoring and alerting.
    """
    try:
        await cost_optimizer.set_budget(
            daily_limit=request.daily_limit,
            weekly_limit=request.weekly_limit,
            monthly_limit=request.monthly_limit
        )
        
        return {
            "success": True,
            "budget": {
                "daily_limit": request.daily_limit,
                "weekly_limit": request.weekly_limit,
                "monthly_limit": request.monthly_limit
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to set budget: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set budget: {str(e)}")


@router.get("/cost/optimizations")
async def get_cost_optimizations(
    cost_optimizer = Depends(get_cost_optimizer)
) -> Dict[str, Any]:
    """
    Get cost optimization recommendations.
    """
    try:
        optimizations = await cost_optimizer.generate_optimizations()
        
        formatted_optimizations = []
        for i, opt in enumerate(optimizations):
            formatted_optimizations.append({
                "index": i,
                "type": opt.optimization_type.value,
                "current_model": opt.current_model,
                "recommended_model": opt.recommended_model,
                "task_type": opt.task_type,
                "potential_savings": opt.potential_savings,
                "confidence_score": opt.confidence_score,
                "impact_assessment": opt.impact_assessment,
                "implementation_effort": opt.implementation_effort,
                "auto_applicable": opt.auto_applicable
            })
        
        return {
            "optimizations": formatted_optimizations,
            "total_optimizations": len(formatted_optimizations),
            "total_potential_savings": sum(opt.potential_savings for opt in optimizations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get optimizations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimizations: {str(e)}")


@router.post("/cost/optimizations/apply")
async def apply_cost_optimization(
    request: OptimizationApplicationRequest,
    cost_optimizer = Depends(get_cost_optimizer)
) -> Dict[str, Any]:
    """
    Apply a specific cost optimization recommendation.
    """
    try:
        # Get current optimizations
        optimizations = await cost_optimizer.generate_optimizations()
        
        if request.optimization_index >= len(optimizations):
            raise HTTPException(status_code=400, detail="Invalid optimization index")
        
        optimization = optimizations[request.optimization_index]
        
        # Apply optimization
        result = await cost_optimizer.apply_optimization(optimization)
        
        return {
            "application_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to apply optimization: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply optimization: {str(e)}")


@router.get("/cost/forecast")
async def get_cost_forecast(
    days: int = Query(default=30, ge=1, le=90, description="Number of days to forecast"),
    cost_optimizer = Depends(get_cost_optimizer)
) -> Dict[str, Any]:
    """
    Get cost forecast for specified number of days.
    """
    try:
        forecast = await cost_optimizer.generate_cost_forecast(days)
        
        return {
            "forecast": {
                "days": days,
                "daily_forecast": forecast.daily_forecast,
                "weekly_forecast": forecast.weekly_forecast,
                "monthly_forecast": forecast.monthly_forecast,
                "trend_direction": forecast.trend_direction,
                "confidence_interval": forecast.confidence_interval,
                "forecast_accuracy": forecast.forecast_accuracy
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cost forecast: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cost forecast: {str(e)}")


@router.get("/cost/alerts")
async def get_cost_alerts(
    cost_optimizer = Depends(get_cost_optimizer)
) -> Dict[str, Any]:
    """
    Get current cost alerts and budget status.
    """
    try:
        alerts = await cost_optimizer.check_budget_alerts()
        
        formatted_alerts = []
        for alert in alerts:
            formatted_alerts.append({
                "level": alert["level"].value if hasattr(alert["level"], "value") else alert["level"],
                "type": alert["type"],
                "message": alert["message"],
                "usage_percentage": alert.get("usage_percentage"),
                "timestamp": alert["timestamp"].isoformat()
            })
        
        return {
            "alerts": formatted_alerts,
            "alert_count": len(formatted_alerts),
            "has_critical_alerts": any(alert["level"] in ["critical", "emergency"] for alert in alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cost alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cost alerts: {str(e)}")


@router.get("/health")
async def get_model_health(
    router_service = Depends(get_model_router)
) -> Dict[str, Any]:
    """
    Get health status of all models.
    """
    try:
        health_status = {}
        
        for model_name in router_service.model_configs.keys():
            is_healthy = await router_service._is_model_healthy(model_name)
            health_status[model_name] = {
                "healthy": is_healthy,
                "last_check": router_service.model_health_cache.get(model_name, (None, None))[1]
            }
        
        overall_health = all(status["healthy"] for status in health_status.values())
        
        return {
            "overall_health": overall_health,
            "model_health": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get model health: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model health: {str(e)}")


@router.get("/strategies")
async def get_routing_strategies() -> Dict[str, Any]:
    """
    Get available routing strategies and their descriptions.
    """
    strategies = {
        "cost_optimized": {
            "name": "Cost Optimized",
            "description": "Minimize cost while meeting accuracy requirements",
            "use_case": "Non-critical tasks where cost is primary concern"
        },
        "latency_optimized": {
            "name": "Latency Optimized", 
            "description": "Minimize response time for fastest results",
            "use_case": "Real-time applications requiring immediate responses"
        },
        "accuracy_optimized": {
            "name": "Accuracy Optimized",
            "description": "Maximize accuracy regardless of cost",
            "use_case": "Critical decisions requiring highest accuracy"
        },
        "balanced": {
            "name": "Balanced",
            "description": "Balance cost, latency, and accuracy based on incident severity",
            "use_case": "General purpose routing with intelligent trade-offs"
        }
    }
    
    return {
        "strategies": strategies,
        "default_strategy": "balanced"
    }


@router.get("/tiers")
async def get_model_tiers() -> Dict[str, Any]:
    """
    Get available model tiers and their characteristics.
    """
    tiers = {
        "economy": {
            "name": "Economy",
            "description": "Lowest cost, basic capability",
            "typical_models": ["claude-3-haiku"],
            "use_cases": ["Simple tasks", "High-volume processing", "Cost-sensitive operations"]
        },
        "standard": {
            "name": "Standard", 
            "description": "Balanced cost and performance",
            "typical_models": ["claude-3-sonnet"],
            "use_cases": ["General purpose", "Most incident response tasks", "Balanced requirements"]
        },
        "premium": {
            "name": "Premium",
            "description": "High cost, best performance",
            "typical_models": ["claude-3-opus"],
            "use_cases": ["Complex analysis", "Critical incidents", "Maximum accuracy required"]
        }
    }
    
    return {
        "tiers": tiers,
        "tier_count": len(tiers)
    }