"""Security Headers Middleware for production security hardening."""

# ruff: noqa: E501 - header strings intentionally long

import base64
import secrets
from typing import Final

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


def _generate_nonce() -> str:
    """Return a base64 encoded cryptographic nonce."""
    # 16 bytes -> 22 char URL-safe string once base64 encoded without padding
    token = secrets.token_bytes(16)
    return base64.b64encode(token).decode("ascii").rstrip("=")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    STYLE_NONCE_HEADER: Final[str] = "X-Style-Nonce"

    async def dispatch(self, request: Request, call_next):
        style_nonce = _generate_nonce()
        request.state.style_nonce = style_nonce

        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers[self.STYLE_NONCE_HEADER] = style_nonce

        csp = (
            "default-src 'self'; "
            f"script-src 'self' 'nonce-{style_nonce}'; "
            f"style-src 'self' 'nonce-{style_nonce}' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self' ws: wss:"  # Allow WebSocket connections
        )

        response.headers["Content-Security-Policy"] = csp

        return response
