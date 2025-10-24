"""FastAPI dependencies for shared services."""

from __future__ import annotations

from fastapi import Depends

from src.services.container import get_container, ServiceContainer
from src.utils.logging import get_logger

logger = get_logger("api.dependencies")


async def get_services() -> ServiceContainer:
    """Dependency wrapper returning initialized service container."""
    container = get_container()
    try:
        await container.startup()
    except Exception as e:
        logger.error(f"Failed to start service container: {e}")
        raise
    return container


ServiceDependency = Depends(get_services)
