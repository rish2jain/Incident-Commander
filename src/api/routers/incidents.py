"""Incident-related API routes."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from src.api.dependencies import get_services
from src.schemas.incident import IncidentTimelineResponse
from src.services.container import ServiceContainer


router = APIRouter(prefix="/incidents", tags=["incidents"])


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
