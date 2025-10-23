"""Streaming integration helpers for LangGraph orchestration."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional


class StreamEmitter:
    """Lightweight async emitter for streaming LangGraph updates."""

    def __init__(self, callback: Optional[Callable[[str, Any], Awaitable[None]]] = None) -> None:
        self._callback = callback

    async def emit(self, channel: str, payload: Any) -> None:
        if not self._callback:
            return
        await self._callback(channel, payload)

