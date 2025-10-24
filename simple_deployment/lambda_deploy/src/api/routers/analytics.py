"""Analytics insights routes."""

from __future__ import annotations
import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.dependencies import get_services
from src.services.container import ServiceContainer

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/insights")
async def get_analytics_insights(services: ServiceContainer = Depends(get_services)):
    try:
        return services.analytics.build_insights(services.coordinator)
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to build analytics insights")
        raise HTTPException(status_code=500, detail="Internal server error") from exc
