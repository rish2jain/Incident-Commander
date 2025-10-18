"""Optional live WebSocket validation for hackathon demos.

Run with `RUN_LIVE_DEMO_TESTS=1 pytest tests/manual/test_websocket_live.py` while
`uvicorn src.main:app --reload` is active.
"""

import asyncio
import json
import os
from datetime import datetime, timezone

import pytest

websockets = pytest.importorskip("websockets")

pytestmark = [
    pytest.mark.manual,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_DEMO_TESTS") != "1",
        reason="Set RUN_LIVE_DEMO_TESTS=1 to exercise live WebSocket checks.",
    )
]


@pytest.mark.asyncio
async def test_websocket_ping_roundtrip() -> None:
    """Verify the demo WebSocket accepts a ping and streams responses."""

    uri = os.getenv("LIVE_WEBSOCKET_URI", "ws://localhost:8000/ws")

    async with websockets.connect(uri) as websocket:  # type: ignore[attr-defined]
        ping_message = {
            "type": "ping",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await websocket.send(json.dumps(ping_message))

        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        payload = json.loads(message)

        assert "type" in payload, "WebSocket payload missing type"
        assert payload["type"] in {"pong", "status", "event"}, "Unexpected payload type"
