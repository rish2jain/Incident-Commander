"""FastAPI dependencies for shared services."""

from __future__ import annotations

from fastapi import Depends

from src.services.container import get_container, ServiceContainer


async def get_services() -> ServiceContainer:
    """Dependency wrapper returning initialized service container."""
    container = get_container()
    try:
        await container.startup()
    except Exception as e:
        print(f"Failed to start service container: {e}")
        raise
    return container


ServiceDependency = Depends(get_services)
