#!/usr/bin/env python3
"""
Mock Backend for Demo Recording
Provides minimal endpoints needed for demo automation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import time
from datetime import datetime

app = FastAPI(title="Mock Incident Commander Backend")

# Enable CORS for dashboard
import os
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # Set to True only if cookies/auth headers are needed
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Mock data for demo
mock_incidents = []
MAX_INCIDENTS = 100  # Prevent unbounded memory growth
mock_agents = {
    "detection": {"status": "active", "confidence": 0.95},
    "diagnosis": {"status": "active", "confidence": 0.88},
    "prediction": {"status": "active", "confidence": 0.92},
    "resolution": {"status": "active", "confidence": 0.85},
    "communication": {"status": "active", "confidence": 0.90}
}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/health")
async def api_health_check():
    """API health check endpoint"""
    return {"status": "healthy", "service": "mock-backend"}

@app.post("/incidents/trigger")
async def trigger_incident(incident_data: dict = None):
    """Trigger a mock incident"""
    
    # Input validation
    if incident_data is not None:
        if not isinstance(incident_data, dict):
            raise HTTPException(status_code=400, detail="incident_data must be a dictionary")
        
        # Validate incident type
        incident_type = incident_data.get("type", "database_cascade")
        if not isinstance(incident_type, str):
            raise HTTPException(status_code=400, detail="type must be a string")
        
        # Validate severity
        severity = incident_data.get("severity", "high")
        allowed_severities = ["low", "medium", "high", "critical"]
        if severity not in allowed_severities:
            raise HTTPException(status_code=400, detail=f"severity must be one of {allowed_severities}")
        
        # Validate status
        status = incident_data.get("status", "detected")
        allowed_statuses = ["detected", "investigating", "resolved"]
        if status not in allowed_statuses:
            raise HTTPException(status_code=400, detail=f"status must be one of {allowed_statuses}")
        
        # Validate description
        description = incident_data.get("description", "Mock incident for demo purposes")
        if not isinstance(description, str):
            raise HTTPException(status_code=400, detail="description must be a string")
    else:
        incident_type = "database_cascade"
        severity = "high"
        status = "detected"
        description = "Mock incident for demo purposes"
    
    incident = {
        "id": f"incident_{int(time.time())}",
        "type": incident_type,
        "severity": severity,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "description": description
    }
    
    # Enforce max incidents limit
    mock_incidents.append(incident)
    if len(mock_incidents) > MAX_INCIDENTS:
        mock_incidents.pop(0)  # Remove oldest incident
    
    return {"success": True, "incident": incident}

@app.get("/incidents")
async def get_incidents():
    """Get all incidents"""
    return {"incidents": mock_incidents}

@app.get("/agents/status")
async def get_agent_status():
    """Get agent status"""
    return {"agents": mock_agents}

@app.get("/demo/stats")
async def get_demo_stats():
    """Get demo statistics"""
    return {
        "mttr": "15 seconds",
        "cost_saved": "$103,360",
        "affected_users": "12,450",
        "sla_compliance": "100%",
        "incidents_resolved": len(mock_incidents),
        "agent_accuracy": "95.2%"
    }

@app.get("/demo/incident")
async def demo_incident():
    """Demo incident endpoint"""
    return await trigger_incident({"type": "database_cascade"})

if __name__ == "__main__":
    print("🚀 Starting Mock Backend for Demo Recording...")
    print("📍 Backend will be available at: http://localhost:8000")
    print("🔗 Health check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000)