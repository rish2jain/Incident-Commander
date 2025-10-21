"""
Enhanced FastAPI application with 3D dashboard and Byzantine consensus.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import asyncio

from src.api.routers import dashboard
from src.services.websocket_manager import websocket_manager
from src.services.auth_middleware import AuthenticationMiddleware, get_security_config
from src.services.localstack_fixtures import initialize_localstack_for_testing
from src.services.opentelemetry_integration import initialize_observability
from src.services.metrics_endpoint import get_metrics_service, metrics_router
from src.utils.logging import get_logger


logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Incident Commander with enhanced features")
    
    # Initialize LocalStack for testing
    await initialize_localstack_for_testing()
    
    # Initialize observability
    initialize_observability()
    
    # Start WebSocket manager
    await websocket_manager.start()
    
    # Start metrics collection
    metrics_service = get_metrics_service()
    await metrics_service.start_background_collection()
    
    # Initialize demo scenarios
    from src.services.demo_scenario_manager import get_demo_manager
    demo_mgr = await get_demo_manager()
    logger.info("Demo scenario manager initialized")
    
    logger.info("All services initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Incident Commander")
    
    # Stop metrics collection
    await metrics_service.stop_background_collection()
    
    # Stop WebSocket manager
    await websocket_manager.stop()
    
    # Cleanup LocalStack
    from src.services.localstack_fixtures import cleanup_localstack
    await cleanup_localstack()
    
    logger.info("Shutdown complete")


# Create FastAPI app with enhanced features
app = FastAPI(
    title="Incident Commander - Enhanced Edition",
    description="AI-powered incident response with 3D visualization and Byzantine consensus",
    version="2.0.0",
    lifespan=lifespan
)

# Security configuration
security_config = get_security_config()

# Authentication middleware
app.add_middleware(AuthenticationMiddleware, security_config=security_config)

# CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=security_config.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard.router)

# Include security router
from src.api.routers import security
app.include_router(security.router)

# Include AWS AI services router for hackathon compliance
from src.api.routers import aws_ai_services
app.include_router(aws_ai_services.router)

# Include real AWS AI showcase for prize eligibility
from src.api.routers import real_aws_ai_showcase
app.include_router(real_aws_ai_showcase.router)

# Include metrics router
app.include_router(metrics_router)

# Serve static files for dashboard
try:
    app.mount("/static", StaticFiles(directory="dashboard/build"), name="static")
except RuntimeError:
    # Dashboard build directory doesn't exist yet
    logger.warning("Dashboard build directory not found - run 'npm run build' in dashboard/")


@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "name": "Incident Commander - Enhanced Edition",
        "version": "2.0.0",
        "features": [
            "3D Real-time Agent Visualization",
            "Byzantine Fault-Tolerant Consensus (PBFT)",
            "Interactive Demo Scenarios",
            "Malicious Agent Detection & Isolation",
            "WebSocket Real-time Updates",
            "Comprehensive Performance Metrics",
            "JWT/API Key Authentication",
            "LocalStack Testing Infrastructure",
            "OpenTelemetry Observability",
            "Prometheus Metrics Export",
            "FinOps Cost Management"
        ],
        "endpoints": {
            "dashboard": "/dashboard/",
            "websocket": "/dashboard/ws",
            "metrics": "/metrics/",
            "metrics_summary": "/metrics/summary",
            "metrics_history": "/metrics/history",
            "demo_trigger": "/dashboard/trigger-demo",
            "byzantine_injection": "/dashboard/inject-byzantine-fault",
            "reset": "/dashboard/reset-agents",
            "health": "/health",
            "system_status": "/system-status"
        }
    }


@app.get("/health")
async def health_check():
    """Enhanced health check with component status."""
    from src.services.demo_scenario_manager import get_demo_manager
    
    try:
        # Check WebSocket manager
        ws_metrics = websocket_manager.get_metrics()
        
        # Check demo manager
        demo_mgr = await get_demo_manager()
        demo_metrics = demo_mgr.get_demo_metrics()
        
        return {
            "status": "healthy",
            "timestamp": ws_metrics.get("uptime_seconds", 0),
            "components": {
                "websocket_manager": {
                    "status": "healthy",
                    "active_connections": ws_metrics.get("active_connections", 0),
                    "total_messages_sent": ws_metrics.get("total_messages_sent", 0)
                },
                "demo_manager": {
                    "status": "healthy",
                    "scenarios_run": demo_metrics["performance_metrics"]["scenarios_run"],
                    "faults_injected": demo_metrics["performance_metrics"]["faults_injected"],
                    "active_scenarios": demo_metrics["active_scenarios"]
                },
                "byzantine_consensus": {
                    "status": "healthy",
                    "detection_rate": demo_metrics["performance_metrics"]["byzantine_detection_rate"]
                }
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/system-status")
async def system_status():
    """Comprehensive system status for monitoring."""
    from src.services.demo_scenario_manager import get_demo_manager
    
    try:
        # Get all component metrics
        ws_metrics = websocket_manager.get_metrics()
        demo_mgr = await get_demo_manager()
        demo_metrics = demo_mgr.get_demo_metrics()
        
        return {
            "system": {
                "name": "Incident Commander Enhanced",
                "version": "2.0.0",
                "uptime_seconds": ws_metrics.get("uptime_seconds", 0)
            },
            "websocket": {
                "active_connections": ws_metrics.get("active_connections", 0),
                "total_connections": ws_metrics.get("total_connections", 0),
                "messages_per_second": ws_metrics.get("messages_per_second", 0),
                "total_messages_sent": ws_metrics.get("total_messages_sent", 0)
            },
            "demo_scenarios": {
                "total_scenarios_run": demo_metrics["performance_metrics"]["scenarios_run"],
                "active_scenarios": demo_metrics["active_scenarios"],
                "average_resolution_time": demo_metrics["performance_metrics"]["average_resolution_time"],
                "available_scenarios": demo_metrics["available_scenarios"]
            },
            "byzantine_consensus": {
                "faults_injected": demo_metrics["performance_metrics"]["faults_injected"],
                "active_faults": demo_metrics["active_faults"],
                "detection_rate": demo_metrics["performance_metrics"]["byzantine_detection_rate"],
                "available_fault_types": demo_metrics["available_faults"]
            }
        }
    except Exception as e:
        logger.error(f"System status check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Incident Commander Enhanced Edition")
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )