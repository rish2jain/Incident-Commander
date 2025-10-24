"""
Monitoring API Router

FastAPI routes for comprehensive monitoring dashboards, metrics, and diagnostic reporting.
Provides endpoints for integration health, guardrail tracking, and agent performance telemetry.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from src.services.integration_monitor import get_integration_monitor, ServiceStatus, IntegrationType
from src.services.guardrail_tracker import get_guardrail_tracker, GuardrailType, GuardrailDecision
from src.services.agent_telemetry import get_agent_telemetry, TelemetryEventType, PerformanceCategory
from src.models.agent import AgentType
from src.utils.logging import get_logger


logger = get_logger("monitoring_api")
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


# Response Models

class ServiceHealthResponse(BaseModel):
    """Response model for service health information."""
    service_name: str
    integration_type: str
    status: str
    response_time_ms: float
    error_rate: float
    availability: float
    last_check: datetime
    error_details: Optional[str] = None
    performance_trend: List[float] = Field(default_factory=list)
    uptime_percentage: float


class IntegrationHealthSummary(BaseModel):
    """Summary of integration health status."""
    timestamp: datetime
    overall_status: str
    healthy_services: int
    degraded_services: int
    unhealthy_services: int
    total_services: int
    system_uptime: float
    performance_summary: Dict[str, Any]


class GuardrailMetricsResponse(BaseModel):
    """Response model for guardrail metrics."""
    guardrail_name: str
    guardrail_type: str
    total_events: int
    allow_count: int
    block_count: int
    warn_count: int
    escalate_count: int
    modify_count: int
    block_rate: float
    escalation_rate: float
    average_processing_time_ms: float


class AgentPerformanceResponse(BaseModel):
    """Response model for agent performance analysis."""
    agent_name: str
    agent_type: str
    analysis_period_hours: int
    total_executions: int
    success_rate: float
    error_rate: float
    average_duration_ms: float
    median_duration_ms: float
    p95_duration_ms: float
    performance_category: str
    performance_trend: str
    efficiency_score: float
    optimization_recommendations: List[str]


class SystemPerformanceResponse(BaseModel):
    """Response model for system-wide performance report."""
    generated_at: datetime
    analysis_period_hours: int
    total_agents: int
    active_agents: int
    total_executions: int
    system_success_rate: float
    consensus_success_rate: float
    escalation_rate: float
    performance_trends: Dict[str, str]
    bottlenecks: List[str]
    system_recommendations: List[str]


# Integration Health Endpoints

@router.get("/health/integrations", response_model=IntegrationHealthSummary)
async def get_integration_health():
    """
    Get comprehensive integration health status.
    
    Returns health status for all AWS service integrations including
    response times, error rates, and availability metrics.
    """
    try:
        monitor = get_integration_monitor()
        
        # Start monitoring if not already active
        if not monitor.monitoring_active:
            await monitor.start_monitoring()
        
        report = await monitor.get_integration_health_report()
        
        return IntegrationHealthSummary(
            timestamp=report.timestamp,
            overall_status=report.overall_status.value,
            healthy_services=report.healthy_services,
            degraded_services=report.degraded_services,
            unhealthy_services=report.unhealthy_services,
            total_services=report.total_services,
            system_uptime=report.system_uptime,
            performance_summary=report.performance_summary
        )
        
    except Exception as e:
        logger.error(f"Failed to get integration health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/integrations/{service_name}", response_model=ServiceHealthResponse)
async def get_service_health(service_name: str):
    """
    Get detailed health information for a specific service.
    
    Args:
        service_name: Name of the service to check (e.g., 'bedrock', 'dynamodb')
    """
    try:
        monitor = get_integration_monitor()
        
        service_health = await monitor.get_service_health(service_name)
        
        if not service_health:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        
        return ServiceHealthResponse(
            service_name=service_health.service_name,
            integration_type=service_health.integration_type.value,
            status=service_health.status.value,
            response_time_ms=service_health.response_time_ms,
            error_rate=service_health.error_rate,
            availability=service_health.availability,
            last_check=service_health.last_check,
            error_details=service_health.error_details,
            performance_trend=service_health.performance_trend,
            uptime_percentage=service_health.uptime_percentage
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service health for {service_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/integrations/unhealthy")
async def get_unhealthy_services():
    """
    Get list of services that are currently unhealthy or degraded.
    
    Returns detailed information about services experiencing issues.
    """
    try:
        monitor = get_integration_monitor()
        
        unhealthy_services = await monitor.get_unhealthy_services()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "unhealthy_count": len(unhealthy_services),
            "services": [
                {
                    "service_name": svc.service_name,
                    "status": svc.status.value,
                    "error_details": svc.error_details,
                    "response_time_ms": svc.response_time_ms,
                    "availability": svc.availability,
                    "last_check": svc.last_check.isoformat()
                }
                for svc in unhealthy_services
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get unhealthy services: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/diagnostics")
async def get_system_diagnostics(service_name: Optional[str] = None):
    """
    Generate diagnostic report for troubleshooting.
    
    Args:
        service_name: Optional specific service to diagnose
    """
    try:
        monitor = get_integration_monitor()
        
        diagnostic_report = await monitor.generate_diagnostic_report(service_name)
        
        return diagnostic_report
        
    except Exception as e:
        logger.error(f"Failed to generate diagnostic report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Guardrail Tracking Endpoints

@router.get("/guardrails/metrics")
async def get_guardrail_metrics(
    guardrail_name: Optional[str] = Query(None, description="Specific guardrail to analyze")
):
    """
    Get guardrail enforcement metrics and statistics.
    
    Args:
        guardrail_name: Optional specific guardrail to analyze
    """
    try:
        tracker = get_guardrail_tracker()
        
        # Start tracking if not already active
        if not tracker.tracking_active:
            await tracker.start_tracking()
        
        metrics = await tracker.get_guardrail_metrics(guardrail_name)
        
        response_metrics = []
        for name, metric in metrics.items():
            response_metrics.append(GuardrailMetricsResponse(
                guardrail_name=metric.guardrail_name,
                guardrail_type=metric.guardrail_type.value,
                total_events=metric.total_events,
                allow_count=metric.allow_count,
                block_count=metric.block_count,
                warn_count=metric.warn_count,
                escalate_count=metric.escalate_count,
                modify_count=metric.modify_count,
                block_rate=metric.calculate_block_rate(),
                escalation_rate=metric.calculate_escalation_rate(),
                average_processing_time_ms=metric.average_processing_time_ms
            ))
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_guardrails": len(response_metrics),
            "metrics": response_metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get guardrail metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardrails/events")
async def get_guardrail_events(
    hours: int = Query(24, description="Hours of history to retrieve", ge=1, le=168),
    guardrail_type: Optional[GuardrailType] = Query(None, description="Filter by guardrail type"),
    decision: Optional[GuardrailDecision] = Query(None, description="Filter by decision type")
):
    """
    Get recent guardrail enforcement events.
    
    Args:
        hours: Number of hours of history to retrieve (1-168)
        guardrail_type: Optional filter by guardrail type
        decision: Optional filter by decision type
    """
    try:
        tracker = get_guardrail_tracker()
        
        events = await tracker.get_recent_events(
            hours=hours,
            guardrail_type=guardrail_type,
            decision=decision
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "total_events": len(events),
            "filters": {
                "guardrail_type": guardrail_type.value if guardrail_type else None,
                "decision": decision.value if decision else None
            },
            "events": [event.to_dict() for event in events[:1000]]  # Limit to 1000 events
        }
        
    except Exception as e:
        logger.error(f"Failed to get guardrail events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardrails/compliance")
async def get_compliance_analytics():
    """
    Get comprehensive compliance analytics and trends.
    
    Returns compliance rates, policy violations, and trend analysis.
    """
    try:
        tracker = get_guardrail_tracker()
        
        analytics = await tracker.get_compliance_analytics()
        
        return analytics
        
    except Exception as e:
        logger.error(f"Failed to get compliance analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/guardrails/compliance/report")
async def generate_compliance_report(
    period_days: int = Query(7, description="Report period in days", ge=1, le=30),
    include_recommendations: bool = Query(True, description="Include optimization recommendations")
):
    """
    Generate comprehensive compliance report.
    
    Args:
        period_days: Report period in days (1-30)
        include_recommendations: Whether to include recommendations
    """
    try:
        tracker = get_guardrail_tracker()
        
        report = await tracker.generate_compliance_report(
            period_days=period_days,
            include_recommendations=include_recommendations
        )
        
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "period": {
                "start": report.period_start.isoformat(),
                "end": report.period_end.isoformat(),
                "days": period_days
            },
            "summary": {
                "total_events": report.total_events,
                "total_violations": report.total_violations,
                "compliance_rate": report.compliance_rate
            },
            "breakdown": {
                "events_by_type": report.events_by_type,
                "violations_by_severity": report.violations_by_severity
            },
            "policy_analysis": {
                "total_policy_violations": len(report.policy_violations),
                "top_violated_policies": report.top_violated_policies,
                "recent_violations": report.policy_violations[:10]  # Last 10 violations
            },
            "recommendations": report.recommendations if include_recommendations else []
        }
        
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Agent Performance Telemetry Endpoints

@router.get("/agents/performance")
async def get_agent_performance(
    agent_name: Optional[str] = Query(None, description="Specific agent to analyze"),
    agent_type: Optional[AgentType] = Query(None, description="Filter by agent type"),
    hours: int = Query(24, description="Analysis period in hours", ge=1, le=168)
):
    """
    Get agent performance analysis and metrics.
    
    Args:
        agent_name: Optional specific agent to analyze
        agent_type: Optional filter by agent type
        hours: Analysis period in hours (1-168)
    """
    try:
        telemetry = get_agent_telemetry()
        
        # Start collection if not already active
        if not telemetry.collection_active:
            await telemetry.start_collection()
        
        analyses = await telemetry.analyze_agent_performance(
            agent_name=agent_name,
            agent_type=agent_type,
            hours=hours
        )
        
        response_analyses = []
        for name, analysis in analyses.items():
            response_analyses.append(AgentPerformanceResponse(
                agent_name=analysis.agent_name,
                agent_type=analysis.agent_type.value,
                analysis_period_hours=hours,
                total_executions=analysis.total_executions,
                success_rate=analysis.success_rate,
                error_rate=analysis.error_rate,
                average_duration_ms=analysis.average_duration_ms,
                median_duration_ms=analysis.median_duration_ms,
                p95_duration_ms=analysis.p95_duration_ms,
                performance_category=analysis.performance_category.value,
                performance_trend=analysis.performance_trend,
                efficiency_score=analysis.calculate_efficiency_score(),
                optimization_recommendations=analysis.optimization_recommendations
            ))
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis_period_hours": hours,
            "total_agents_analyzed": len(response_analyses),
            "filters": {
                "agent_name": agent_name,
                "agent_type": agent_type.value if agent_type else None
            },
            "analyses": response_analyses
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/performance/system", response_model=SystemPerformanceResponse)
async def get_system_performance(
    hours: int = Query(24, description="Analysis period in hours", ge=1, le=168)
):
    """
    Get comprehensive system-wide performance report.
    
    Args:
        hours: Analysis period in hours (1-168)
    """
    try:
        telemetry = get_agent_telemetry()
        
        report = await telemetry.generate_system_performance_report(hours=hours)
        
        return SystemPerformanceResponse(
            generated_at=report.generated_at,
            analysis_period_hours=hours,
            total_agents=report.total_agents,
            active_agents=report.active_agents,
            total_executions=report.total_executions,
            system_success_rate=report.system_success_rate,
            consensus_success_rate=report.consensus_success_rate,
            escalation_rate=report.escalation_rate,
            performance_trends=report.performance_trends,
            bottlenecks=report.bottlenecks,
            system_recommendations=report.system_recommendations
        )
        
    except Exception as e:
        logger.error(f"Failed to get system performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/telemetry/events")
async def get_telemetry_events(
    hours: int = Query(24, description="Hours of history to retrieve", ge=1, le=168),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    event_type: Optional[TelemetryEventType] = Query(None, description="Filter by event type")
):
    """
    Get raw telemetry events for detailed analysis.
    
    Args:
        hours: Number of hours of history to retrieve (1-168)
        agent_name: Optional filter by agent name
        event_type: Optional filter by event type
    """
    try:
        telemetry = get_agent_telemetry()
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter events
        events = [
            event for event in telemetry.events
            if event.timestamp >= cutoff_time
        ]
        
        if agent_name:
            events = [e for e in events if e.agent_name == agent_name]
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Sort by timestamp (most recent first)
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "total_events": len(events),
            "filters": {
                "agent_name": agent_name,
                "event_type": event_type.value if event_type else None
            },
            "events": [event.to_dict() for event in events[:1000]]  # Limit to 1000 events
        }
        
    except Exception as e:
        logger.error(f"Failed to get telemetry events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Dashboard and Summary Endpoints

@router.get("/dashboard")
async def get_monitoring_dashboard():
    """
    Get comprehensive monitoring dashboard data.
    
    Returns a summary of all monitoring systems for dashboard display.
    """
    try:
        # Get integration health
        integration_monitor = get_integration_monitor()
        if not integration_monitor.monitoring_active:
            await integration_monitor.start_monitoring()
        
        integration_report = await integration_monitor.get_integration_health_report()
        
        # Get guardrail analytics
        guardrail_tracker = get_guardrail_tracker()
        if not guardrail_tracker.tracking_active:
            await guardrail_tracker.start_tracking()
        
        compliance_analytics = await guardrail_tracker.get_compliance_analytics()
        
        # Get agent performance
        agent_telemetry = get_agent_telemetry()
        if not agent_telemetry.collection_active:
            await agent_telemetry.start_collection()
        
        system_performance = await agent_telemetry.generate_system_performance_report(hours=24)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "integration_health": {
                "overall_status": integration_report.overall_status.value,
                "healthy_services": integration_report.healthy_services,
                "degraded_services": integration_report.degraded_services,
                "unhealthy_services": integration_report.unhealthy_services,
                "total_services": integration_report.total_services,
                "system_uptime": integration_report.system_uptime
            },
            "compliance": {
                "compliance_rate_24h": compliance_analytics["summary"]["compliance_rate_24h"],
                "total_events_24h": compliance_analytics["summary"]["total_events_24h"],
                "active_guardrails": compliance_analytics["summary"]["active_guardrails"],
                "decisions_breakdown": compliance_analytics["decisions_breakdown_24h"]
            },
            "agent_performance": {
                "system_success_rate": system_performance.system_success_rate,
                "total_executions": system_performance.total_executions,
                "active_agents": system_performance.active_agents,
                "escalation_rate": system_performance.escalation_rate,
                "bottlenecks": system_performance.bottlenecks[:5]  # Top 5 bottlenecks
            },
            "alerts": {
                "critical_issues": len([
                    svc for svc in integration_report.service_details.values()
                    if svc.status.value == "unhealthy"
                ]) + len(system_performance.bottlenecks),
                "warnings": len([
                    svc for svc in integration_report.service_details.values()
                    if svc.status.value == "degraded"
                ])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_monitoring_status():
    """
    Get status of all monitoring systems.
    
    Returns the operational status of monitoring components.
    """
    try:
        integration_monitor = get_integration_monitor()
        guardrail_tracker = get_guardrail_tracker()
        agent_telemetry = get_agent_telemetry()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "monitoring_systems": {
                "integration_monitor": {
                    "active": integration_monitor.monitoring_active,
                    "services_monitored": len(integration_monitor.health_metrics),
                    "monitoring_interval_seconds": integration_monitor.monitoring_interval.total_seconds()
                },
                "guardrail_tracker": {
                    "active": guardrail_tracker.tracking_active,
                    "total_events": len(guardrail_tracker.events),
                    "active_guardrails": len(guardrail_tracker.metrics)
                },
                "agent_telemetry": {
                    "active": agent_telemetry.collection_active,
                    "total_events": len(agent_telemetry.events),
                    "active_sessions": len(agent_telemetry.active_sessions)
                }
            },
            "overall_status": "operational" if all([
                integration_monitor.monitoring_active,
                guardrail_tracker.tracking_active,
                agent_telemetry.collection_active
            ]) else "partial"
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export Endpoints

@router.get("/export/integration-health")
async def export_integration_health():
    """Export integration health data for external analysis."""
    try:
        monitor = get_integration_monitor()
        report = await monitor.get_integration_health_report()
        
        return {
            "export_timestamp": datetime.utcnow().isoformat(),
            "data_type": "integration_health",
            "report": {
                "timestamp": report.timestamp.isoformat(),
                "overall_status": report.overall_status.value,
                "service_counts": {
                    "healthy": report.healthy_services,
                    "degraded": report.degraded_services,
                    "unhealthy": report.unhealthy_services,
                    "total": report.total_services
                },
                "services": {
                    name: {
                        "status": metrics.status.value,
                        "response_time_ms": metrics.response_time_ms,
                        "error_rate": metrics.error_rate,
                        "availability": metrics.availability,
                        "last_check": metrics.last_check.isoformat()
                    }
                    for name, metrics in report.service_details.items()
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to export integration health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/guardrail-events")
async def export_guardrail_events(
    hours: int = Query(24, description="Hours of data to export", ge=1, le=168),
    format_type: str = Query("json", description="Export format")
):
    """Export guardrail events for compliance reporting."""
    try:
        tracker = get_guardrail_tracker()
        
        exported_data = await tracker.export_events(
            format_type=format_type,
            hours=hours
        )
        
        return {
            "export_timestamp": datetime.utcnow().isoformat(),
            "data_type": "guardrail_events",
            "format": format_type,
            "period_hours": hours,
            "data": exported_data
        }
        
    except Exception as e:
        logger.error(f"Failed to export guardrail events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/agent-telemetry")
async def export_agent_telemetry(
    hours: int = Query(24, description="Hours of data to export", ge=1, le=168),
    agent_name: Optional[str] = Query(None, description="Specific agent to export"),
    format_type: str = Query("json", description="Export format")
):
    """Export agent telemetry data for performance analysis."""
    try:
        telemetry = get_agent_telemetry()
        
        exported_data = await telemetry.export_telemetry_data(
            format_type=format_type,
            hours=hours,
            agent_name=agent_name
        )
        
        return {
            "export_timestamp": datetime.utcnow().isoformat(),
            "data_type": "agent_telemetry",
            "format": format_type,
            "period_hours": hours,
            "agent_filter": agent_name,
            "data": exported_data
        }
        
    except Exception as e:
        logger.error(f"Failed to export agent telemetry: {e}")
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/enhanced/status")
async def get_enhanced_monitoring_status():
    """
    Get enhanced monitoring integration status.
    
    Returns status of Prometheus integration and metrics collection.
    """
    try:
        from src.services.enhanced_monitoring_integration import get_enhanced_monitoring_integration
        
        monitoring = get_enhanced_monitoring_integration()
        status = await monitoring.get_monitoring_status()
        
        return {
            "status": "success",
            "enhanced_monitoring": status,
            "prometheus_integration": {
                "metrics_endpoint": "/metrics",
                "collection_active": status["monitoring_active"],
                "metrics_exported": status["prometheus_integration"]["metrics_exported"]
            },
            "grafana_integration": {
                "dashboard_available": True,
                "dashboard_config_endpoint": "/monitoring/enhanced/grafana-config"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get enhanced monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enhanced/grafana-config")
async def get_grafana_dashboard_config():
    """
    Get Grafana dashboard configuration for enhanced monitoring.
    
    Returns JSON configuration that can be imported into Grafana.
    """
    try:
        from src.services.enhanced_monitoring_integration import get_enhanced_monitoring_integration
        
        monitoring = get_enhanced_monitoring_integration()
        config = await monitoring.create_grafana_dashboard_config()
        
        return {
            "status": "success",
            "grafana_config": config,
            "import_instructions": {
                "step_1": "Copy the dashboard configuration from 'grafana_config'",
                "step_2": "In Grafana, go to '+' -> Import",
                "step_3": "Paste the JSON configuration",
                "step_4": "Configure data source as Prometheus (http://prometheus:9090)",
                "step_5": "Save and view the dashboard"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get Grafana config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhanced/start")
async def start_enhanced_monitoring():
    """Start enhanced monitoring integration."""
    try:
        from src.services.enhanced_monitoring_integration import get_enhanced_monitoring_integration
        
        monitoring = get_enhanced_monitoring_integration()
        await monitoring.start_enhanced_monitoring()
        
        return {
            "status": "success",
            "message": "Enhanced monitoring started",
            "monitoring_active": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start enhanced monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhanced/stop")
async def stop_enhanced_monitoring():
    """Stop enhanced monitoring integration."""
    try:
        from src.services.enhanced_monitoring_integration import get_enhanced_monitoring_integration
        
        monitoring = get_enhanced_monitoring_integration()
        await monitoring.stop_enhanced_monitoring()
        
        return {
            "status": "success",
            "message": "Enhanced monitoring stopped",
            "monitoring_active": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to stop enhanced monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integration/validate")
async def validate_system_integration():
    """
    Execute comprehensive system integration validation.
    
    Validates all enhancements work together correctly and meet performance targets.
    """
    try:
        from src.services.system_integration_validator import validate_complete_system_integration
        
        logger.info("Starting comprehensive system integration validation")
        
        # Execute validation
        validation_report = await validate_complete_system_integration()
        
        return {
            "status": "success",
            "validation_report": {
                "validation_id": validation_report.validation_id,
                "overall_status": validation_report.overall_status.value,
                "summary": {
                    "total_tests": validation_report.total_tests,
                    "passed_tests": validation_report.passed_tests,
                    "failed_tests": validation_report.failed_tests,
                    "warning_tests": validation_report.warning_tests,
                    "success_rate": f"{(validation_report.passed_tests / validation_report.total_tests * 100):.1f}%" if validation_report.total_tests > 0 else "0%"
                },
                "execution_time": {
                    "total_duration_ms": validation_report.total_duration_ms,
                    "started_at": validation_report.started_at.isoformat(),
                    "completed_at": validation_report.completed_at.isoformat()
                },
                "performance_metrics": validation_report.performance_metrics,
                "recommendations": validation_report.recommendations,
                "test_results": [
                    {
                        "test_name": result.test_name,
                        "component": result.component,
                        "status": result.status.value,
                        "message": result.message,
                        "execution_time_ms": result.execution_time_ms,
                        "timestamp": result.timestamp.isoformat()
                    }
                    for result in validation_report.test_results
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to execute system integration validation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integration/status")
async def get_integration_validation_status():
    """
    Get current integration validation status.
    
    Returns information about the last validation run and system health.
    """
    try:
        # Get status from various integrated components
        integration_status = {
            "showcase_controller": {"available": False, "status": "unknown"},
            "3d_visualization": {"available": False, "status": "unknown"},
            "enhanced_monitoring": {"available": False, "status": "unknown"},
            "websocket_manager": {"available": False, "status": "unknown"}
        }
        
        # Check showcase controller
        try:
            from src.services.showcase_controller import get_showcase_controller
            showcase = get_showcase_controller()
            integration_status["showcase_controller"] = {
                "available": True,
                "status": "operational"
            }
        except Exception as e:
            integration_status["showcase_controller"]["error"] = str(e)
        
        # Check 3D visualization
        try:
            from src.services.visual_3d_integration import get_visual_3d_integration
            visual_3d = get_visual_3d_integration()
            viz_status = await visual_3d.get_visualization_status()
            integration_status["3d_visualization"] = {
                "available": True,
                "status": "operational" if viz_status.get("streaming_active") else "inactive",
                "details": viz_status
            }
        except Exception as e:
            integration_status["3d_visualization"]["error"] = str(e)
        
        # Check enhanced monitoring
        try:
            from src.services.enhanced_monitoring_integration import get_enhanced_monitoring_integration
            monitoring = get_enhanced_monitoring_integration()
            monitoring_status = await monitoring.get_monitoring_status()
            integration_status["enhanced_monitoring"] = {
                "available": True,
                "status": "operational" if monitoring_status.get("monitoring_active") else "inactive",
                "details": monitoring_status
            }
        except Exception as e:
            integration_status["enhanced_monitoring"]["error"] = str(e)
        
        # Check WebSocket manager
        try:
            from src.services.websocket_manager import get_websocket_manager
            websocket_manager = get_websocket_manager()
            connection_stats = websocket_manager.get_connection_stats()
            integration_status["websocket_manager"] = {
                "available": True,
                "status": "operational",
                "details": connection_stats
            }
        except Exception as e:
            integration_status["websocket_manager"]["error"] = str(e)
        
        # Calculate overall integration health
        available_components = sum(1 for comp in integration_status.values() if comp["available"])
        operational_components = sum(1 for comp in integration_status.values() if comp.get("status") == "operational")
        
        overall_health = {
            "total_components": len(integration_status),
            "available_components": available_components,
            "operational_components": operational_components,
            "health_percentage": f"{(operational_components / len(integration_status) * 100):.1f}%",
            "overall_status": "healthy" if operational_components == len(integration_status) else "degraded" if operational_components > 0 else "unhealthy"
        }
        
        return {
            "status": "success",
            "integration_health": overall_health,
            "component_status": integration_status,
            "validation_available": True,
            "validation_endpoint": "/monitoring/integration/validate",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get integration validation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))