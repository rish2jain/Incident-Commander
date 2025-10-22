"""Incident-related API routes."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, Query

from src.api.dependencies import get_services
from src.schemas.incident import IncidentTimelineResponse
from src.services.container import ServiceContainer


router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("/")
async def list_incidents(
    status: Optional[str] = Query(None, description="Filter by status: active, resolved, all"),
    severity: Optional[str] = Query(None, description="Filter by severity: critical, high, medium, low"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of incidents to return"),
    offset: int = Query(0, ge=0, description="Number of incidents to skip"),
    services: ServiceContainer = Depends(get_services)
):
    """List incidents with optional filtering and pagination."""
    coordinator = services.coordinator
    
    # Get all incidents from coordinator
    # Note: This assumes coordinator has a list_incidents method
    # If not available, we'll need to implement it
    try:
        if hasattr(coordinator, 'list_incidents'):
            incidents = coordinator.list_incidents(
                status=status,
                severity=severity,
                limit=limit,
                offset=offset
            )
        else:
            # Fallback: Return empty list with a note
            # This allows the endpoint to work even if backend method isn't implemented yet
            incidents = []
            
        # Get total count for pagination
        if hasattr(coordinator, 'get_incidents_count'):
            total_count = coordinator.get_incidents_count(
                status=status,
                severity=severity
            )
        else:
            total_count = len(incidents)
        
        return {
            "incidents": incidents,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "filters": {
                "status": status,
                "severity": severity
            }
        }
    except ValueError as e:
        # Handle expected validation errors
        raise HTTPException(status_code=400, detail=str(e))
    except AttributeError as e:
        # Handle missing coordinator methods gracefully
        return {
            "incidents": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "filters": {"status": status, "severity": severity},
            "note": "Incident listing not yet fully implemented in coordinator"
        }
    except Exception as e:
        # Log unexpected errors and return 500
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Unexpected error in list_incidents: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{incident_id}")
async def get_incident(incident_id: str, services: ServiceContainer = Depends(get_services)):
    coordinator = services.coordinator
    status = coordinator.get_incident_status(incident_id)

    if not status:
        raise HTTPException(status_code=404, detail="Incident not found")

    return {"incident_id": incident_id, **status}


@router.get("/{incident_id}/timeline", response_model=IncidentTimelineResponse)
async def get_incident_timeline(
    incident_id: str,
    event_type: Optional[str] = None,
    phase: Optional[str] = None,
    agent: Optional[str] = None,
    search: Optional[str] = None,
    services: ServiceContainer = Depends(get_services),
):
    coordinator = services.coordinator
    timeline_payload = coordinator.get_incident_timeline(
        incident_id,
        event_type=event_type,
        phase=phase,
        agent=agent,
        search=search,
    )

    if not timeline_payload:
        raise HTTPException(status_code=404, detail="Incident not found")

    timeline_payload["filters"] = {
        "event_type": event_type,
        "phase": phase,
        "agent": agent,
        "search": search,
    }

    return IncidentTimelineResponse(**timeline_payload)


@router.get("/{incident_id}/explainability")
async def get_incident_explainability(incident_id: str, services: ServiceContainer = Depends(get_services)):
    coordinator = services.coordinator
    state = coordinator.get_processing_state(incident_id)

    if not state:
        raise HTTPException(status_code=404, detail="Incident not found")

    package = services.explainability.build_explainability_package(state)
    return package