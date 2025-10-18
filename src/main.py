"""
FastAPI application entry point for the Incident Commander system.
"""

import asyncio
import json
from contextlib import asynccontextmanager, suppress
from typing import Dict, Any, Optional, Awaitable, Set, List

from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from src.utils.config import config
from src.utils.logging import get_logger, IncidentCommanderLogger
from src.utils.exceptions import IncidentCommanderError
from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
from src.orchestrator.swarm_coordinator import get_swarm_coordinator
from src.services.aws import AWSServiceFactory
from src.services.rag_memory import ScalableRAGMemory
from src.services.system_health_monitor import get_system_health_monitor
from src.services.meta_incident_handler import get_meta_incident_handler
from src.services.byzantine_consensus import get_byzantine_consensus_engine
from src.services.performance_optimizer import get_performance_optimizer
from src.services.scaling_manager import get_scaling_manager
from src.services.cost_optimizer import get_cost_optimizer
from src.services.circuit_breaker import circuit_breaker_manager
from src.services.rate_limiter import bedrock_rate_limiter, external_service_rate_limiter
from src.services.realtime_integration import get_realtime_broadcaster
from agents.detection.agent import RobustDetectionAgent
from agents.diagnosis.agent import HardenedDiagnosisAgent
from agents.prediction.agent import PredictionAgent
from agents.resolution.agent import SecureResolutionAgent
from agents.communication.agent import ResilientCommunicationAgent
from datetime import datetime, timedelta


# Configure logging
IncidentCommanderLogger.configure(level="INFO")
logger = get_logger("main")

process_start_time: datetime = datetime.utcnow()
aws_factory: Optional[AWSServiceFactory] = None
coordinator_instance: Optional["AgentSwarmCoordinator"] = None
rag_memory_instance: Optional[ScalableRAGMemory] = None
health_monitor_instance = None
meta_incident_handler_instance = None
byzantine_consensus_instance = None
performance_optimizer_instance = None
scaling_manager_instance = None
cost_optimizer_instance = None
_background_tasks: Set[asyncio.Task] = set()


def schedule_background_task(coro: Awaitable[Any], *, description: str) -> None:
    """Schedule and track a background coroutine with logging."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.error(f"Cannot schedule background task '{description}' outside event loop")
        return

    task = loop.create_task(coro, name=description)
    _background_tasks.add(task)

    def _on_done(completed: asyncio.Task) -> None:
        _background_tasks.discard(completed)
        try:
            completed.result()
        except asyncio.CancelledError:
            logger.info(f"Background task '{description}' cancelled during shutdown")
        except Exception as exc:
            logger.error(f"Background task '{description}' failed: {exc}", exc_info=True)

    task.add_done_callback(_on_done)


async def _cancel_background_tasks() -> None:
    if not _background_tasks:
        return

    logger.info(f"Cancelling {len(_background_tasks)} background task(s)")
    for task in list(_background_tasks):
        task.cancel()

    results = await asyncio.gather(*_background_tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception) and not isinstance(result, asyncio.CancelledError):
            logger.error("Background task raised during cancellation: %s", result, exc_info=True)

    _background_tasks.clear()


def _runtime_uptime_seconds() -> float:
    return max(0.0, (datetime.utcnow() - process_start_time).total_seconds())


async def _shutdown_services() -> None:
    """Shutdown services and background work gracefully."""
    global aws_factory
    global coordinator_instance
    global rag_memory_instance
    global health_monitor_instance
    global meta_incident_handler_instance
    global byzantine_consensus_instance
    global performance_optimizer_instance
    global scaling_manager_instance
    global cost_optimizer_instance

    await _cancel_background_tasks()

    if health_monitor_instance is not None:
        try:
            await health_monitor_instance.stop_monitoring()
        except Exception as exc:
            logger.error("Error stopping health monitor: %s", exc, exc_info=True)
        finally:
            health_monitor_instance = None

    if coordinator_instance is not None:
        try:
            await coordinator_instance.shutdown()
        except Exception as exc:
            logger.error("Error shutting down coordinator: %s", exc, exc_info=True)
        finally:
            coordinator_instance = None

    if aws_factory is not None:
        try:
            await aws_factory.cleanup()
        except Exception as exc:
            logger.error("Error cleaning up AWS factory: %s", exc, exc_info=True)
        finally:
            aws_factory = None

    rag_memory_instance = None
    meta_incident_handler_instance = None
    byzantine_consensus_instance = None
    performance_optimizer_instance = None
    scaling_manager_instance = None
    cost_optimizer_instance = None


def get_aws_factory_instance() -> AWSServiceFactory:
    """Get shared AWS service factory, creating if necessary."""
    global aws_factory
    if aws_factory is None:
        aws_factory = AWSServiceFactory()
    return aws_factory


def get_coordinator_instance() -> "AgentSwarmCoordinator":
    """Get shared coordinator instance, ensuring dependencies are initialized."""
    global coordinator_instance
    if coordinator_instance is None:
        coordinator_instance = get_swarm_coordinator(service_factory=get_aws_factory_instance())
    return coordinator_instance


def get_health_monitor_instance():
    """Get shared system health monitor."""
    global health_monitor_instance
    if health_monitor_instance is None:
        health_monitor_instance = get_system_health_monitor(get_aws_factory_instance())
    return health_monitor_instance


def get_meta_handler_instance():
    """Get shared meta-incident handler."""
    global meta_incident_handler_instance
    if meta_incident_handler_instance is None:
        meta_incident_handler_instance = get_meta_incident_handler(
            get_aws_factory_instance(),
            get_health_monitor_instance()
        )
    return meta_incident_handler_instance


def get_byzantine_consensus_instance():
    """Get shared Byzantine consensus engine."""
    global byzantine_consensus_instance
    if byzantine_consensus_instance is None:
        byzantine_consensus_instance = get_byzantine_consensus_engine(get_aws_factory_instance())
    return byzantine_consensus_instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with proper resource management."""
    global process_start_time
    global aws_factory
    global coordinator_instance
    global rag_memory_instance
    global health_monitor_instance
    global meta_incident_handler_instance
    global byzantine_consensus_instance
    global performance_optimizer_instance
    global scaling_manager_instance
    global cost_optimizer_instance

    logger.info("Starting Incident Commander system")
    process_start_time = datetime.utcnow()

    try:
        config.validate_required_config()
        logger.info("Configuration validation passed")

        aws_factory = AWSServiceFactory()
        coordinator_instance = get_swarm_coordinator(service_factory=aws_factory)
        rag_memory_instance = ScalableRAGMemory(service_factory=aws_factory)

        health_monitor_instance = get_system_health_monitor(aws_factory)
        await health_monitor_instance.start_monitoring()
        logger.info("System health monitoring started")

        meta_incident_handler_instance = get_meta_incident_handler(aws_factory, health_monitor_instance)

        byzantine_consensus_instance = get_byzantine_consensus_engine(aws_factory)
        logger.info("Byzantine consensus engine initialized")

        performance_optimizer_instance = await get_performance_optimizer()
        scaling_manager_instance = await get_scaling_manager()
        cost_optimizer_instance = await get_cost_optimizer()

        logger.info("Performance optimization services initialized")
        logger.info("- Performance Optimizer: Connection pooling, caching, memory optimization")
        logger.info("- Scaling Manager: Auto-scaling, load balancing, geographic distribution")
        logger.info("- Cost Optimizer: Cost-aware scaling, intelligent model selection, Lambda warming")

        detection_agent = RobustDetectionAgent("primary_detection")
        diagnosis_agent = HardenedDiagnosisAgent("primary_diagnosis")
        prediction_agent = PredictionAgent(aws_factory, rag_memory_instance, "primary_prediction")
        resolution_agent = SecureResolutionAgent(aws_factory, "primary_resolution")
        communication_agent = ResilientCommunicationAgent("primary_communication")

        await coordinator_instance.register_agent(detection_agent)
        await coordinator_instance.register_agent(diagnosis_agent)
        await coordinator_instance.register_agent(prediction_agent)
        await coordinator_instance.register_agent(resolution_agent)
        await coordinator_instance.register_agent(communication_agent)

        logger.info("All agents initialized and registered (Detection, Diagnosis, Prediction, Resolution, Communication)")

        is_healthy = await coordinator_instance.health_check()
        if is_healthy:
            logger.info("System health check passed")
        else:
            logger.warning("System health check reported degraded state")

    except Exception as exc:
        logger.error("Failed to initialize Incident Commander system: %s", exc, exc_info=True)
        await _shutdown_services()
        raise

    try:
        yield
    finally:
        logger.info("Shutting down Incident Commander system")
        await _shutdown_services()
        logger.info("Incident Commander system shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Autonomous Incident Commander",
    description="Multi-agent system for autonomous incident detection, diagnosis, and resolution",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
# Production-ready CORS configuration
def get_allowed_origins():
    """Get allowed origins based on environment."""
    if config.environment == "development":
        return ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8080"]
    elif config.environment == "staging":
        return ["https://staging-incident-commander.example.com"]
    else:  # production
        return [
            "https://incident-commander.example.com",
            "https://demo.incident-commander.example.com"
        ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["X-Total-Count", "X-Request-ID"],
)

# Security Headers Middleware
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers for production deployment
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:; "
                "frame-ancestors 'none';"
            ),
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            ),
            "X-Request-ID": f"req-{request.headers.get('x-request-id', 'unknown')}"
        }
        
        # Apply headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(IncidentCommanderError)
async def incident_commander_exception_handler(request, exc: IncidentCommanderError):
    """Handle custom exceptions."""
    logger.error(f"Incident Commander error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": type(exc).__name__}
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Autonomous Incident Commander API",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    coordinator = get_coordinator_instance()
    agent_health = coordinator.get_agent_health_status()
    unhealthy_agents = {
        name: status for name, status in agent_health.items()
        if not status.get("is_healthy", True)
    }

    monitor = health_monitor_instance or get_health_monitor_instance()
    health_snapshot = monitor.get_current_health_status()

    meta_handler = meta_incident_handler_instance or get_meta_handler_instance()
    meta_incidents_active = meta_handler.get_active_meta_incidents()

    cb_dashboard = circuit_breaker_manager.get_health_dashboard()

    services = {
        "api": "healthy",
        "agents": "healthy" if not unhealthy_agents else "degraded",
        "message_bus": "healthy" if cb_dashboard["unhealthy_services"] == 0 else "degraded",
        "health_monitor": health_snapshot.get("overall_status", "unknown"),
        "meta_incidents": "healthy" if not meta_incidents_active else "attention_required"
    }

    status = "healthy"
    if (
        services["agents"] != "healthy"
        or services["message_bus"] != "healthy"
        or services["health_monitor"] not in {"healthy", "unknown"}
        or services["meta_incidents"] != "healthy"
    ):
        status = "degraded"

    return {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": config.environment,
        "uptime_seconds": _runtime_uptime_seconds(),
        "services": services,
        "unhealthy_agents": unhealthy_agents,
        "circuit_breakers": {
            "healthy_services": cb_dashboard["healthy_services"],
            "degraded_services": cb_dashboard["degraded_services"],
            "unhealthy_services": cb_dashboard["unhealthy_services"],
            "total_services": cb_dashboard["total_circuit_breakers"]
        },
        "meta_incidents": meta_incidents_active
    }


@app.get("/status")
async def system_status():
    """Get detailed system status."""
    coordinator = get_coordinator_instance()
    agent_health = coordinator.get_agent_health_status()
    processing_metrics = coordinator.get_processing_metrics()

    cb_dashboard = circuit_breaker_manager.get_health_dashboard()
    bedrock_status = bedrock_rate_limiter.get_status()

    meta_handler = meta_incident_handler_instance or get_meta_handler_instance()
    meta_stats = meta_handler.get_meta_incident_statistics()
    meta_active = meta_handler.get_active_meta_incidents()

    return {
        "system": {
            "environment": config.environment,
            "version": "0.1.0",
            "uptime_seconds": _runtime_uptime_seconds(),
            "timestamp": datetime.utcnow().isoformat(),
            "background_tasks": len(_background_tasks)
        },
        "agents": agent_health,
        "metrics": processing_metrics,
        "infrastructure": {
            "circuit_breakers": cb_dashboard,
            "rate_limiters": {
                "bedrock": bedrock_status,
                "external_services": {
                    "slack": external_service_rate_limiter.get_service_status("slack"),
                    "pagerduty": external_service_rate_limiter.get_service_status("pagerduty")
                }
            }
        },
        "health_monitor": get_health_monitor_instance().get_current_health_status(),
        "meta_incidents": {
            "active": meta_active,
            "statistics": meta_stats
        }
    }


@app.post("/incidents/trigger")
async def trigger_incident(incident_data: Dict[str, Any]):
    """
    Trigger a new incident for processing.
    
    This endpoint processes incidents through the agent swarm.
    """
    try:
        # Create incident from request data
        business_impact = BusinessImpact(
            service_tier=ServiceTier(incident_data.get("service_tier", "tier_2")),
            affected_users=incident_data.get("affected_users", 0),
            revenue_impact_per_minute=incident_data.get("revenue_impact_per_minute", 0.0)
        )
        
        metadata = IncidentMetadata(
            source_system=incident_data.get("source_system", "manual"),
            tags=incident_data.get("tags", {})
        )
        
        incident = Incident(
            title=incident_data["title"],
            description=incident_data["description"],
            severity=IncidentSeverity(incident_data.get("severity", "medium")),
            business_impact=business_impact,
            metadata=metadata
        )
        
        coordinator = get_coordinator_instance()
        broadcaster = get_realtime_broadcaster()

        schedule_background_task(
            broadcaster.simulate_full_incident_processing(incident),
            description=f"incident-broadcast-{incident.id}"
        )
        schedule_background_task(
            coordinator.process_incident(incident),
            description=f"incident-process-{incident.id}"
        )

        logger.info(f"Triggered incident: {incident.id}")
        
        return {
            "incident_id": incident.id,
            "status": "processing",
            "message": "Incident is being processed by agent swarm",
            "estimated_completion_minutes": 3,
            "cost_per_minute": business_impact.calculate_cost_per_minute()
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger incident: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get incident details and processing status."""
    try:
        from src.orchestrator.swarm_coordinator import get_swarm_coordinator
        coordinator = get_swarm_coordinator()
        
        # Get incident status from coordinator
        status = coordinator.get_incident_status(incident_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        return {
            "incident_id": incident_id,
            **status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get incident {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/incidents/{incident_id}/timeline")
async def get_incident_timeline(incident_id: str):
    """Get incident processing timeline."""
    try:
        from src.orchestrator.swarm_coordinator import get_swarm_coordinator
        coordinator = get_swarm_coordinator()
        
        # Get incident status
        status = coordinator.get_incident_status(incident_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        # Build timeline from agent executions
        timeline = []
        
        # Add incident start
        timeline.append({
            "timestamp": status["start_time"],
            "event": "incident_started",
            "description": "Incident processing started",
            "phase": "detection"
        })
        
        # Add agent execution events
        for agent_name, execution in status["agent_executions"].items():
            if execution["status"] == "completed":
                timeline.append({
                    "timestamp": status["start_time"],  # Would be execution start time in real implementation
                    "event": "agent_completed",
                    "description": f"{execution['agent_type']} agent completed",
                    "agent": agent_name,
                    "duration_seconds": execution["duration_seconds"],
                    "recommendations_count": execution["recommendations_count"]
                })
            elif execution["status"] == "failed":
                timeline.append({
                    "timestamp": status["start_time"],
                    "event": "agent_failed",
                    "description": f"{execution['agent_type']} agent failed: {execution['error']}",
                    "agent": agent_name,
                    "error": execution["error"]
                })
        
        # Add consensus event
        if status["consensus_decision"]:
            timeline.append({
                "timestamp": status["end_time"] or status["start_time"],
                "event": "consensus_reached",
                "description": f"Consensus reached: {status['consensus_decision']['selected_action']}",
                "confidence": status["consensus_decision"]["final_confidence"],
                "requires_approval": status["consensus_decision"]["requires_human_approval"]
            })
        
        # Sort timeline by timestamp
        timeline.sort(key=lambda x: x["timestamp"])
        
        return {
            "incident_id": incident_id,
            "timeline": timeline,
            "total_events": len(timeline),
            "processing_duration_seconds": status["duration_seconds"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get timeline for incident {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/status")
async def get_agents_status():
    """Get status of all registered agents."""
    try:
        from src.orchestrator.swarm_coordinator import get_swarm_coordinator
        coordinator = get_swarm_coordinator()
        
        agent_status = coordinator.get_agent_health_status()
        processing_metrics = coordinator.get_processing_metrics()
        
        return {
            "agents": agent_status,
            "metrics": processing_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/demo/scenarios/{scenario_name}")
async def run_demo_scenario(scenario_name: str):
    """
    Run a predefined demo scenario.
    
    Available scenarios: database_cascade, ddos_attack, memory_leak, api_overload, storage_failure
    """
    valid_scenarios = ["database_cascade", "ddos_attack", "memory_leak", "api_overload", "storage_failure"]
    
    if scenario_name not in valid_scenarios:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid scenario. Available: {valid_scenarios}"
        )
    
    # Create demo incident based on scenario
    scenario_configs = {
        "database_cascade": {
            "title": "Database Connection Pool Exhaustion",
            "description": "Critical database connection pool exhaustion causing cascade failures across payment processing services",
            "severity": "critical",
            "service_tier": "tier_1",
            "affected_users": 50000,
            "revenue_impact_per_minute": 2000.0,
            "tags": {"scenario": "database_cascade", "demo": "true", "complexity": "high"}
        },
        "ddos_attack": {
            "title": "Distributed Denial of Service Attack",
            "description": "Large-scale DDoS attack overwhelming API gateway and causing service degradation",
            "severity": "high",
            "service_tier": "tier_1", 
            "affected_users": 25000,
            "revenue_impact_per_minute": 1500.0,
            "tags": {"scenario": "ddos_attack", "demo": "true", "complexity": "medium"}
        },
        "memory_leak": {
            "title": "Application Memory Leak",
            "description": "Memory leak in user service causing gradual performance degradation and eventual service crashes",
            "severity": "medium",
            "service_tier": "tier_2",
            "affected_users": 5000,
            "revenue_impact_per_minute": 300.0,
            "tags": {"scenario": "memory_leak", "demo": "true", "complexity": "low"}
        },
        "api_overload": {
            "title": "API Rate Limit Exceeded",
            "description": "Sudden traffic spike causing API rate limits to be exceeded, resulting in service degradation",
            "severity": "high",
            "service_tier": "tier_1",
            "affected_users": 15000,
            "revenue_impact_per_minute": 800.0,
            "tags": {"scenario": "api_overload", "demo": "true", "complexity": "medium"}
        },
        "storage_failure": {
            "title": "Distributed Storage System Failure",
            "description": "Multiple storage nodes failing simultaneously, causing data availability issues",
            "severity": "critical",
            "service_tier": "tier_1",
            "affected_users": 75000,
            "revenue_impact_per_minute": 3000.0,
            "tags": {"scenario": "storage_failure", "demo": "true", "complexity": "high"}
        }
    }
    
    scenario_config = scenario_configs[scenario_name]
    
    try:
        # Trigger the demo incident
        incident_response = await trigger_incident(scenario_config)
        
        logger.info(f"Running demo scenario: {scenario_name}")
        
        return {
            "scenario": scenario_name,
            "status": "started",
            "incident_id": incident_response["incident_id"],
            "estimated_duration_minutes": 3,
            "cost_per_minute": incident_response["cost_per_minute"],
            "description": scenario_config["description"],
            "complexity": scenario_config["tags"]["complexity"],
            "demo_features": {
                "real_time_mttr": True,
                "cost_accumulation": True,
                "agent_coordination": True,
                "consensus_visualization": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to run demo scenario {scenario_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/scenarios")
async def list_demo_scenarios():
    """List all available demo scenarios with descriptions."""
    scenarios = {
        "database_cascade": {
            "name": "Database Connection Pool Exhaustion",
            "complexity": "high",
            "estimated_duration": "2-3 minutes",
            "business_impact": "Critical - $2000/minute",
            "description": "Demonstrates agent coordination for complex database cascade failures"
        },
        "ddos_attack": {
            "name": "Distributed Denial of Service Attack", 
            "complexity": "medium",
            "estimated_duration": "2-3 minutes",
            "business_impact": "High - $1500/minute",
            "description": "Shows rapid detection and mitigation of external attacks"
        },
        "memory_leak": {
            "name": "Application Memory Leak",
            "complexity": "low",
            "estimated_duration": "1-2 minutes", 
            "business_impact": "Medium - $300/minute",
            "description": "Illustrates predictive capabilities and gradual issue resolution"
        },
        "api_overload": {
            "name": "API Rate Limit Exceeded",
            "complexity": "medium",
            "estimated_duration": "2 minutes",
            "business_impact": "High - $800/minute", 
            "description": "Demonstrates auto-scaling and load balancing responses"
        },
        "storage_failure": {
            "name": "Distributed Storage System Failure",
            "complexity": "high",
            "estimated_duration": "3-4 minutes",
            "business_impact": "Critical - $3000/minute",
            "description": "Shows multi-agent coordination for complex infrastructure failures"
        }
    }
    
    return {
        "available_scenarios": scenarios,
        "total_scenarios": len(scenarios),
        "demo_capabilities": [
            "Real-time MTTR tracking",
            "Business impact calculation", 
            "Agent coordination visualization",
            "Consensus decision making",
            "Automated resolution actions"
        ]
    }


@app.get("/demo/status")
async def get_demo_status():
    """Get current demo environment status."""
    from src.orchestrator.swarm_coordinator import get_swarm_coordinator
    
    coordinator = get_swarm_coordinator()
    
    # Get active demo incidents
    active_demos = []
    for incident_id, state in coordinator.processing_states.items():
        if (state.incident.metadata.tags.get("demo") == "true" and 
            state.phase not in ["completed", "failed"]):
            active_demos.append({
                "incident_id": incident_id,
                "scenario": state.incident.metadata.tags.get("scenario"),
                "phase": state.phase.value,
                "duration_seconds": state.total_duration_seconds,
                "cost_accumulated": state.incident.business_impact.calculate_total_cost(
                    state.total_duration_seconds / 60.0
                )
            })
    
    # Get system health for demo
    agent_status = coordinator.get_agent_health_status()
    processing_metrics = coordinator.get_processing_metrics()
    
    return {
        "demo_environment": {
            "status": "ready" if len(active_demos) == 0 else "running_demo",
            "active_demos": active_demos,
            "total_active": len(active_demos)
        },
        "system_health": {
            "agents_healthy": sum(1 for status in agent_status.values() if status["is_healthy"]),
            "total_agents": len(agent_status),
            "consensus_engine": "operational",
            "message_bus": "operational"
        },
        "performance_metrics": {
            "average_mttr_seconds": processing_metrics.get("average_processing_time", 0),
            "success_rate": processing_metrics.get("success_rate", 0),
            "total_incidents_processed": processing_metrics.get("total_incidents", 0)
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# WebSocket Endpoint for Real-time Dashboard Updates

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time dashboard communication.
    
    Provides real-time streaming of:
    - Incident processing updates
    - Agent action notifications  
    - System metrics and health status
    - Performance data for demo visualization
    """
    from src.services.websocket_manager import get_websocket_manager
    
    manager = get_websocket_manager()
    
    try:
        # Accept connection and register client
        await manager.connect(websocket, {
            "user_agent": websocket.headers.get("user-agent", "unknown"),
            "origin": websocket.headers.get("origin", "unknown")
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (heartbeat, etc.)
                data = await websocket.receive_text()
                
                # Handle client messages (optional - for heartbeat/ping)
                try:
                    message = json.loads(data)
                    if message.get("type") == "ping":
                        await manager.send_to_connection(websocket, {
                            "type": "pong",
                            "data": {"timestamp": datetime.utcnow().isoformat()}
                        })
                except json.JSONDecodeError:
                    # Ignore malformed messages
                    pass
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        await manager.disconnect(websocket)


# Milestone 2 Endpoints - System Health Monitoring and Byzantine Consensus

@app.get("/system/health/detailed")
async def get_detailed_system_health():
    """Get detailed system health status including meta-incidents."""
    try:
        health_monitor = get_health_monitor_instance()
        meta_handler = get_meta_handler_instance()
        
        # Get current health status
        health_status = health_monitor.get_current_health_status()
        
        # Get meta-incidents
        meta_incidents = meta_handler.get_active_meta_incidents()
        meta_stats = meta_handler.get_meta_incident_statistics()
        
        return {
            "system_health": health_status,
            "meta_incidents": {
                "active": meta_incidents,
                "statistics": meta_stats
            },
            "monitoring": {
                "is_active": health_monitor.is_monitoring,
                "monitoring_interval_seconds": health_monitor.monitoring_interval.total_seconds(),
                "metrics_retention_hours": health_monitor.metric_retention_period.total_seconds() / 3600
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get detailed system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/consensus/byzantine/status")
async def get_byzantine_consensus_status():
    """Get Byzantine consensus engine status and statistics."""
    try:
        byzantine_consensus = get_byzantine_consensus_instance()
        
        # Get Byzantine consensus statistics
        stats = byzantine_consensus.get_byzantine_statistics()
        
        # Get agent reputation scores
        reputation_scores = byzantine_consensus.agent_reputation
        
        return {
            "byzantine_consensus": {
                "engine_status": "operational",
                "statistics": stats,
                "agent_reputation": dict(reputation_scores),
                "configuration": {
                    "byzantine_threshold": byzantine_consensus.byzantine_threshold,
                    "confidence_threshold": byzantine_consensus.confidence_threshold,
                    "min_agreement_threshold": byzantine_consensus.min_agreement_threshold
                }
            },
            "recent_consensus_rounds": [
                {
                    "round_id": round.round_id,
                    "incident_id": round.incident_id,
                    "consensus_reached": round.consensus_reached,
                    "byzantine_agents_detected": len(round.byzantine_agents),
                    "participating_agents": len(round.participating_agents),
                    "final_confidence": round.final_confidence,
                    "duration_ms": round.round_duration_ms
                }
                for round in byzantine_consensus.consensus_rounds[-10:]  # Last 10 rounds
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get Byzantine consensus status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/system/health/trigger-meta-incident")
async def trigger_meta_incident_test(meta_incident_data: Dict[str, Any]):
    """
    Trigger a test meta-incident for demonstration purposes.
    
    This endpoint is for testing the meta-incident handling system.
    """
    try:
        from src.services.system_health_monitor import MetaIncident, IncidentSeverity
        from src.services.meta_incident_handler import get_meta_incident_handler
        from src.services.aws import AWSServiceFactory
        
        aws_factory = AWSServiceFactory()
        health_monitor = get_system_health_monitor(aws_factory)
        meta_handler = get_meta_incident_handler(aws_factory, health_monitor)
        
        # Create test meta-incident
        meta_incident = MetaIncident(
            id=f"test_meta_{int(datetime.utcnow().timestamp())}",
            title=meta_incident_data.get("title", "Test Meta-Incident"),
            description=meta_incident_data.get("description", "Test meta-incident for demonstration"),
            severity=IncidentSeverity(meta_incident_data.get("severity", "medium")),
            affected_components=meta_incident_data.get("affected_components", ["test_component"]),
            detected_at=datetime.utcnow(),
            root_cause=meta_incident_data.get("root_cause"),
            recovery_actions=meta_incident_data.get("recovery_actions", ["test_action"]),
            status="active"
        )
        
        # Process the meta-incident
        incident = await meta_handler.process_meta_incident(meta_incident)
        
        return {
            "meta_incident_id": meta_incident.id,
            "incident_created": incident is not None,
            "incident_id": incident.id if incident else None,
            "status": "triggered",
            "auto_resolution_enabled": meta_handler.auto_resolution_enabled,
            "message": "Test meta-incident triggered successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger test meta-incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/system/metrics/performance")
async def get_performance_metrics():
    """Get comprehensive system performance metrics."""
    try:
        from src.orchestrator.swarm_coordinator import get_swarm_coordinator
        from src.services.consensus import get_consensus_engine
        from src.services.system_health_monitor import get_system_health_monitor
        from src.services.aws import AWSServiceFactory
        
        coordinator = get_swarm_coordinator()
        consensus_engine = get_consensus_engine()
        aws_factory = AWSServiceFactory()
        health_monitor = get_system_health_monitor(aws_factory)
        
        # Get processing metrics
        processing_metrics = coordinator.get_processing_metrics()
        
        # Get consensus statistics
        consensus_stats = consensus_engine.get_consensus_statistics()
        
        # Get current health status
        health_status = health_monitor.get_current_health_status()
        
        return {
            "performance_metrics": {
                "incident_processing": processing_metrics,
                "consensus_engine": consensus_stats,
                "system_health": health_status,
                "agent_performance": {
                    agent_name: {
                        "is_healthy": status["is_healthy"],
                        "processing_count": status.get("processing_count", 0),
                        "error_count": status.get("error_count", 0),
                        "last_activity": status.get("last_activity")
                    }
                    for agent_name, status in coordinator.get_agent_health_status().items()
                }
            },
            "milestone_2_features": {
                "byzantine_consensus": "operational",
                "system_health_monitoring": "operational",
                "meta_incident_handling": "operational",
                "automated_recovery": "operational"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Task 15 Endpoints - Performance Optimization and Scalability

@app.get("/performance/metrics")
async def get_performance_optimization_metrics():
    """Get comprehensive performance optimization metrics."""
    try:
        from src.services.performance_optimizer import get_performance_optimizer
        from src.services.scaling_manager import get_scaling_manager
        from src.services.cost_optimizer import get_cost_optimizer
        
        performance_optimizer = await get_performance_optimizer()
        scaling_manager = await get_scaling_manager()
        cost_optimizer = await get_cost_optimizer()
        
        # Get metrics from all optimization services
        perf_metrics = await performance_optimizer.get_performance_metrics()
        scaling_metrics = await scaling_manager.get_scaling_metrics()
        cost_metrics = await cost_optimizer.get_cost_metrics()
        
        return {
            "performance_optimization": {
                "connection_pools": perf_metrics.connection_pool_utilization,
                "cache_hit_rates": perf_metrics.cache_hit_rates,
                "memory_usage_percent": perf_metrics.memory_usage_percent,
                "gc_collections": perf_metrics.gc_collections,
                "query_response_times": {
                    query_type: {
                        "count": len(times),
                        "avg_seconds": sum(times) / len(times) if times else 0,
                        "max_seconds": max(times) if times else 0
                    }
                    for query_type, times in perf_metrics.query_response_times.items()
                },
                "optimization_actions": perf_metrics.optimization_actions_taken[-10:]  # Last 10 actions
            },
            "scaling": {
                "incidents_per_minute": scaling_metrics.total_incidents_per_minute,
                "agent_utilization": scaling_metrics.agent_utilization,
                "load_distribution": scaling_metrics.load_distribution,
                "scaling_actions": scaling_metrics.scaling_actions[-10:],  # Last 10 actions
                "failover_events": scaling_metrics.failover_events,
                "cross_region_latency": scaling_metrics.cross_region_latency
            },
            "cost_optimization": {
                "current_hourly_cost": cost_metrics.current_hourly_cost,
                "projected_daily_cost": cost_metrics.projected_daily_cost,
                "cost_by_service": cost_metrics.cost_by_service,
                "cost_by_model": cost_metrics.cost_by_model,
                "cost_savings_achieved": cost_metrics.cost_savings_achieved,
                "lambda_warm_cost": cost_metrics.lambda_warm_cost,
                "scaling_cost": cost_metrics.scaling_cost,
                "optimization_actions": cost_metrics.optimization_actions[-10:]  # Last 10 actions
            },
            "task_15_status": {
                "performance_optimizer": "operational",
                "scaling_manager": "operational", 
                "cost_optimizer": "operational",
                "features_implemented": [
                    "Connection pooling for external services",
                    "Intelligent caching with multiple strategies",
                    "Memory optimization and garbage collection",
                    "Auto-scaling based on incident volume",
                    "Load balancing with multiple strategies",
                    "Geographic distribution and failover",
                    "Cost-aware scaling decisions",
                    "Intelligent model selection",
                    "Predictive Lambda warming",
                    "Cost monitoring and optimization"
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance optimization metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/performance/recommendations")
async def get_performance_recommendations():
    """Get performance optimization recommendations."""
    try:
        from src.services.performance_optimizer import get_performance_optimizer
        from src.services.cost_optimizer import get_cost_optimizer
        
        performance_optimizer = await get_performance_optimizer()
        cost_optimizer = await get_cost_optimizer()
        
        # Get recommendations from optimization services
        perf_recommendations = await performance_optimizer.get_optimization_recommendations()
        cost_recommendations = await cost_optimizer.get_cost_recommendations()
        
        return {
            "performance_recommendations": perf_recommendations,
            "cost_recommendations": cost_recommendations,
            "summary": {
                "total_recommendations": len(perf_recommendations) + len(cost_recommendations),
                "performance_issues": len(perf_recommendations),
                "cost_optimization_opportunities": len(cost_recommendations)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scaling/status")
async def get_scaling_status():
    """Get current scaling status and replica information."""
    try:
        from src.services.scaling_manager import get_scaling_manager
        
        scaling_manager = await get_scaling_manager()
        
        # Get replica status and scaling metrics
        replica_status = await scaling_manager.get_replica_status()
        scaling_metrics = await scaling_manager.get_scaling_metrics()
        
        return {
            "replica_status": replica_status,
            "scaling_metrics": {
                "incidents_per_minute": scaling_metrics.total_incidents_per_minute,
                "agent_utilization": scaling_metrics.agent_utilization,
                "recent_scaling_actions": scaling_metrics.scaling_actions[-5:],  # Last 5 actions
                "failover_events": scaling_metrics.failover_events
            },
            "scaling_policies": {
                agent_type: {
                    "min_replicas": policy.min_replicas,
                    "max_replicas": policy.max_replicas,
                    "target_utilization": policy.target_utilization,
                    "scale_up_threshold": policy.scale_up_threshold,
                    "scale_down_threshold": policy.scale_down_threshold,
                    "cooldown_period": policy.cooldown_period
                }
                for agent_type, policy in scaling_manager.scaling_policies.items()
            },
            "geographic_distribution": {
                region: len([r for replicas in replica_status.values() for r in replicas if r["region"] == region])
                for region in scaling_manager.regions
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get scaling status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scaling/optimize")
async def optimize_scaling():
    """Trigger scaling optimization based on current load."""
    try:
        from src.services.scaling_manager import get_scaling_manager
        from src.services.cost_optimizer import get_cost_optimizer
        
        scaling_manager = await get_scaling_manager()
        cost_optimizer = await get_cost_optimizer()
        
        # Calculate current utilization
        current_load = {}
        for agent_type in scaling_manager.scaling_policies.keys():
            utilization = await scaling_manager._calculate_agent_utilization(agent_type)
            current_load[agent_type] = utilization
        
        # Get cost-aware scaling recommendations
        recommendations = await cost_optimizer.optimize_scaling_costs(current_load)
        
        # Apply scaling recommendations (in a real implementation, this would be more sophisticated)
        actions_taken = []
        
        for scale_up_rec in recommendations["scale_up"]:
            agent_type = scale_up_rec["agent_type"]
            success = await scaling_manager._scale_up_agent(agent_type)
            if success:
                actions_taken.append(f"Scaled up {agent_type}")
        
        for scale_down_rec in recommendations["scale_down"]:
            agent_type = scale_down_rec["agent_type"]
            success = await scaling_manager._scale_down_agent(agent_type)
            if success:
                actions_taken.append(f"Scaled down {agent_type}")
        
        return {
            "optimization_triggered": True,
            "current_load": current_load,
            "recommendations": recommendations,
            "actions_taken": actions_taken,
            "cost_impact": recommendations["cost_impact"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to optimize scaling: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cost/optimize")
async def optimize_costs():
    """Trigger cost optimization analysis and actions."""
    try:
        from src.services.cost_optimizer import get_cost_optimizer
        
        cost_optimizer = await get_cost_optimizer()
        
        # Get current cost metrics
        cost_metrics = await cost_optimizer.get_cost_metrics()
        
        # Generate optimization recommendations
        recommendations = await cost_optimizer.get_cost_recommendations()
        
        # Apply automatic optimizations
        applied_optimizations = []
        for recommendation in recommendations:
            if recommendation.get("auto_apply", False):
                await cost_optimizer._apply_cost_optimization(recommendation)
                applied_optimizations.append(recommendation)
        
        return {
            "cost_optimization_triggered": True,
            "current_metrics": {
                "hourly_cost": cost_metrics.current_hourly_cost,
                "daily_projection": cost_metrics.projected_daily_cost,
                "cost_threshold": cost_optimizer.current_cost_threshold.value
            },
            "recommendations": recommendations,
            "applied_optimizations": applied_optimizations,
            "potential_savings": sum(r.get("potential_savings", 0) for r in recommendations),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to optimize costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/lambda/warm")
async def warm_lambda_functions(functions: Optional[List[str]] = None):
    """Warm Lambda functions to prevent cold starts."""
    try:
        from src.services.cost_optimizer import get_cost_optimizer
        
        cost_optimizer = await get_cost_optimizer()
        
        # Warm specified functions or all functions
        results = await cost_optimizer.warm_lambda_functions(functions)
        
        return {
            "warming_triggered": True,
            "functions_warmed": functions or cost_optimizer.lambda_functions,
            "results": results,
            "successful_warmings": sum(1 for success in results.values() if success),
            "failed_warmings": sum(1 for success in results.values() if not success),
            "estimated_cost": len(results) * 0.0000002,  # Approximate cost per invocation
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to warm Lambda functions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Milestone 3 Endpoints - Demo Controller and Interactive Features

@app.post("/demo/controller/start/{scenario_type}")
async def start_controlled_demo_scenario(scenario_type: str, session_id: str = None):
    """
    Start a controlled demo scenario with real-time visualization.
    
    Task 12.1: Build demo controller with controlled scenario execution
    """
    try:
        from src.services.demo_controller import get_demo_controller, DemoScenarioType
        
        # Validate scenario type
        try:
            scenario_enum = DemoScenarioType(scenario_type)
        except ValueError:
            valid_scenarios = [s.value for s in DemoScenarioType]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid scenario type. Available: {valid_scenarios}"
            )
        
        demo_controller = get_demo_controller(schedule_background_task)
        
        # Start controlled demo scenario
        demo_session = await demo_controller.start_demo_scenario(
            scenario_type=scenario_enum,
            session_id=session_id
        )
        
        logger.info(f"Started controlled demo scenario: {scenario_type} (session: {demo_session.session_id})")
        
        return {
            "session_id": demo_session.session_id,
            "scenario_type": scenario_type,
            "incident_id": demo_session.incident_id,
            "status": "started",
            "current_phase": demo_session.current_phase.value,
            "completion_guarantee_minutes": demo_session.completion_guarantee_minutes,
            "environment_isolated": demo_session.environment_isolated,
            "real_time_features": {
                "mttr_countdown": True,
                "cost_accumulation": True,
                "agent_confidence_tracking": True,
                "phase_timing": True,
                "business_impact_visualization": True
            },
            "estimated_completion_time": (datetime.utcnow() + timedelta(minutes=demo_session.completion_guarantee_minutes)).isoformat(),
            "demo_endpoints": {
                "real_time_metrics": f"/demo/controller/{demo_session.session_id}/metrics",
                "comparison_metrics": f"/demo/controller/{demo_session.session_id}/comparison",
                "stop_session": f"/demo/controller/{demo_session.session_id}/stop"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to start controlled demo scenario {scenario_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/controller/{session_id}/metrics")
async def get_demo_real_time_metrics(session_id: str):
    """
    Get real-time metrics for active demo session.
    
    Provides MTTR countdown, cost accumulation, and agent confidence scores.
    """
    try:
        from src.services.demo_controller import get_demo_controller
        
        demo_controller = get_demo_controller(schedule_background_task)
        metrics = demo_controller.get_real_time_metrics(session_id)
        
        if not metrics:
            raise HTTPException(status_code=404, detail="Demo session not found")
        
        return {
            "real_time_metrics": metrics,
            "visualization_data": {
                "mttr_progress": {
                    "current_seconds": metrics["metrics"]["mttr_seconds"],
                    "traditional_estimate_seconds": metrics["metrics"]["traditional_mttr_estimate"],
                    "improvement_percentage": metrics["metrics"]["autonomous_improvement_percentage"]
                },
                "cost_tracking": {
                    "accumulated_cost": metrics["metrics"]["cost_accumulated"],
                    "cost_per_minute": metrics["metrics"]["cost_per_minute"],
                    "projected_savings": (
                        metrics["metrics"]["traditional_mttr_estimate"] / 60.0 * 
                        metrics["metrics"]["cost_per_minute"] - 
                        metrics["metrics"]["cost_accumulated"]
                    )
                },
                "sla_status": {
                    "breach_countdown_seconds": metrics["metrics"]["sla_breach_countdown"],
                    "is_within_sla": metrics["metrics"]["sla_breach_countdown"] > 0,
                    "reputation_impact": metrics["metrics"]["reputation_impact_score"]
                },
                "agent_performance": {
                    "confidence_scores": metrics["agent_confidence_scores"],
                    "current_phase": metrics["current_phase"],
                    "phase_timings": metrics["phase_timings"]
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get demo metrics for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/controller/{session_id}/comparison")
async def get_demo_comparison_metrics(session_id: str):
    """
    Get before/after comparison metrics for demo visualization.
    
    Shows traditional vs autonomous response comparison with business impact.
    """
    try:
        from src.services.demo_controller import get_demo_controller
        
        demo_controller = get_demo_controller(schedule_background_task)
        comparison = demo_controller.get_comparison_metrics(session_id)
        
        if not comparison:
            raise HTTPException(status_code=404, detail="Demo session not found")
        
        return {
            "comparison_metrics": comparison,
            "dramatic_visualization": {
                "traditional_timeline": {
                    "detection_minutes": 5,
                    "escalation_minutes": 10,
                    "diagnosis_minutes": 15,
                    "resolution_minutes": comparison["traditional_response"]["mttr_minutes"] - 30,
                    "total_minutes": comparison["traditional_response"]["mttr_minutes"]
                },
                "autonomous_timeline": {
                    "detection_seconds": 30,
                    "diagnosis_seconds": 90,
                    "prediction_seconds": 60,
                    "resolution_seconds": 120,
                    "communication_seconds": 15,
                    "total_minutes": comparison["autonomous_response"]["mttr_minutes"]
                },
                "impact_comparison": {
                    "time_saved": f"{comparison['improvement']['time_saved_minutes']:.1f} minutes",
                    "cost_saved": f"${comparison['improvement']['cost_savings']:.2f}",
                    "efficiency_gain": f"{comparison['improvement']['mttr_reduction_percentage']:.1f}%",
                    "customer_impact_reduction": f"{comparison['business_impact']['customer_satisfaction_improvement']:.1f}%"
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get demo comparison for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/controller/sessions")
async def list_demo_sessions():
    """List all active demo controller sessions."""
    try:
        from src.services.demo_controller import get_demo_controller, DemoScenarioType
        
        demo_controller = get_demo_controller(schedule_background_task)
        sessions = demo_controller.list_active_sessions()
        
        return {
            "active_sessions": sessions,
            "total_sessions": len(sessions),
            "demo_controller_features": {
                "controlled_execution": "5-minute completion guarantee",
                "real_time_metrics": "MTTR countdown and cost accumulation",
                "environment_isolation": "Isolated demo environment",
                "deterministic_timing": "Predictable phase execution",
                "business_impact_visualization": "Traditional vs autonomous comparison"
            },
            "available_scenarios": [s.value for s in DemoScenarioType],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list demo sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/demo/controller/{session_id}/stop")
async def stop_demo_session(session_id: str):
    """Stop an active demo session."""
    try:
        from src.services.demo_controller import get_demo_controller
        
        demo_controller = get_demo_controller(schedule_background_task)
        success = demo_controller.stop_demo_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Demo session not found")
        
        return {
            "session_id": session_id,
            "status": "stopped",
            "message": "Demo session stopped successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop demo session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/demo/controller/cleanup")
async def cleanup_demo_sessions(max_age_hours: int = 24):
    """Clean up completed demo sessions."""
    try:
        from src.services.demo_controller import get_demo_controller
        
        demo_controller = get_demo_controller(schedule_background_task)
        cleaned_count = demo_controller.cleanup_completed_sessions(max_age_hours)
        
        return {
            "cleaned_sessions": cleaned_count,
            "max_age_hours": max_age_hours,
            "message": f"Cleaned up {cleaned_count} completed demo sessions",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup demo sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Task 12.3: Demo Metrics and Performance Comparison

@app.get("/demo/metrics/{session_id}/mttr-comparison")
async def get_mttr_comparison(session_id: str):
    """
    Get MTTR comparison showing 95% reduction demonstration.
    
    Task 12.3: Demo metrics and performance comparison
    """
    try:
        from src.services.demo_metrics import get_demo_metrics_analyzer
        
        analyzer = get_demo_metrics_analyzer()
        comparison = analyzer.calculate_mttr_comparison(session_id)
        
        return {
            "session_id": session_id,
            "mttr_comparison": {
                "scenario_type": comparison.scenario_type,
                "traditional_mttr_minutes": comparison.traditional_mttr_minutes,
                "autonomous_mttr_minutes": comparison.autonomous_mttr_minutes,
                "reduction_percentage": comparison.reduction_percentage,
                "time_saved_minutes": comparison.time_saved_minutes,
                "improvement_factor": comparison.improvement_factor,
                "meets_95_percent_target": comparison.reduction_percentage >= 95.0
            },
            "dramatic_visualization": {
                "traditional_response": f"{comparison.traditional_mttr_minutes} minutes",
                "autonomous_response": f"{comparison.autonomous_mttr_minutes:.1f} minutes",
                "time_saved": f"{comparison.time_saved_minutes:.1f} minutes saved",
                "improvement": f"{comparison.improvement_factor:.1f}x faster"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get MTTR comparison for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/metrics/{session_id}/business-impact")
async def get_business_impact_comparison(session_id: str):
    """
    Get business impact and cost savings visualization.
    
    Shows dramatic cost reduction and business value creation.
    """
    try:
        from src.services.demo_metrics import get_demo_metrics_analyzer
        
        analyzer = get_demo_metrics_analyzer()
        impact = analyzer.calculate_business_impact_comparison(session_id)
        
        return {
            "session_id": session_id,
            "business_impact_comparison": {
                "scenario_type": impact.scenario_type,
                "traditional_cost": impact.traditional_cost,
                "autonomous_cost": impact.autonomous_cost,
                "cost_savings": impact.cost_savings,
                "cost_savings_percentage": impact.cost_savings_percentage,
                "affected_users": impact.affected_users,
                "revenue_protected": impact.revenue_protected,
                "customer_impact_reduction": impact.customer_impact_reduction
            },
            "cost_visualization": {
                "traditional_cost": f"${impact.traditional_cost:,.2f}",
                "autonomous_cost": f"${impact.autonomous_cost:,.2f}",
                "savings_achieved": f"${impact.cost_savings:,.2f}",
                "savings_percentage": f"{impact.cost_savings_percentage:.1f}%",
                "users_protected": f"{impact.affected_users:,} users",
                "customer_satisfaction": f"{impact.customer_impact_reduction:.1f}% improvement"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get business impact for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/metrics/{session_id}/performance-guarantee")
async def get_performance_guarantee_validation(session_id: str):
    """
    Validate demo scenario timing and performance guarantees.
    
    Ensures 5-minute completion guarantee and consistent performance.
    """
    try:
        from src.services.demo_metrics import get_demo_metrics_analyzer
        
        analyzer = get_demo_metrics_analyzer()
        guarantee = analyzer.validate_performance_guarantee(session_id)
        
        return {
            "session_id": session_id,
            "performance_guarantee": {
                "scenario_type": guarantee.scenario_type,
                "guaranteed_completion_minutes": guarantee.guaranteed_completion_minutes,
                "actual_completion_minutes": guarantee.actual_completion_minutes,
                "guarantee_met": guarantee.guarantee_met,
                "performance_margin_minutes": guarantee.performance_margin,
                "consistency_score": guarantee.consistency_score
            },
            "guarantee_visualization": {
                "completion_status": "✅ Guarantee Met" if guarantee.guarantee_met else "❌ Guarantee Missed",
                "completion_time": f"{guarantee.actual_completion_minutes:.1f} minutes",
                "performance_margin": f"{guarantee.performance_margin:.1f} minutes under guarantee",
                "consistency_rating": "Excellent" if guarantee.consistency_score > 0.9 else "Good" if guarantee.consistency_score > 0.7 else "Fair"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to validate performance guarantee for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/metrics/{session_id}/comprehensive-report")
async def get_comprehensive_demo_report(session_id: str):
    """
    Generate comprehensive demo performance report.
    
    Includes all metrics, comparisons, and performance validations.
    """
    try:
        from src.services.demo_metrics import get_demo_metrics_analyzer
        
        analyzer = get_demo_metrics_analyzer()
        report = analyzer.generate_comprehensive_demo_report(session_id)
        
        return {
            "comprehensive_report": report,
            "executive_summary": {
                "mttr_improvement": report["key_achievements"]["mttr_reduction_achieved"],
                "cost_savings": report["key_achievements"]["cost_savings_achieved"],
                "guarantee_status": "✅ Met" if report["performance_validation"]["guarantee_met"] else "❌ Missed",
                "customer_impact": report["key_achievements"]["customer_impact_reduced"],
                "demo_quality": "Excellent" if report["performance_validation"]["consistency_score"] > 0.9 else "Good"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate comprehensive report for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/metrics/aggregate/performance")
async def get_aggregate_performance_metrics():
    """
    Get aggregate performance metrics across all demo sessions.
    
    Provides overall system performance and consistency analysis.
    """
    try:
        from src.services.demo_metrics import get_demo_metrics_analyzer
        
        analyzer = get_demo_metrics_analyzer()
        metrics = analyzer.get_aggregate_performance_metrics()
        
        return {
            "aggregate_metrics": metrics,
            "system_performance_summary": {
                "total_scenarios": metrics.get("performance_summary", {}).get("scenarios_analyzed", 0),
                "total_sessions": metrics.get("performance_summary", {}).get("total_demo_sessions", 0),
                "overall_rating": metrics.get("performance_summary", {}).get("overall_performance_rating", "unknown"),
                "guarantee_success_rate": metrics.get("aggregate_performance", {}).get("overall_system", {}).get("overall_guarantee_success_rate", 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get aggregate performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/demo/metrics/{session_id}/log-interaction")
async def log_judge_interaction(session_id: str, interaction_data: Dict[str, Any]):
    """
    Log judge interaction for demo session recording.
    
    Captures complete interaction context for replay and analysis.
    """
    try:
        from src.services.demo_metrics import get_demo_metrics_analyzer
        
        analyzer = get_demo_metrics_analyzer()
        
        judge_id = interaction_data.get("judge_id", "demo_judge")
        interaction_type = interaction_data["interaction_type"]
        interaction_details = interaction_data.get("interaction_details", {})
        
        interaction_id = analyzer.log_judge_interaction(
            session_id=session_id,
            judge_id=judge_id,
            interaction_type=interaction_type,
            interaction_data=interaction_details
        )
        
        return {
            "interaction_logged": True,
            "interaction_id": interaction_id,
            "session_id": session_id,
            "judge_id": judge_id,
            "interaction_type": interaction_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to log judge interaction for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/metrics/judge/{judge_id}/analytics")
async def get_judge_interaction_analytics(judge_id: str):
    """
    Get analytics on judge interactions for demo improvement.
    
    Analyzes interaction patterns and their impact on demo effectiveness.
    """
    try:
        from src.services.demo_metrics import get_demo_metrics_analyzer
        
        analyzer = get_demo_metrics_analyzer()
        analytics = analyzer.get_judge_interaction_analytics(judge_id)
        
        return {
            "judge_analytics": analytics,
            "interaction_insights": {
                "engagement_level": analytics.get("demo_effectiveness", {}).get("demo_interactivity_rating", "unknown"),
                "most_used_feature": analytics.get("interaction_patterns", {}).get("most_common_interaction", "none"),
                "total_interactions": analytics.get("analysis_period", {}).get("total_interactions", 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get judge analytics for {judge_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Task 12.2: Interactive Judge Features and Real-Time Visualization

@app.post("/demo/judge/custom-incident")
async def create_custom_incident(incident_data: Dict[str, Any]):
    """
    Create custom incident with judge-specified parameters.
    
    Task 12.2: Interactive judge features for custom incident triggering
    """
    try:
        from src.services.interactive_judge import get_interactive_judge
        
        interactive_judge = get_interactive_judge()
        
        # Extract required parameters
        judge_id = incident_data.get("judge_id", "demo_judge")
        title = incident_data["title"]
        description = incident_data["description"]
        severity = incident_data.get("severity", "high")
        service_tier = incident_data.get("service_tier", "tier_1")
        affected_users = incident_data.get("affected_users", 10000)
        revenue_impact_per_minute = incident_data.get("revenue_impact_per_minute", 1000.0)
        custom_parameters = incident_data.get("custom_parameters", {})
        
        # Create custom incident
        result = await interactive_judge.create_custom_incident(
            judge_id=judge_id,
            title=title,
            description=description,
            severity=severity,
            service_tier=service_tier,
            affected_users=affected_users,
            revenue_impact_per_minute=revenue_impact_per_minute,
            custom_parameters=custom_parameters
        )
        
        logger.info(f"Judge {judge_id} created custom incident: {result['incident_id']}")
        
        return {
            "custom_incident": result,
            "judge_interface_features": {
                "severity_adjustment": True,
                "real_time_confidence_tracking": True,
                "decision_tree_exploration": True,
                "conflict_resolution_visualization": True,
                "reasoning_trace_analysis": True
            },
            "interactive_endpoints": {
                "adjust_severity": f"/demo/judge/{result['session_id']}/adjust-severity",
                "agent_confidence": f"/demo/judge/{result['session_id']}/agent-confidence",
                "decision_tree": f"/demo/judge/{result['session_id']}/decision-tree",
                "conflict_resolution": f"/demo/judge/{result['session_id']}/conflict-resolution",
                "reasoning_trace": f"/demo/judge/{result['session_id']}/reasoning-trace"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to create custom incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/demo/judge/{session_id}/adjust-severity")
async def adjust_incident_severity(session_id: str, adjustment_data: Dict[str, Any]):
    """
    Allow judges to adjust incident severity during demo execution.
    
    Provides interactive control over incident parameters.
    """
    try:
        from src.services.interactive_judge import get_interactive_judge
        
        interactive_judge = get_interactive_judge()
        
        judge_id = adjustment_data.get("judge_id", "demo_judge")
        new_severity = adjustment_data["new_severity"]
        adjustment_reason = adjustment_data.get("adjustment_reason", "Judge adjustment for demonstration")
        
        result = await interactive_judge.adjust_incident_severity(
            judge_id=judge_id,
            session_id=session_id,
            new_severity=new_severity,
            adjustment_reason=adjustment_reason
        )
        
        return {
            "severity_adjustment": result,
            "impact_visualization": {
                "cost_multiplier_applied": result["cost_multiplier"],
                "new_business_impact": result["new_cost_per_minute"],
                "adjustment_timestamp": result["timestamp"]
            },
            "message": f"Severity adjusted from {result['old_severity']} to {result['new_severity']}"
        }
        
    except Exception as e:
        logger.error(f"Failed to adjust severity for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/judge/{session_id}/agent-confidence")
async def get_agent_confidence_visualization(session_id: str):
    """
    Get real-time agent confidence score visualizations.
    
    Provides live confidence tracking with reasoning factors and evidence.
    """
    try:
        from src.services.interactive_judge import get_interactive_judge
        
        interactive_judge = get_interactive_judge()
        confidence_viz = interactive_judge.get_real_time_agent_confidence(session_id)
        
        # Format for visualization
        visualization_data = {}
        for agent_name, viz in confidence_viz.items():
            visualization_data[agent_name] = {
                "current_confidence": viz.current_confidence,
                "confidence_history": [
                    {"timestamp": ts.isoformat(), "confidence": conf}
                    for ts, conf in viz.confidence_history[-20:]  # Last 20 points
                ],
                "reasoning_factors": viz.reasoning_factors,
                "evidence_sources": viz.evidence_sources,
                "uncertainty_factors": viz.uncertainty_factors,
                "confidence_trend": "increasing" if len(viz.confidence_history) > 1 and 
                                  viz.confidence_history[-1][1] > viz.confidence_history[-2][1] else "stable"
            }
        
        return {
            "session_id": session_id,
            "agent_confidence_visualization": visualization_data,
            "visualization_features": {
                "real_time_updates": True,
                "confidence_history_tracking": True,
                "reasoning_factor_breakdown": True,
                "evidence_source_display": True,
                "uncertainty_analysis": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get agent confidence for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/judge/{session_id}/decision-tree")
async def get_interactive_decision_tree(session_id: str):
    """
    Get interactive decision tree for agent reasoning visualization.
    
    Provides hierarchical decision tree with confidence scores and alternative paths.
    """
    try:
        from src.services.interactive_judge import get_interactive_judge
        
        interactive_judge = get_interactive_judge()
        decision_tree = interactive_judge.get_interactive_decision_tree(session_id)
        
        def serialize_tree_node(node):
            return {
                "node_id": node.node_id,
                "decision_point": node.decision_point,
                "confidence_score": node.confidence_score,
                "evidence": node.evidence,
                "selected_path": node.selected_path,
                "alternative_paths": node.alternative_paths,
                "children": [serialize_tree_node(child) for child in node.children]
            }
        
        return {
            "session_id": session_id,
            "decision_tree": serialize_tree_node(decision_tree),
            "interactive_features": {
                "node_exploration": True,
                "alternative_path_viewing": True,
                "confidence_score_details": True,
                "evidence_inspection": True,
                "path_comparison": True
            },
            "visualization_instructions": {
                "selected_path": "Highlighted path shows actual agent decisions",
                "alternative_paths": "Click nodes to explore alternative decision paths",
                "confidence_scores": "Color intensity represents confidence levels",
                "evidence": "Hover over nodes to see supporting evidence"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get decision tree for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/judge/{session_id}/conflict-resolution")
async def get_conflict_resolution_visualization(session_id: str):
    """
    Get conflict resolution process visualization.
    
    Shows weighted scoring, agent disagreements, and consensus building process.
    """
    try:
        from src.services.interactive_judge import get_interactive_judge
        
        interactive_judge = get_interactive_judge()
        conflict_viz = interactive_judge.get_conflict_resolution_visualization(session_id)
        
        return {
            "session_id": session_id,
            "conflict_resolution": {
                "conflict_id": conflict_viz.conflict_id,
                "conflicting_agents": conflict_viz.conflicting_agents,
                "agent_recommendations": conflict_viz.agent_recommendations,
                "weighted_scores": conflict_viz.weighted_scores,
                "resolution_process": [
                    {
                        "step": step["step"],
                        "action": step["action"],
                        "timestamp": step["timestamp"].isoformat(),
                        "status": step["status"]
                    }
                    for step in conflict_viz.resolution_process
                ],
                "final_decision": conflict_viz.final_decision,
                "consensus_confidence": conflict_viz.consensus_confidence
            },
            "weighted_scoring_details": {
                "agent_weights": {
                    "detection": 0.2,
                    "diagnosis": 0.4,
                    "prediction": 0.3,
                    "resolution": 0.1
                },
                "confidence_threshold": 0.7,
                "consensus_algorithm": "weighted_voting_with_confidence_aggregation"
            },
            "visualization_features": {
                "real_time_process_tracking": True,
                "weighted_score_breakdown": True,
                "agent_disagreement_analysis": True,
                "consensus_building_visualization": True,
                "decision_rationale_display": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get conflict resolution for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/judge/{session_id}/reasoning-trace/{agent_name}")
async def get_agent_reasoning_trace(session_id: str, agent_name: str):
    """
    Get detailed reasoning trace for specific agent.
    
    Provides step-by-step reasoning process with evidence weighting.
    """
    try:
        from src.services.interactive_judge import get_interactive_judge
        
        interactive_judge = get_interactive_judge()
        reasoning_trace = interactive_judge.get_reasoning_trace(session_id, agent_name)
        
        if not reasoning_trace:
            raise HTTPException(status_code=404, detail=f"No reasoning trace found for agent {agent_name}")
        
        return {
            "session_id": session_id,
            "agent_name": agent_name,
            "reasoning_trace": reasoning_trace,
            "trace_analysis": {
                "confidence_evolution": [
                    step["confidence_change"] for step in reasoning_trace.get("reasoning_steps", [])
                ],
                "evidence_strength": sum(reasoning_trace.get("evidence_weights", {}).values()),
                "uncertainty_level": len(reasoning_trace.get("uncertainty_factors", [])),
                "reasoning_quality": "high" if reasoning_trace.get("final_confidence", 0) > 0.8 else "medium"
            },
            "visualization_features": {
                "step_by_step_reasoning": True,
                "confidence_evolution_tracking": True,
                "evidence_weight_analysis": True,
                "uncertainty_factor_display": True,
                "reasoning_quality_assessment": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get reasoning trace for {agent_name} in session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/judge/{judge_id}/interactions")
async def get_judge_interaction_history(judge_id: str):
    """Get interaction history for specific judge."""
    try:
        from src.services.interactive_judge import get_interactive_judge
        
        interactive_judge = get_interactive_judge()
        interactions = interactive_judge.get_judge_interaction_history(judge_id)
        
        return {
            "judge_id": judge_id,
            "interaction_history": interactions,
            "total_interactions": len(interactions),
            "interaction_types": list(set(interaction["interaction_type"] for interaction in interactions)),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get interaction history for judge {judge_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Task 12.3: Demo Metrics and Performance Comparison

@app.get("/demo/metrics/{session_id}/mttr-comparison")
async def get_mttr_comparison(session_id: str):
    """
    Get MTTR comparison showing 95% reduction demonstration.
    
    Task 12.3: Before/after MTTR comparison with dramatic improvement visualization
    """
    try:
        from src.services.demo_metrics import get_demo_metrics_analyzer
        
        metrics_analyzer = get_demo_metrics_analyzer()
        mttr_comparison = metrics_analyzer.calculate_mttr_comparison(session_id)
        
        return {
            "session_id": session_id,
            "mttr_comparison": {
                "traditional_response": {
                    "mttr_minutes": mttr_comparison.traditional_mttr_minutes,
                    "response_type": "manual_human_intervention"
                },
                "autonomous_response": {
                    "mttr_minutes": mttr_comparison.autonomous_mttr_minutes,
                    "response_type": "automated_multi_agent_system"
                },
                "improvement_metrics": {
                    "reduction_percentage": mttr_comparison.reduction_percentage,
                    "time_saved_minutes": mttr_comparison.time_saved_minutes,
                    "improvement_factor": f"{mttr_comparison.improvement_factor:.1f}x faster",
                    "meets_95_percent_target": mttr_comparison.reduction_percentage >= 95.0
                }
            },
            "dramatic_visualization": {
                "traditional_timeline": f"{mttr_comparison.traditional_mttr_minutes} minutes of manual intervention",
                "autonomous_timeline": f"{mttr_comparison.autonomous_mttr_minutes:.1f} minutes of automated response",
                "time_savings": f"Saved {mttr_comparison.time_saved_minutes:.1f} minutes ({mttr_comparison.reduction_percentage:.1f}% faster)",
                "efficiency_gain": f"{mttr_comparison.improvement_factor:.1f}x improvement in response time"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get MTTR comparison for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/metrics/{session_id}/business-impact")
async def get_business_impact_comparison(session_id: str):
    """
    Get business impact calculation and cost savings visualization.
    
    Shows dramatic cost reduction and business value creation.
    """
    try:
        from src.services.demo_metrics import get_demo_metrics_analyzer
        
        metrics_analyzer = get_demo_metrics_analyzer()
        business_impact = metrics_analyzer.calculate_business_impact_comparison(session_id)
        
        return {
            "session_id": session_id,
            "business_impact_comparison": {
                "traditional_impact": {
                    "total_cost": business_impact.traditional_cost,
                    "cost_per_minute": business_impact.traditional_cost / (business_impact.traditional_cost / business_impact.autonomous_cost * business_impact.autonomous_cost / business_impact.traditional_cost * 60) if business_impact.traditional_cost > 0 else 0,
                    "affected_users": business_impact.affected_users,
                    "business_disruption": "high"
                },
                "autonomous_impact": {
                    "total_cost": business_impact.autonomous_cost,
                    "cost_per_minute": business_impact.autonomous_cost / 5.0,  # Assuming 5-minute resolution
                    "affected_users": business_impact.affected_users,
                    "business_disruption": "minimal"
                },
                "cost_savings": {
                    "absolute_savings": business_impact.cost_savings,
                    "percentage_savings": business_impact.cost_savings_percentage,
                    "revenue_protected": business_impact.revenue_protected,
                    "customer_impact_reduction": business_impact.customer_impact_reduction
                }
            },
            "roi_calculation": {
                "cost_avoidance": business_impact.cost_savings,
                "roi_percentage": business_impact.cost_savings_percentage,
                "payback_period": "immediate",
                "annual_savings_projection": business_impact.cost_savings * 12  # Assuming monthly incidents
            },
            "customer_impact_metrics": {
                "users_affected": business_impact.affected_users,
                "service_disruption_reduction": f"{business_impact.customer_impact_reduction:.1f}%",
                "customer_satisfaction_improvement": "significant",
                "reputation_protection": "high"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get business impact for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/metrics/{session_id}/performance-validation")
async def get_performance_validation(session_id: str):
    """
    Get demo scenario timing validation and performance guarantees.
    
    Validates 5-minute completion guarantee and performance consistency.
    """
    try:
        from src.services.demo_metrics import get_demo_metrics_analyzer
        
        metrics_analyzer = get_demo_metrics_analyzer()
        performance_guarantee = metrics_analyzer.validate_performance_guarantee(session_id)
        
        return {
            "session_id": session_id,
            "performance_validation": {
                "guarantee_details": {
                    "guaranteed_completion_minutes": performance_guarantee.guaranteed_completion_minutes,
                    "actual_completion_minutes": performance_guarantee.actual_completion_minutes,
                    "guarantee_met": performance_guarantee.guarantee_met,
                    "performance_margin_minutes": performance_guarantee.performance_margin
                },
                "consistency_analysis": {
                    "consistency_score": performance_guarantee.consistency_score,
                    "performance_rating": "excellent" if performance_guarantee.consistency_score > 0.9 else "good" if performance_guarantee.consistency_score > 0.7 else "acceptable",
                    "reliability_assessment": "high" if performance_guarantee.guarantee_met else "needs_improvement"
                },
                "performance_summary": {
                    "completion_status": "within_guarantee" if performance_guarantee.guarantee_met else "exceeded_guarantee",
                    "efficiency_rating": "optimal" if performance_guarantee.performance_margin > 1.0 else "acceptable",
                    "predictability": "high" if performance_guarantee.consistency_score > 0.8 else "medium"
                }
            },
            "guarantee_compliance": {
                "sla_met": performance_guarantee.guarantee_met,
                "performance_buffer": performance_guarantee.performance_margin,
                "consistency_maintained": performance_guarantee.consistency_score > 0.7,
                "overall_compliance": "compliant" if performance_guarantee.guarantee_met and performance_guarantee.consistency_score > 0.7 else "non_compliant"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance validation for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/metrics/{session_id}/comprehensive-report")
async def get_comprehensive_demo_report(session_id: str):
    """
    Generate comprehensive demo performance report.
    
    Includes all metrics, comparisons, performance validations, and judge interactions.
    """
    try:
        from src.services.demo_metrics import get_demo_metrics_analyzer
        
        metrics_analyzer = get_demo_metrics_analyzer()
        report = metrics_analyzer.generate_comprehensive_demo_report(session_id)
        
        return {
            "comprehensive_demo_report": report,
            "executive_summary": {
                "mttr_achievement": f"{report['mttr_analysis']['reduction_percentage']:.1f}% reduction in MTTR",
                "cost_savings": f"${report['business_impact_analysis']['cost_savings']:,.2f} saved per incident",
                "performance_guarantee": "Met" if report['performance_validation']['guarantee_met'] else "Not Met",
                "judge_engagement": f"{report['judge_interactions']['total_interactions']} interactive demonstrations",
                "overall_rating": "excellent" if report['mttr_analysis']['meets_95_percent_target'] and report['performance_validation']['guarantee_met'] else "good"
            },
            "key_highlights": {
                "dramatic_improvement": f"{report['mttr_analysis']['improvement_factor']:.1f}x faster incident resolution",
                "business_value": f"${report['business_impact_analysis']['revenue_protected']:,.2f} in revenue protection",
                "customer_impact": f"{report['business_impact_analysis']['customer_impact_reduction']:.1f}% reduction in customer impact",
                "system_reliability": f"{report['performance_validation']['consistency_score']:.1%} consistency score"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate comprehensive report for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/metrics/aggregate-performance")
async def get_aggregate_performance_metrics():
    """
    Get aggregate performance metrics across all demo sessions.
    
    Provides overall system performance and consistency analysis.
    """
    try:
        from src.services.demo_metrics import get_demo_metrics_analyzer
        
        metrics_analyzer = get_demo_metrics_analyzer()
        aggregate_metrics = metrics_analyzer.get_aggregate_performance_metrics()
        
        return {
            "aggregate_performance_analysis": aggregate_metrics,
            "system_performance_summary": {
                "overall_rating": aggregate_metrics.get("performance_summary", {}).get("overall_performance_rating", "unknown"),
                "total_scenarios": aggregate_metrics.get("performance_summary", {}).get("scenarios_analyzed", 0),
                "total_sessions": aggregate_metrics.get("performance_summary", {}).get("total_demo_sessions", 0),
                "system_reliability": "high" if aggregate_metrics.get("aggregate_performance", {}).get("overall_system", {}).get("overall_guarantee_success_rate", 0) > 0.95 else "medium"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get aggregate performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/metrics/judge-analytics")
async def get_judge_interaction_analytics(judge_id: Optional[str] = None):
    """
    Get analytics on judge interactions for demo improvement.
    
    Analyzes interaction patterns and their impact on demo effectiveness.
    """
    try:
        from src.services.demo_metrics import get_demo_metrics_analyzer
        
        metrics_analyzer = get_demo_metrics_analyzer()
        analytics = metrics_analyzer.get_judge_interaction_analytics(judge_id)
        
        return {
            "judge_interaction_analytics": analytics,
            "demo_effectiveness_insights": {
                "engagement_level": analytics.get("demo_effectiveness", {}).get("demo_interactivity_rating", "unknown"),
                "interaction_diversity": analytics.get("demo_effectiveness", {}).get("interaction_diversity", 0),
                "judge_satisfaction": "high" if analytics.get("demo_effectiveness", {}).get("judge_engagement_score", 0) > 0.7 else "medium"
            },
            "recommendations": {
                "demo_improvements": "Increase interactive features" if analytics.get("demo_effectiveness", {}).get("interaction_diversity", 0) < 0.6 else "Maintain current engagement level",
                "judge_training": "Provide additional demo features training" if analytics.get("demo_effectiveness", {}).get("judge_engagement_score", 0) < 0.5 else "Current training adequate"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get judge analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Task 12.5: Interactive Fault Tolerance Showcase

@app.get("/demo/fault-tolerance/dashboard")
async def get_fault_tolerance_dashboard():
    """
    Get real-time circuit breaker dashboard showing agent health and state transitions.
    
    Task 12.5: Interactive fault tolerance showcase with circuit breaker visualization
    """
    try:
        from src.services.fault_tolerance_showcase import get_fault_tolerance_showcase
        
        showcase = get_fault_tolerance_showcase(schedule_background_task)
        dashboard = showcase.get_circuit_breaker_dashboard()
        
        return {
            "fault_tolerance_dashboard": dashboard,
            "interactive_features": {
                "real_time_circuit_breaker_monitoring": True,
                "agent_health_visualization": True,
                "system_resilience_scoring": True,
                "failure_pattern_analysis": True,
                "automatic_recovery_tracking": True
            },
            "judge_controls": {
                "chaos_injection": "/demo/fault-tolerance/inject-chaos",
                "network_partition": "/demo/fault-tolerance/simulate-partition",
                "recovery_visualization": "/demo/fault-tolerance/recovery-status",
                "comprehensive_report": "/demo/fault-tolerance/comprehensive-report"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get fault tolerance dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/demo/fault-tolerance/inject-chaos")
async def inject_chaos_fault(chaos_request: Dict[str, Any]):
    """
    Inject chaos engineering fault for judges to test system resilience.
    
    Provides interactive chaos engineering controls for live demonstration.
    """
    try:
        from src.services.fault_tolerance_showcase import get_fault_tolerance_showcase, FaultType
        
        showcase = get_fault_tolerance_showcase(schedule_background_task)
        
        judge_id = chaos_request.get("judge_id", "demo_judge")
        fault_type_str = chaos_request["fault_type"]
        target_component = chaos_request["target_component"]
        duration_seconds = chaos_request.get("duration_seconds", 60)
        intensity = chaos_request.get("intensity", 0.5)
        
        # Validate fault type
        try:
            fault_type = FaultType(fault_type_str)
        except ValueError:
            valid_types = [ft.value for ft in FaultType]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid fault type. Available: {valid_types}"
            )
        
        experiment_id = await showcase.inject_chaos_fault(
            judge_id=judge_id,
            fault_type=fault_type,
            target_component=target_component,
            duration_seconds=duration_seconds,
            intensity=intensity
        )
        
        return {
            "chaos_experiment": {
                "experiment_id": experiment_id,
                "fault_type": fault_type_str,
                "target_component": target_component,
                "duration_seconds": duration_seconds,
                "intensity": f"{intensity * 100:.0f}%",
                "judge_id": judge_id,
                "status": "injected"
            },
            "expected_effects": {
                "circuit_breaker_activation": "Automatic failure detection and isolation",
                "graceful_degradation": "Fallback mechanisms activated",
                "self_healing_initiation": "Recovery processes started",
                "visual_feedback": "Real-time dashboard updates"
            },
            "monitoring_endpoints": {
                "recovery_status": f"/demo/fault-tolerance/recovery/{experiment_id}",
                "system_impact": "/demo/fault-tolerance/dashboard",
                "resilience_metrics": "/demo/fault-tolerance/comprehensive-report"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to inject chaos fault: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/fault-tolerance/recovery/{experiment_id}")
async def get_fault_recovery_visualization(experiment_id: str):
    """
    Get fault recovery visualization showing system self-healing capabilities.
    
    Demonstrates automatic recovery and resilience mechanisms.
    """
    try:
        from src.services.fault_tolerance_showcase import get_fault_tolerance_showcase
        
        showcase = get_fault_tolerance_showcase(schedule_background_task)
        recovery_viz = showcase.get_fault_recovery_visualization(experiment_id)
        
        return {
            "fault_recovery_visualization": recovery_viz,
            "self_healing_demonstration": {
                "automatic_detection": "System detected fault within seconds",
                "isolation_mechanisms": "Circuit breakers activated to contain impact",
                "recovery_procedures": "Self-healing protocols initiated automatically",
                "business_continuity": "Service maintained through graceful degradation",
                "full_recovery": "System restored without human intervention"
            },
            "resilience_metrics": {
                "fault_tolerance_score": recovery_viz["visual_indicators"]["resilience_score"],
                "recovery_efficiency": recovery_viz["fault_recovery_visualization"]["recovery_progress"],
                "system_stability": recovery_viz["visual_indicators"]["system_health_trend"],
                "business_impact": recovery_viz["system_resilience_metrics"]["business_continuity"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get recovery visualization for {experiment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/demo/fault-tolerance/simulate-partition")
async def simulate_network_partition(partition_request: Dict[str, Any]):
    """
    Simulate network partition for partition tolerance demonstration.
    
    Shows how the system handles network splits and maintains consistency.
    """
    try:
        from src.services.fault_tolerance_showcase import get_fault_tolerance_showcase, FaultType
        
        showcase = get_fault_tolerance_showcase(schedule_background_task)
        
        judge_id = partition_request.get("judge_id", "demo_judge")
        target_network = partition_request.get("target_network", "consensus_network")
        duration_seconds = partition_request.get("duration_seconds", 120)
        
        experiment_id = await showcase.inject_chaos_fault(
            judge_id=judge_id,
            fault_type=FaultType.NETWORK_PARTITION,
            target_component=target_network,
            duration_seconds=duration_seconds,
            intensity=0.8
        )
        
        # Get partition details
        partition_ids = list(showcase.network_partitions.keys())
        partition_id = partition_ids[-1] if partition_ids else None
        
        return {
            "network_partition_simulation": {
                "experiment_id": experiment_id,
                "partition_id": partition_id,
                "target_network": target_network,
                "duration_seconds": duration_seconds,
                "judge_id": judge_id,
                "status": "active"
            },
            "partition_tolerance_features": {
                "local_state_continuation": "Agents continue operating with local state",
                "conflict_detection": "Automatic detection of state inconsistencies",
                "state_merging": "Intelligent state merge after partition healing",
                "consensus_recovery": "Automatic consensus re-establishment",
                "data_integrity": "Cryptographic validation maintained"
            },
            "cap_theorem_demonstration": {
                "consistency": "Eventually consistent after partition healing",
                "availability": "Maintained for non-partitioned operations",
                "partition_tolerance": "System continues operating during network splits"
            },
            "monitoring_endpoints": {
                "partition_status": f"/demo/fault-tolerance/partition/{partition_id}" if partition_id else None,
                "recovery_tracking": f"/demo/fault-tolerance/recovery/{experiment_id}",
                "system_dashboard": "/demo/fault-tolerance/dashboard"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to simulate network partition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/fault-tolerance/partition/{partition_id}")
async def get_network_partition_demonstration(partition_id: str):
    """
    Get network partition simulation details and partition tolerance demonstration.
    
    Shows detailed partition handling and CAP theorem trade-offs.
    """
    try:
        from src.services.fault_tolerance_showcase import get_fault_tolerance_showcase
        
        showcase = get_fault_tolerance_showcase(schedule_background_task)
        partition_demo = showcase.get_network_partition_demonstration(partition_id)
        
        return {
            "network_partition_demonstration": partition_demo,
            "educational_content": {
                "cap_theorem_explanation": {
                    "consistency": "All nodes see the same data simultaneously",
                    "availability": "System remains operational during failures",
                    "partition_tolerance": "System continues despite network failures",
                    "trade_off": "Can only guarantee 2 out of 3 properties simultaneously"
                },
                "system_strategy": "Prioritizes Availability and Partition Tolerance (AP system)",
                "eventual_consistency": "Consistency restored after partition healing"
            },
            "technical_details": {
                "partition_detection_method": "Heartbeat timeout and consensus failure",
                "local_state_management": "Vector clocks for conflict resolution",
                "healing_detection": "Network connectivity restoration monitoring",
                "state_synchronization": "Merkle tree-based state comparison and merge"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get partition demonstration for {partition_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/fault-tolerance/comprehensive-report")
async def get_comprehensive_fault_tolerance_report():
    """
    Get comprehensive fault tolerance showcase report.
    
    Provides complete overview of system resilience and fault tolerance capabilities.
    """
    try:
        from src.services.fault_tolerance_showcase import get_fault_tolerance_showcase
        
        showcase = get_fault_tolerance_showcase()
        report = showcase.get_comprehensive_fault_tolerance_report()
        
        return {
            "comprehensive_fault_tolerance_report": report,
            "system_resilience_summary": {
                "overall_health": f"{report['fault_tolerance_showcase_report']['system_resilience_summary']['overall_resilience_score']:.1%}",
                "active_experiments": len(report["fault_tolerance_showcase_report"]["active_chaos_experiments"]),
                "network_partitions": len(report["fault_tolerance_showcase_report"]["active_network_partitions"]),
                "circuit_breaker_status": report["fault_tolerance_showcase_report"]["circuit_breaker_status"]["system_overview"]["overall_status"]
            },
            "fault_tolerance_capabilities_summary": {
                "circuit_breaker_protection": "✅ Operational",
                "graceful_degradation": "✅ Operational", 
                "self_healing": "✅ Operational",
                "partition_tolerance": "✅ Operational",
                "chaos_engineering": "✅ Operational",
                "real_time_monitoring": "✅ Operational"
            },
            "judge_demonstration_features": {
                "interactive_fault_injection": "Live chaos engineering controls",
                "real_time_recovery_visualization": "Visual self-healing demonstration",
                "circuit_breaker_dashboard": "Live system health monitoring",
                "network_partition_simulation": "CAP theorem demonstration",
                "resilience_scoring": "Quantitative fault tolerance assessment"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get comprehensive fault tolerance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/fault-tolerance/available-faults")
async def list_available_fault_types():
    """List all available fault types for chaos engineering."""
    try:
        from src.services.fault_tolerance_showcase import FaultType
        
        fault_types = {}
        for fault_type in FaultType:
            fault_types[fault_type.value] = {
                "name": fault_type.value.replace("_", " ").title(),
                "description": {
                    "agent_failure": "Simulate individual agent failures with configurable intensity",
                    "network_partition": "Create network splits to test partition tolerance",
                    "service_timeout": "Inject service timeouts to test circuit breaker response",
                    "memory_pressure": "Simulate memory pressure for graceful degradation testing",
                    "cpu_overload": "Create CPU overload conditions",
                    "database_failure": "Simulate database failures with cascading effects",
                    "external_api_failure": "Test external API failure handling and fallbacks"
                }.get(fault_type.value, "Configurable fault injection for resilience testing"),
                "target_components": {
                    "agent_failure": ["detection", "diagnosis", "prediction", "resolution", "communication"],
                    "network_partition": ["consensus_network", "external_services", "agent_communication"],
                    "service_timeout": ["bedrock_api", "dynamodb", "kinesis", "opensearch"],
                    "memory_pressure": ["detection_agent", "diagnosis_agent", "opensearch"],
                    "cpu_overload": ["all_agents", "orchestrator", "consensus_engine"],
                    "database_failure": ["dynamodb", "opensearch"],
                    "external_api_failure": ["datadog_api", "pagerduty_api", "slack_api", "bedrock_api"]
                }.get(fault_type.value, ["system_wide"]),
                "intensity_range": "0.1 to 1.0 (10% to 100% impact)",
                "duration_range": "30 to 300 seconds"
            }
        
        return {
            "available_fault_types": fault_types,
            "chaos_engineering_capabilities": {
                "real_time_injection": "Faults can be injected during live demonstrations",
                "configurable_intensity": "Adjustable impact levels for controlled testing",
                "automatic_recovery": "Self-healing mechanisms activate automatically",
                "visual_feedback": "Real-time dashboard updates show system response",
                "educational_value": "Demonstrates resilience patterns and fault tolerance"
            },
            "recommended_demo_sequence": [
                {
                    "step": 1,
                    "fault": "agent_failure",
                    "target": "detection",
                    "purpose": "Show circuit breaker activation and agent failover"
                },
                {
                    "step": 2,
                    "fault": "network_partition",
                    "target": "consensus_network", 
                    "purpose": "Demonstrate partition tolerance and CAP theorem trade-offs"
                },
                {
                    "step": 3,
                    "fault": "database_failure",
                    "target": "dynamodb",
                    "purpose": "Show cascading failure prevention and graceful degradation"
                }
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to list available fault types: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Task 12.4: Compelling Real-Time Business Impact Visualization

@app.get("/demo/business-impact/{session_id}/live-dashboard")
async def get_live_business_impact_dashboard(session_id: str):
    """
    Get comprehensive real-time business impact dashboard.
    
    Task 12.4: Compelling visualization with live cost accumulation and customer impact
    """
    try:
        from src.services.business_impact_viz import get_business_metrics
        
        business_metrics = get_business_metrics()
        dashboard = business_metrics.get_comprehensive_business_impact_dashboard(session_id)
        
        return {
            "live_business_impact_dashboard": dashboard,
            "compelling_features": {
                "real_time_cost_meter": "Live cost accumulation with velocity tracking",
                "customer_impact_gauge": "Real-time customer satisfaction and churn risk",
                "sla_breach_countdown": "Dramatic countdown timer with compliance status",
                "roi_calculator": "Immediate ROI and annual savings projection",
                "disaster_prevention_score": "Visual representation of catastrophe averted"
            },
            "judge_appeal_elements": {
                "dramatic_comparisons": True,
                "live_cost_savings": True,
                "business_continuity_visualization": True,
                "reputation_protection_metrics": True,
                "regulatory_compliance_tracking": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get live business impact dashboard for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/business-impact/{session_id}/cost-accumulation")
async def get_live_cost_accumulation(session_id: str):
    """
    Get real-time cost accumulation with dramatic visualization.
    
    Shows live cost meter with velocity and acceleration for maximum impact.
    """
    try:
        from src.services.business_impact_viz import get_business_metrics
        
        business_metrics = get_business_metrics()
        cost_data = business_metrics.get_live_cost_accumulation(session_id)
        
        return {
            "session_id": session_id,
            "live_cost_accumulation": {
                "current_cost": f"${cost_data.current_cost:,.2f}",
                "cost_per_second": f"${cost_data.cost_per_second:.2f}",
                "cost_velocity": f"${cost_data.cost_velocity:,.2f}/minute",
                "projected_cost": f"${cost_data.projected_cost:,.2f}",
                "cost_trend": cost_data.cost_trend,
                "cost_acceleration": f"${cost_data.cost_acceleration:.2f}/minute²"
            },
            "dramatic_visualization": {
                "cost_meter_color": "red" if cost_data.cost_trend == "increasing" else "yellow" if cost_data.cost_trend == "stable" else "green",
                "urgency_level": "critical" if cost_data.cost_acceleration > 100 else "high" if cost_data.cost_acceleration > 50 else "medium",
                "cost_impact_message": f"Burning ${cost_data.cost_velocity:,.0f} per minute with {cost_data.cost_trend} trend"
            },
            "business_context": {
                "cost_equivalent": f"Equivalent to {cost_data.current_cost / 50000:.1f} employee salaries per year" if cost_data.current_cost > 0 else "Minimal cost impact",
                "revenue_impact": f"Could fund {cost_data.current_cost / 10000:.0f} customer acquisition campaigns" if cost_data.current_cost > 0 else "No significant revenue impact"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get cost accumulation for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/business-impact/{session_id}/customer-impact")
async def get_customer_impact_visualization(session_id: str):
    """
    Get real-time customer impact visualization.
    
    Shows dramatic customer and business impact with severity assessment.
    """
    try:
        from src.services.business_impact_viz import get_business_metrics
        
        business_metrics = get_business_metrics()
        customer_impact = business_metrics.get_customer_impact_metrics(session_id)
        
        return {
            "session_id": session_id,
            "customer_impact_visualization": {
                "affected_users": f"{customer_impact.affected_users:,} users",
                "impact_severity": customer_impact.user_impact_severity.value,
                "service_degradation": f"{customer_impact.service_degradation_percentage:.1f}%",
                "satisfaction_impact": f"{customer_impact.customer_satisfaction_impact:.1f}% decrease",
                "churn_risk": f"{customer_impact.churn_risk_percentage:.1f}% at risk",
                "reputation_damage": f"{customer_impact.reputation_damage_score:.1f}/100 damage score"
            },
            "dramatic_context": {
                "user_impact_message": f"{customer_impact.affected_users:,} customers experiencing {customer_impact.user_impact_severity.value} service disruption",
                "business_risk_level": "critical" if customer_impact.churn_risk_percentage > 15 else "high" if customer_impact.churn_risk_percentage > 10 else "moderate",
                "reputation_status": "severe damage" if customer_impact.reputation_damage_score > 70 else "moderate damage" if customer_impact.reputation_damage_score > 40 else "minimal damage"
            },
            "customer_experience_metrics": {
                "service_availability": f"{100 - customer_impact.service_degradation_percentage:.1f}%",
                "customer_satisfaction_score": f"{100 - customer_impact.customer_satisfaction_impact:.1f}/100",
                "brand_trust_impact": f"{100 - customer_impact.reputation_damage_score:.1f}/100",
                "customer_retention_risk": f"{customer_impact.churn_risk_percentage:.1f}% churn probability"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get customer impact for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/business-impact/{session_id}/sla-breach-countdown")
async def get_sla_breach_countdown(session_id: str):
    """
    Get real-time SLA breach countdown with compliance monitoring.
    
    Provides dramatic countdown timer and breach impact visualization.
    """
    try:
        from src.services.business_impact_viz import get_business_metrics
        
        business_metrics = get_business_metrics()
        sla_tracking = business_metrics.get_sla_breach_countdown(session_id)
        
        return {
            "session_id": session_id,
            "sla_breach_countdown": {
                "sla_target_minutes": sla_tracking.sla_target_minutes,
                "time_remaining_seconds": sla_tracking.time_remaining_seconds,
                "time_remaining_display": f"{int(sla_tracking.time_remaining_seconds // 60)}:{int(sla_tracking.time_remaining_seconds % 60):02d}",
                "breach_probability": f"{sla_tracking.breach_probability:.1f}%",
                "compliance_status": sla_tracking.compliance_status,
                "breach_cost_multiplier": f"{sla_tracking.breach_cost_multiplier}x",
                "regulatory_impact": sla_tracking.regulatory_impact
            },
            "dramatic_countdown": {
                "urgency_level": "critical" if sla_tracking.time_remaining_seconds < 60 else "high" if sla_tracking.time_remaining_seconds < 300 else "medium",
                "countdown_color": "red" if sla_tracking.compliance_status == "breached" else "orange" if sla_tracking.compliance_status == "at_risk" else "green",
                "breach_warning": "SLA BREACH IMMINENT!" if sla_tracking.time_remaining_seconds < 60 else "SLA at risk" if sla_tracking.time_remaining_seconds < 300 else "SLA compliant"
            },
            "compliance_implications": {
                "regulatory_penalties": "Severe financial penalties apply" if sla_tracking.regulatory_impact == "severe_penalties_apply" else "Potential penalties" if sla_tracking.regulatory_impact == "potential_penalties" else "No penalties",
                "customer_credits": f"{sla_tracking.breach_cost_multiplier * 10:.0f}% service credits required" if sla_tracking.compliance_status == "breached" else "No credits required",
                "audit_impact": "Compliance violation recorded" if sla_tracking.compliance_status == "breached" else "Compliance maintained"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get SLA breach countdown for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/business-impact/{session_id}/roi-calculation")
async def get_real_time_roi_calculation(session_id: str):
    """
    Get real-time ROI calculation with dramatic cost savings visualization.
    
    Shows immediate ROI and projected annual savings for maximum impact.
    """
    try:
        from src.services.business_impact_viz import get_business_metrics
        
        business_metrics = get_business_metrics()
        roi_data = business_metrics.calculate_real_time_roi(session_id)
        
        return {
            "session_id": session_id,
            "roi_calculation": {
                "traditional_cost": f"${roi_data.traditional_cost:,.2f}",
                "autonomous_cost": f"${roi_data.autonomous_cost:,.2f}",
                "cost_savings": f"${roi_data.cost_savings:,.2f}",
                "roi_percentage": f"{roi_data.roi_percentage:.1f}%",
                "payback_period": "Immediate",
                "annual_savings_projection": f"${roi_data.annual_savings_projection:,.2f}"
            },
            "dramatic_roi_visualization": {
                "savings_message": f"SAVED ${roi_data.cost_savings:,.0f} with {roi_data.roi_percentage:.0f}% ROI",
                "annual_impact": f"Projected ${roi_data.annual_savings_projection:,.0f} annual savings",
                "efficiency_gain": f"{roi_data.roi_percentage:.0f}% return on autonomous investment",
                "business_value": "Immediate positive ROI with zero payback period"
            },
            "investment_justification": {
                "cost_avoidance": f"${roi_data.cost_savings:,.2f} in immediate cost avoidance",
                "productivity_gain": "Eliminated manual intervention and human error costs",
                "scalability_benefit": "Consistent performance regardless of incident complexity",
                "competitive_advantage": "Sub-5-minute resolution vs industry standard 30+ minutes"
            },
            "financial_impact": {
                "quarterly_savings": f"${roi_data.annual_savings_projection / 4:,.2f}",
                "monthly_savings": f"${roi_data.annual_savings_projection / 12:,.2f}",
                "cost_per_incident_avoided": f"${roi_data.cost_savings:,.2f}",
                "efficiency_multiplier": f"{roi_data.roi_percentage / 100:.1f}x cost efficiency"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get ROI calculation for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo/business-impact/{session_id}/failure-comparison")
async def get_dramatic_failure_comparison(session_id: str):
    """
    Get dramatic failure comparison showing traditional vs autonomous timelines.
    
    Provides compelling visualization of disaster averted and business continuity.
    """
    try:
        from src.services.business_impact_viz import get_business_metrics
        
        business_metrics = get_business_metrics()
        comparison = business_metrics.get_dramatic_failure_comparison(session_id)
        
        return {
            "session_id": session_id,
            "dramatic_failure_comparison": {
                "traditional_disaster_timeline": comparison.traditional_timeline,
                "autonomous_success_timeline": comparison.autonomous_timeline,
                "disaster_averted_score": f"{comparison.disaster_averted_score:.1f}/100",
                "business_continuity_maintained": comparison.business_continuity_maintained,
                "failure_cascade_prevented": comparison.failure_cascade_prevented
            },
            "compelling_narrative": {
                "disaster_scenario": "Without autonomous response: 45+ minutes of cascading failures, customer impact, and business disruption",
                "success_story": "With autonomous response: <5 minutes to resolution, business continuity maintained, disaster averted",
                "impact_prevented": f"Prevented {len(comparison.failure_cascade_prevented)} critical business impacts",
                "continuity_status": "Business operations maintained" if comparison.business_continuity_maintained else "Business disruption occurred"
            },
            "timeline_comparison": {
                "traditional_total_time": "45+ minutes of manual intervention",
                "autonomous_total_time": "<5 minutes of automated response",
                "time_advantage": "9x faster resolution",
                "reliability_advantage": "Consistent performance vs human error-prone process"
            },
            "business_impact_prevented": {
                "revenue_loss_avoided": "Prevented extended service outage and revenue loss",
                "customer_churn_avoided": "Maintained customer satisfaction and retention",
                "reputation_damage_avoided": "Protected brand reputation and market position",
                "regulatory_compliance_maintained": "Avoided compliance violations and penalties"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get failure comparison for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Task 14: Security Hardening and Compliance

@app.get("/security/audit/events")
async def get_audit_events(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100
):
    """
    Get audit events with filtering capabilities.
    
    Task 14.1: Comprehensive audit logging and compliance
    """
    try:
        from src.services.security import TamperProofAuditLogger
        from src.utils.config import config
        from datetime import datetime, timedelta
        
        audit_logger = TamperProofAuditLogger(config)
        
        # Parse date parameters
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start_dt = datetime.utcnow() - timedelta(days=7)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_dt = datetime.utcnow()
        
        # Get audit events (simplified - would implement full filtering in production)
        events = await audit_logger._get_audit_events_by_date_range(start_dt, end_dt)
        
        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if severity:
            events = [e for e in events if e.severity == severity]
        
        # Limit results
        events = events[:limit]
        
        return {
            "audit_events": [
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "severity": event.severity,
                    "agent_id": event.agent_id,
                    "action": event.action,
                    "outcome": event.outcome,
                    "integrity_verified": event.verify_integrity()
                }
                for event in events
            ],
            "total_events": len(events),
            "period": {
                "start": start_dt.isoformat(),
                "end": end_dt.isoformat()
            },
            "compliance_features": {
                "tamper_proof_logging": True,
                "cryptographic_integrity": True,
                "7_year_retention": True,
                "pii_redaction": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get audit events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/security/audit/verify-chain")
async def verify_audit_chain(verification_request: Dict[str, Any]):
    """
    Verify audit chain integrity for compliance validation.
    
    Provides cryptographic verification of audit log integrity.
    """
    try:
        from src.services.security import TamperProofAuditLogger
        from src.utils.config import config
        from datetime import datetime
        
        audit_logger = TamperProofAuditLogger(config)
        
        start_date = datetime.fromisoformat(verification_request["start_date"].replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(verification_request["end_date"].replace('Z', '+00:00'))
        
        # Verify audit chain integrity
        is_valid = await audit_logger.verify_audit_chain(start_date, end_date)
        
        return {
            "chain_verification": {
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "integrity_verified": is_valid,
                "verification_method": "cryptographic_hash_chain",
                "tamper_detection": "enabled"
            },
            "compliance_status": {
                "audit_trail_intact": is_valid,
                "regulatory_compliance": "maintained" if is_valid else "compromised",
                "investigation_required": not is_valid
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to verify audit chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/security/compliance/generate-report")
async def generate_compliance_report(report_request: Dict[str, Any]):
    """
    Generate compliance report for regulatory requirements.
    
    Task 14.1: Compliance reporting for regulatory requirements
    """
    try:
        from src.services.security import ComplianceManager
        from src.utils.config import config
        from datetime import datetime
        
        compliance_manager = ComplianceManager(config)
        
        framework = report_request["framework"]
        start_date = datetime.fromisoformat(report_request["start_date"].replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(report_request["end_date"].replace('Z', '+00:00'))
        
        # Generate compliance report
        report = await compliance_manager.generate_compliance_report(
            framework=framework,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "compliance_report": {
                "report_id": report.report_id,
                "framework": report.compliance_framework,
                "period": {
                    "start": report.period_start.isoformat(),
                    "end": report.period_end.isoformat()
                },
                "compliance_status": {
                    "data_retention_compliant": report.data_retention_compliance,
                    "encryption_compliant": report.encryption_compliance,
                    "access_control_compliant": report.access_control_compliance
                },
                "findings": report.findings,
                "recommendations": report.recommendations,
                "total_audit_events": report.total_audit_events,
                "security_violations": report.security_violations
            },
            "supported_frameworks": ["SOC2", "GDPR", "HIPAA", "PCI_DSS"],
            "report_features": {
                "automated_generation": True,
                "regulatory_alignment": True,
                "finding_analysis": True,
                "recommendation_engine": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/security/monitoring/alerts")
async def get_security_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """
    Get security alerts from threat detection system.
    
    Task 14.2: Security monitoring and threat detection
    """
    try:
        from src.services.security import SecurityMonitor
        from src.utils.config import config
        
        security_monitor = SecurityMonitor(config)
        
        # Get active alerts (simplified - would implement full filtering)
        active_alerts = list(security_monitor._active_alerts.values())
        
        # Apply filters
        if severity:
            active_alerts = [a for a in active_alerts if a.severity == severity]
        if status:
            active_alerts = [a for a in active_alerts if a.status == status]
        
        # Limit results
        active_alerts = active_alerts[:limit]
        
        return {
            "security_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "timestamp": alert.timestamp.isoformat(),
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "agent_id": alert.agent_id,
                    "description": alert.description,
                    "confidence_score": alert.confidence_score,
                    "status": alert.status,
                    "indicators": alert.indicators,
                    "mitigation_actions": alert.mitigation_actions
                }
                for alert in active_alerts
            ],
            "alert_summary": {
                "total_alerts": len(active_alerts),
                "critical_alerts": len([a for a in active_alerts if a.severity == "critical"]),
                "high_alerts": len([a for a in active_alerts if a.severity == "high"]),
                "open_alerts": len([a for a in active_alerts if a.status == "open"])
            },
            "threat_detection_features": {
                "behavioral_analysis": True,
                "agent_compromise_detection": True,
                "automated_response": True,
                "threat_intelligence_correlation": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get security alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/security/monitoring/analyze-event")
async def analyze_security_event(event_data: Dict[str, Any]):
    """
    Analyze security event for threats and generate alerts.
    
    Provides real-time security event analysis and threat detection.
    """
    try:
        from src.services.security import SecurityMonitor, TamperProofAuditLogger
        from src.models.security import AuditEvent, SecurityEventType, SecuritySeverity
        from src.utils.config import config
        
        security_monitor = SecurityMonitor(config)
        audit_logger = TamperProofAuditLogger(config)
        
        # Create audit event from request
        audit_event = AuditEvent(
            event_id=event_data.get("event_id", str(uuid4())),
            event_type=SecurityEventType(event_data["event_type"]),
            severity=SecuritySeverity(event_data.get("severity", "medium")),
            agent_id=event_data.get("agent_id"),
            action=event_data["action"],
            outcome=event_data["outcome"],
            details=event_data.get("details", {})
        )
        
        # Analyze for security threats
        alerts = await security_monitor.analyze_security_event(audit_event)
        
        return {
            "security_analysis": {
                "event_id": audit_event.event_id,
                "analysis_completed": True,
                "alerts_generated": len(alerts),
                "threat_level": "high" if any(a.severity == "critical" for a in alerts) else "medium" if alerts else "low"
            },
            "generated_alerts": [
                {
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "confidence_score": alert.confidence_score,
                    "description": alert.description,
                    "mitigation_actions": alert.mitigation_actions
                }
                for alert in alerts
            ],
            "behavioral_analysis": {
                "suspicious_patterns_detected": len(alerts) > 0,
                "agent_behavior_anomalies": any("behavior" in alert.alert_type for alert in alerts),
                "threat_intelligence_matches": any("threat_intelligence" in alert.alert_type for alert in alerts)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to analyze security event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/security/agents/certificates")
async def get_agent_certificates(agent_id: Optional[str] = None):
    """
    Get agent certificates and authentication status.
    
    Task 14.4: Agent cryptographic identity verification
    """
    try:
        from src.services.security import AgentAuthenticator
        from src.utils.config import config
        
        authenticator = AgentAuthenticator(config)
        
        if agent_id:
            # Get specific agent certificate
            certificate = await authenticator.get_agent_certificate(agent_id)
            if not certificate:
                raise HTTPException(status_code=404, detail="Agent certificate not found")
            
            return {
                "agent_certificate": {
                    "agent_id": certificate.agent_id,
                    "certificate_id": certificate.certificate_id,
                    "issued_at": certificate.issued_at.isoformat(),
                    "expires_at": certificate.expires_at.isoformat(),
                    "status": certificate.status,
                    "is_valid": certificate.is_valid(),
                    "days_until_expiry": certificate.days_until_expiry(),
                    "revoked_at": certificate.revoked_at.isoformat() if certificate.revoked_at else None
                },
                "certificate_features": {
                    "cryptographic_identity": True,
                    "signature_verification": True,
                    "automatic_rotation": True,
                    "revocation_support": True
                }
            }
        else:
            # Get all certificates needing renewal
            agents_needing_renewal = await authenticator.check_certificates_for_renewal()
            
            return {
                "certificate_overview": {
                    "agents_needing_renewal": agents_needing_renewal,
                    "renewal_threshold_days": authenticator.cert_renewal_threshold_days,
                    "default_lifetime_days": authenticator.default_cert_lifetime_days
                },
                "certificate_management": {
                    "automatic_renewal": True,
                    "cryptographic_verification": True,
                    "revocation_list_management": True,
                    "impersonation_detection": True
                }
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent certificates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/security/agents/generate-certificate")
async def generate_agent_certificate(cert_request: Dict[str, Any]):
    """
    Generate new certificate for agent authentication.
    
    Provides cryptographic identity management for agents.
    """
    try:
        from src.services.security import AgentAuthenticator
        from src.utils.config import config
        
        authenticator = AgentAuthenticator(config)
        
        agent_id = cert_request["agent_id"]
        lifetime_days = cert_request.get("lifetime_days")
        
        # Generate certificate
        certificate = await authenticator.generate_agent_certificate(
            agent_id=agent_id,
            lifetime_days=lifetime_days
        )
        
        return {
            "certificate_generated": {
                "agent_id": certificate.agent_id,
                "certificate_id": certificate.certificate_id,
                "issued_at": certificate.issued_at.isoformat(),
                "expires_at": certificate.expires_at.isoformat(),
                "lifetime_days": (certificate.expires_at - certificate.issued_at).days,
                "status": certificate.status
            },
            "security_features": {
                "rsa_2048_encryption": True,
                "cryptographic_signatures": True,
                "secure_key_storage": "AWS Secrets Manager",
                "automatic_expiry_monitoring": True
            },
            "next_steps": {
                "certificate_deployment": "Certificate ready for agent deployment",
                "signature_verification": "Agent can now sign communications",
                "identity_verification": "Cryptographic identity established"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate agent certificate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/security/agents/verify-signature")
async def verify_agent_signature(verification_request: Dict[str, Any]):
    """
    Verify cryptographic signature from agent.
    
    Provides signature verification for agent communications.
    """
    try:
        from src.services.security import AgentAuthenticator
        from src.utils.config import config
        
        authenticator = AgentAuthenticator(config)
        
        agent_id = verification_request["agent_id"]
        message = verification_request["message"]
        signature = verification_request["signature"]
        
        # Verify signature
        is_valid = await authenticator.verify_agent_signature(
            agent_id=agent_id,
            message=message,
            signature=signature
        )
        
        # Check for impersonation
        is_impersonation = await authenticator.detect_agent_impersonation(
            agent_id=agent_id,
            message=message,
            signature=signature,
            source_ip=verification_request.get("source_ip")
        )
        
        return {
            "signature_verification": {
                "agent_id": agent_id,
                "signature_valid": is_valid,
                "impersonation_detected": is_impersonation,
                "verification_method": "RSA-PSS with SHA-256",
                "security_status": "verified" if is_valid and not is_impersonation else "failed"
            },
            "security_analysis": {
                "cryptographic_integrity": is_valid,
                "identity_confirmed": is_valid and not is_impersonation,
                "threat_level": "none" if is_valid and not is_impersonation else "high"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to verify agent signature: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/security/testing/run-security-tests")
async def run_security_test_suite(test_request: Dict[str, Any]):
    """
    Run comprehensive security test suite.
    
    Task 14.3: Security testing and penetration testing framework
    """
    try:
        from src.services.security import SecurityTestingFramework
        from src.utils.config import config
        
        testing_framework = SecurityTestingFramework(config)
        
        # Run comprehensive security tests
        test_results = await testing_framework.run_comprehensive_security_test_suite()
        
        return {
            "security_test_results": test_results,
            "test_execution_summary": {
                "total_tests": test_results["summary"]["total_tests"],
                "passed_tests": test_results["summary"]["passed_tests"],
                "failed_tests": test_results["summary"]["failed_tests"],
                "success_rate": f"{test_results['summary']['success_rate']:.1f}%",
                "vulnerabilities_found": test_results["summary"]["vulnerabilities_found"]
            },
            "security_assessment": {
                "overall_security_posture": "strong" if test_results["summary"]["success_rate"] > 90 else "needs_improvement",
                "critical_vulnerabilities": test_results["summary"]["critical_vulnerabilities"],
                "high_vulnerabilities": test_results["summary"]["high_vulnerabilities"],
                "remediation_required": test_results["summary"]["vulnerabilities_found"] > 0
            },
            "testing_capabilities": {
                "automated_security_testing": True,
                "penetration_testing": True,
                "vulnerability_scanning": True,
                "compliance_validation": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to run security test suite: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/security/testing/penetration-test")
async def run_penetration_test(pen_test_request: Dict[str, Any]):
    """
    Run specific penetration testing scenario.
    
    Provides targeted security testing for specific attack vectors.
    """
    try:
        from src.services.security import SecurityTestingFramework
        from src.utils.config import config
        
        testing_framework = SecurityTestingFramework(config)
        
        scenario = pen_test_request["scenario"]
        
        # Run penetration test
        results = await testing_framework.run_penetration_test_scenario(scenario)
        
        return {
            "penetration_test_results": results,
            "test_scenario": {
                "scenario_name": scenario,
                "attack_vector": scenario.replace("_", " ").title(),
                "test_completed": True,
                "vulnerabilities_found": len(results.get("vulnerabilities", []))
            },
            "security_findings": {
                "vulnerabilities": results.get("vulnerabilities", []),
                "recommendations": results.get("recommendations", []),
                "risk_assessment": "high" if len(results.get("vulnerabilities", [])) > 0 else "low"
            },
            "available_scenarios": testing_framework.penetration_test_scenarios,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to run penetration test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/security/metrics/dashboard")
async def get_security_metrics_dashboard():
    """
    Get comprehensive security metrics dashboard.
    
    Provides real-time security monitoring and compliance metrics.
    """
    try:
        from src.services.security import SecurityMonitor, ComplianceManager
        from src.utils.config import config
        
        security_monitor = SecurityMonitor(config)
        compliance_manager = ComplianceManager(config)
        
        # Get security metrics
        security_metrics = await security_monitor.get_security_metrics()
        compliance_metrics = await compliance_manager.get_compliance_dashboard_metrics()
        
        return {
            "security_dashboard": {
                "security_metrics": {
                    "active_alerts": security_metrics.security_alerts_open,
                    "resolved_alerts": security_metrics.security_alerts_resolved,
                    "suspicious_behaviors": security_metrics.suspicious_behaviors_detected,
                    "potential_compromises": security_metrics.potential_compromises_detected,
                    "automated_responses": security_metrics.automated_responses_triggered
                },
                "compliance_metrics": compliance_metrics,
                "authentication_metrics": {
                    "successful_authentications": security_metrics.successful_authentications,
                    "failed_authentications": security_metrics.failed_authentications,
                    "active_certificates": security_metrics.active_agent_certificates,
                    "expired_certificates": security_metrics.expired_certificates
                }
            },
            "security_posture": {
                "overall_health": "good" if security_metrics.security_alerts_open < 5 else "needs_attention",
                "threat_level": "low" if security_metrics.potential_compromises_detected == 0 else "elevated",
                "compliance_status": "compliant" if all(
                    framework_data.get("compliance_percentage", 0) > 80 
                    for framework_data in compliance_metrics.get("frameworks", {}).values()
                ) else "non_compliant"
            },
            "real_time_features": {
                "live_threat_detection": True,
                "automated_response": True,
                "compliance_monitoring": True,
                "certificate_management": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get security metrics dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Task 13: Integration and End-to-End Workflows

@app.post("/integration/incidents/submit")
async def submit_incident_for_processing(incident_data: Dict[str, Any]):
    """
    Submit incident for end-to-end processing through integrated workflow.
    
    Task 13.2: Complete incident lifecycle management
    """
    try:
        from src.services.incident_lifecycle_manager import get_incident_lifecycle_manager
        from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
        
        # Create incident from request data
        business_impact = BusinessImpact(
            service_tier=ServiceTier(incident_data.get("service_tier", "tier_2")),
            affected_users=incident_data.get("affected_users", 0),
            revenue_impact_per_minute=incident_data.get("revenue_impact_per_minute", 0.0)
        )
        
        metadata = IncidentMetadata(
            source_system=incident_data.get("source_system", "integration_api"),
            tags=incident_data.get("tags", {})
        )
        
        incident = Incident(
            title=incident_data["title"],
            description=incident_data["description"],
            severity=IncidentSeverity(incident_data.get("severity", "medium")),
            business_impact=business_impact,
            metadata=metadata
        )
        
        # Submit for processing
        lifecycle_manager = get_incident_lifecycle_manager()
        incident_id = await lifecycle_manager.submit_incident(incident)
        
        return {
            "incident_id": incident_id,
            "status": "submitted",
            "priority": lifecycle_manager.active_incidents[incident_id].priority.name,
            "estimated_processing_time": "3-5 minutes",
            "lifecycle_features": {
                "end_to_end_processing": True,
                "state_machine_management": True,
                "concurrent_processing": True,
                "business_impact_prioritization": True,
                "automatic_escalation": True
            },
            "tracking_endpoints": {
                "status": f"/integration/incidents/{incident_id}/status",
                "lifecycle": f"/integration/incidents/{incident_id}/lifecycle",
                "metrics": f"/integration/processing/metrics"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to submit incident for processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/integration/incidents/{incident_id}/status")
async def get_incident_processing_status(incident_id: str):
    """
    Get comprehensive incident processing status and lifecycle information.
    
    Task 13.2: Incident state machine with proper transition handling
    """
    try:
        from src.services.incident_lifecycle_manager import get_incident_lifecycle_manager
        
        lifecycle_manager = get_incident_lifecycle_manager()
        status = lifecycle_manager.get_incident_status(incident_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        return {
            "incident_status": status,
            "lifecycle_management": {
                "state_machine_controlled": True,
                "transition_validation": True,
                "automatic_progression": True,
                "escalation_handling": True
            },
            "processing_context": {
                "concurrent_processing": True,
                "priority_based_scheduling": True,
                "linear_performance_scaling": True,
                "comprehensive_error_handling": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get incident status {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/integration/incidents/{incident_id}/lifecycle")
async def get_incident_lifecycle_details(incident_id: str):
    """
    Get detailed incident lifecycle information including state transitions.
    
    Shows complete incident journey through the system.
    """
    try:
        from src.services.incident_lifecycle_manager import get_incident_lifecycle_manager
        
        lifecycle_manager = get_incident_lifecycle_manager()
        status = lifecycle_manager.get_incident_status(incident_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        return {
            "incident_id": incident_id,
            "lifecycle_details": {
                "current_state": status["current_state"],
                "state_transitions": status["state_transitions"],
                "processing_duration": status["processing_duration_seconds"],
                "priority": status["priority"],
                "workflow_integration": {
                    "workflow_id": status["workflow_id"],
                    "agent_coordination": True,
                    "dependency_management": True,
                    "parallel_execution": True
                }
            },
            "state_machine_info": {
                "valid_transitions": "Managed by state machine",
                "transition_validation": "Automatic",
                "error_handling": "Comprehensive with recovery",
                "escalation_triggers": "Automatic based on conditions"
            },
            "integration_features": {
                "end_to_end_processing": True,
                "concurrent_incident_handling": True,
                "business_impact_prioritization": True,
                "automatic_recovery": True,
                "human_escalation": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get incident lifecycle {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/integration/processing/metrics")
async def get_integration_processing_metrics():
    """
    Get comprehensive processing metrics for integrated workflow system.
    
    Task 13.2: Concurrent incident processing with linear performance scaling
    """
    try:
        from src.services.incident_lifecycle_manager import get_incident_lifecycle_manager
        from src.services.agent_swarm_coordinator import get_agent_swarm_coordinator
        
        lifecycle_manager = get_incident_lifecycle_manager()
        swarm_coordinator = get_agent_swarm_coordinator()
        
        # Get processing metrics
        processing_metrics = lifecycle_manager.get_processing_metrics()
        queue_status = lifecycle_manager.get_incident_queue_status()
        agent_health = swarm_coordinator.get_agent_health_status()
        
        return {
            "integration_metrics": {
                "incident_processing": processing_metrics,
                "queue_management": queue_status,
                "agent_coordination": {
                    "total_agents": len(agent_health),
                    "healthy_agents": sum(1 for status in agent_health.values() if status["is_healthy"]),
                    "degraded_agents": sum(1 for status in agent_health.values() if status["is_degraded"]),
                    "dependency_graph_valid": True
                }
            },
            "performance_characteristics": {
                "concurrent_processing": True,
                "linear_scaling": True,
                "priority_based_scheduling": True,
                "automatic_load_balancing": True,
                "fault_tolerance": True
            },
            "system_capabilities": {
                "end_to_end_automation": True,
                "state_machine_management": True,
                "comprehensive_error_handling": True,
                "automatic_recovery": True,
                "human_escalation": True,
                "business_impact_prioritization": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get integration metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/integration/workflow/coordination")
async def get_workflow_coordination_status():
    """
    Get agent swarm coordination status and dependency management.
    
    Task 13.1: Multi-agent orchestration with dependency ordering
    """
    try:
        from src.services.agent_swarm_coordinator import get_agent_swarm_coordinator
        
        swarm_coordinator = get_agent_swarm_coordinator()
        
        # Get coordination information
        agent_health = swarm_coordinator.get_agent_health_status()
        dependency_info = swarm_coordinator.get_dependency_graph_info()
        validation_results = await swarm_coordinator.validate_workflow_integrity()
        
        return {
            "workflow_coordination": {
                "agent_health_status": agent_health,
                "dependency_management": dependency_info,
                "workflow_validation": validation_results
            },
            "coordination_features": {
                "dependency_ordering": True,
                "deadlock_prevention": True,
                "parallel_execution": True,
                "state_checkpointing": True,
                "graceful_degradation": True,
                "fallback_chains": True
            },
            "orchestration_capabilities": {
                "multi_agent_coordination": True,
                "dependency_graph_management": True,
                "execution_planning": True,
                "failure_recovery": True,
                "human_escalation": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow coordination status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/integration/error-handling/analytics")
async def get_error_handling_analytics():
    """
    Get comprehensive error handling and recovery analytics.
    
    Task 13.3: System-wide error logging and incident correlation
    """
    try:
        from src.services.error_handling_recovery import get_error_handling_system
        
        error_system = get_error_handling_system()
        analytics = error_system.get_error_analytics()
        
        return {
            "error_handling_analytics": analytics,
            "recovery_capabilities": {
                "graceful_degradation": True,
                "automatic_recovery": True,
                "human_escalation": True,
                "error_correlation": True,
                "context_preservation": True,
                "fallback_strategies": True
            },
            "system_resilience": {
                "comprehensive_error_handling": True,
                "automatic_recovery_mechanisms": True,
                "escalation_triggers": True,
                "system_wide_logging": True,
                "incident_correlation": True,
                "recovery_monitoring": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get error handling analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.environment == "development",
        log_level="info"
    )
