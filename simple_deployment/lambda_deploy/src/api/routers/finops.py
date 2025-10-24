"""FinOps visibility routes."""

from __future__ import annotations
import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_services
from src.services.container import ServiceContainer
from src.api.routers.models import FinOpsGuardrailRequest

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/finops", tags=["finops"])


@router.get("/dashboard")
async def get_finops_dashboard(services: ServiceContainer = Depends(get_services)):
    try:
        return await services.finops.get_dashboard()
    except Exception as exc:  # pragma: no cover - surfaced in caller
        logger.exception("Failed to get FinOps dashboard")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.post("/guardrails")
async def configure_finops_guardrail(
    request: FinOpsGuardrailRequest, services: ServiceContainer = Depends(get_services)
):
    # Input validation
    if not request.daily_limit or request.daily_limit <= 0:
        raise HTTPException(status_code=400, detail="daily_limit must be positive")
    if not request.weekly_limit or request.weekly_limit <= 0:
        raise HTTPException(status_code=400, detail="weekly_limit must be positive")
    
    try:
        guardrail = await services.finops.register_budget(
            tenant=request.tenant,
            daily_limit=request.daily_limit,
            weekly_limit=request.weekly_limit,
            capabilities=request.capabilities,
        )
        return {"guardrail": guardrail.to_dict(), "message": "Guardrail registered"}
    except ValueError as e:
        # Expected validation errors
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to configure FinOps guardrail")
        raise HTTPException(status_code=500, detail="Internal server error") from exc


@router.get("/guardrails")
async def get_finops_guardrails(services: ServiceContainer = Depends(get_services)):
    guardrails = await services.finops.get_guardrails()
    return {"guardrails": guardrails}
