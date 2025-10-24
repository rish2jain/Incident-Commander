"""Operator control and scenario routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_services
from src.api.routers.models import OperatorSettingsRequest, OperatorDryRunRequest, ScenarioBuildRequest
from src.services.container import ServiceContainer


router = APIRouter(prefix="/operator", tags=["operator"])


@router.get("/settings")
async def get_operator_settings(services: ServiceContainer = Depends(get_services)):
    return {
        "settings": services.operator_controls.get_settings(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/settings")
async def update_operator_settings(
    request: OperatorSettingsRequest, services: ServiceContainer = Depends(get_services)
):
    controls = services.operator_controls
    try:
        if request.autonomy_mode is not None or request.confidence_threshold is not None:
            current_mode = request.autonomy_mode or controls.get_settings()["autonomy_mode"]
            controls.set_autonomy_mode(current_mode, confidence_threshold=request.confidence_threshold)
        if request.global_dry_run is not None:
            controls.toggle_global_dry_run(request.global_dry_run)
    except ValueError as exc:  # pragma: no cover - validation bubble
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "settings": controls.get_settings(),
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Operator settings updated",
    }


@router.post("/dry-run")
async def configure_dry_run(
    request: OperatorDryRunRequest, services: ServiceContainer = Depends(get_services)
):
    if not request.incident_id:
        raise HTTPException(status_code=400, detail="incident_id is required for dry-run toggles")

    controls = services.operator_controls
    controls.set_incident_dry_run(request.incident_id, request.enabled)

    return {
        "incident_id": request.incident_id,
        "dry_run": controls.is_dry_run(request.incident_id),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/scenarios/{template_name}")
async def build_operator_scenario(
    template_name: str,
    request: ScenarioBuildRequest,
    services: ServiceContainer = Depends(get_services),
):
    try:
        scenario = services.operator_controls.build_scenario(template_name, request.overrides)
        return {
            "scenario": scenario,
            "history_length": len(services.operator_controls.get_scenario_history()),
        }
    except ValueError as exc:  # pragma: no cover
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/scenarios/history")
async def get_scenario_history(services: ServiceContainer = Depends(get_services)):
    return {
        "scenarios": services.operator_controls.get_scenario_history(),
        "timestamp": datetime.utcnow().isoformat(),
    }
