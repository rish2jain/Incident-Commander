"""Routing helpers for LangGraph node coordination."""

from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Dict, Iterable

from src.langgraph_orchestrator.state_schema import IncidentGraphState


async def run_parallel(*coroutines: Awaitable[IncidentGraphState]) -> Iterable[IncidentGraphState]:
    """Execute coroutines in parallel and return their results preserving order."""
    return await asyncio.gather(*coroutines)


def merge_state_updates(
    base_state: IncidentGraphState, *updates: Dict[str, Any]
) -> IncidentGraphState:
    """Merge state update dictionaries into a new incident graph state."""
    merged: IncidentGraphState = dict(base_state)
    for update in updates:
        for key, value in update.items():
            merged[key] = value
    return merged

