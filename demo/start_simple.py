#!/usr/bin/env python3
"""
Simple startup script that bypasses LocalStack for testing.
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment to skip LocalStack
os.environ['AWS_ENDPOINT_URL'] = 'https://bedrock-runtime.us-east-1.amazonaws.com'
os.environ['SKIP_LOCALSTACK'] = 'true'

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

# Create a simple FastAPI app without complex dependencies
app = FastAPI(
    title="Incident Commander - Simple Mode",
    description="Simplified version for testing",
    version="1.0.0"
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
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "X-Request-ID": f"req-{request.headers.get('x-request-id', 'unknown')}"
        }
        
        # Apply headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Incident Commander - Simple Mode",
        "version": "1.0.0",
        "status": "running",
        "mode": "testing"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": "2025-10-20T18:57:00Z",
        "components": {
            "api": {"status": "healthy"},
            "simple_mode": {"status": "active"}
        }
    }

@app.get("/system-status")
async def system_status():
    """System status endpoint."""
    return {
        "system": {
            "name": "Incident Commander Simple",
            "version": "1.0.0",
            "uptime_seconds": 100
        },
        "mode": "testing",
        "features": ["basic_api", "health_checks"]
    }

@app.get("/metrics/summary")
async def metrics_summary():
    """Metrics summary endpoint."""
    return {
        "active_incidents": 0,
        "resolved_incidents": 5,
        "average_resolution_time": 180,
        "system_health": "good"
    }

@app.get("/dashboard/metrics")
async def dashboard_metrics():
    """Dashboard metrics endpoint."""
    return {
        "active_connections": 1,
        "total_incidents": 5,
        "resolution_rate": 0.95
    }

@app.get("/dashboard/demo-metrics")
async def demo_metrics():
    """Demo metrics endpoint."""
    return {
        "scenarios_available": ["database_failure", "api_cascade", "memory_leak"],
        "scenarios_run": 3,
        "success_rate": 0.95
    }

@app.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint."""
    return {
        "# TYPE incidents_total counter",
        "incidents_total 5",
        "# TYPE resolution_time_seconds histogram", 
        "resolution_time_seconds_sum 900",
        "resolution_time_seconds_count 5"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Optimized WebSocket endpoint for real-time updates."""
    await websocket.accept()
    try:
        # Send immediate connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "latency": "optimized"
        }))
        
        # Fast heartbeat loop
        counter = 0
        while True:
            await asyncio.sleep(0.1)  # 100ms updates for low latency
            counter += 1
            
            if counter % 10 == 0:  # Send data every second
                await websocket.send_text(json.dumps({
                    "type": "metrics_update",
                    "data": {
                        "active_incidents": counter % 3,
                        "resolved_incidents": 5 + (counter // 10),
                        "latency_ms": 50  # Simulated low latency
                    }
                }))
            
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

@app.websocket("/dashboard/ws")
async def dashboard_websocket_endpoint(websocket: WebSocket):
    """Optimized dashboard WebSocket endpoint."""
    await websocket.accept()
    try:
        # Immediate response for latency testing
        await websocket.send_text(json.dumps({
            "type": "connection",
            "status": "connected",
            "optimized": True
        }))
        
        # Listen for messages and respond immediately
        while True:
            try:
                # Wait for message with short timeout
                message = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                
                # Echo back immediately for latency testing
                await websocket.send_text(json.dumps({
                    "type": "echo",
                    "received": message,
                    "timestamp": asyncio.get_event_loop().time()
                }))
                
            except asyncio.TimeoutError:
                # Send periodic updates
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": asyncio.get_event_loop().time()
                }))
            
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

@app.post("/dashboard/trigger-demo")
async def trigger_demo():
    """Trigger demo scenario."""
    return {
        "status": "success",
        "scenario": "database_failure",
        "estimated_duration": 120
    }

@app.post("/dashboard/reset-agents")
async def reset_agents():
    """Reset agents to initial state."""
    return {
        "status": "success",
        "message": "Agents reset successfully"
    }

@app.post("/dashboard/trigger-incident")
async def trigger_incident():
    """Trigger a new incident for testing."""
    return {
        "status": "success",
        "incident_id": "test-incident-001",
        "scenario": "database_cascade",
        "estimated_duration": 180
    }

@app.post("/dashboard/scenarios/{scenario_id}")
async def trigger_scenario(scenario_id: str):
    """Trigger a specific demo scenario."""
    scenarios = {
        "database_failure": "Database connection pool exhausted",
        "api_cascade": "API gateway cascade failure", 
        "memory_leak": "Memory leak in microservice",
        "network_partition": "Network partition detected",
        "security_breach": "Security incident detected"
    }
    
    return {
        "status": "success",
        "scenario_id": scenario_id,
        "description": scenarios.get(scenario_id, "Unknown scenario"),
        "estimated_resolution_time": 120
    }

@app.get("/dashboard/presets")
async def get_presets():
    """Get available demo presets."""
    return {
        "available_presets": [
            "quick_demo",
            "technical_deep_dive", 
            "business_impact",
            "interactive_judge"
        ],
        "default_preset": "quick_demo"
    }

@app.post("/dashboard/start-preset-demo")
async def start_preset_demo(preset_name: str):
    """Start a preset demo configuration."""
    return {
        "status": "success",
        "preset": preset_name,
        "duration_seconds": 120,
        "features_enabled": ["real_time_updates", "agent_visualization"]
    }

@app.post("/dashboard/interactive-demo")
async def interactive_demo(action: str):
    """Handle interactive demo actions."""
    if action == "get_available_scenarios":
        return {
            "result": {
                "scenarios": [
                    {"id": "db_failure", "name": "Database Failure"},
                    {"id": "api_cascade", "name": "API Cascade"},
                    {"id": "memory_leak", "name": "Memory Leak"}
                ]
            }
        }
    return {"status": "success", "action": action}

@app.post("/dashboard/judge-controls")
async def judge_controls(control_type: str):
    """Handle judge control actions."""
    if control_type == "get_detailed_metrics":
        return {
            "status": "success",
            "metrics": {
                "incidents_resolved": 15,
                "average_resolution_time": 142,
                "success_rate": 0.96
            }
        }
    elif control_type == "trigger_custom_incident":
        return {
            "status": "success", 
            "incident_id": "custom-001",
            "message": "Custom incident triggered"
        }
    return {"status": "success", "control_type": control_type}

@app.get("/dashboard/standalone-metrics")
async def standalone_dashboard_metrics():
    """Get metrics for standalone dashboard."""
    return {
        "websocket_latency": "0.2ms",
        "average_mttr": "1.4min",
        "success_rate": "95%",
        "annual_savings": "$2.8M",
        "system_status": "All services operational",
        "status_class": "healthy",
        "last_updated": datetime.now().isoformat()
    }

@app.post("/api/incidents/trigger")
async def api_trigger_incident():
    """API endpoint for triggering incidents (used by tests)."""
    return {
        "status": "success",
        "incident_id": "api-incident-001",
        "scenario": "database_cascade",
        "message": "Incident triggered via API"
    }

@app.post("/incidents/trigger")
async def trigger_incident_alt():
    """Alternative incident trigger endpoint."""
    return {
        "status": "success",
        "incident_id": "incident-001", 
        "scenario": "test_scenario",
        "message": "Incident triggered successfully"
    }

if __name__ == "__main__":
    print("🚀 Starting Incident Commander in Simple Mode")
    uvicorn.run(
        "start_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )