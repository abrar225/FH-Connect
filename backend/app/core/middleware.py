import time
import uuid
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logging import get_logger, reset_request_id, set_request_id

logger = get_logger("request")

# Security headers to add to all responses
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


class RequestGuardMiddleware(BaseHTTPMiddleware):
    """
    Lightweight edge protection for the API process.

    This is intentionally local and dependency-free. In production, keep it as a
    final safety net and add a shared limiter at the gateway/load-balancer layer.
    """

    _MAX_TRACKED_IPS = 10_000

    def __init__(self, app):
        super().__init__(app)
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)

    def _sweep_stale_clients(self, now: float) -> None:
        """Purge IP entries whose most recent hit is older than the rate window."""
        cutoff = now - settings.RATE_LIMIT_WINDOW_SECONDS
        stale_keys = [k for k, v in self._hits.items() if not v or v[-1] < cutoff]
        for k in stale_keys:
            del self._hits[k]

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        token = set_request_id(request_id)
        started_at = time.monotonic()
        content_length = request.headers.get("content-length")
        try:
            if content_length:
                try:
                    parsed_content_length = int(content_length)
                except ValueError:
                    response = JSONResponse(status_code=400, content={"detail": "Invalid content length"})
                    response.headers["x-request-id"] = request_id
                    return response
                if parsed_content_length > settings.MAX_REQUEST_BYTES:
                    response = JSONResponse(status_code=413, content={"detail": "Request too large"})
                    response.headers["x-request-id"] = request_id
                    return response

            forwarded_for = request.headers.get("x-forwarded-for", "").split(",", 1)[0].strip()
            client = forwarded_for or (request.client.host if request.client else "unknown")
            now = time.monotonic()
            window_start = now - settings.RATE_LIMIT_WINDOW_SECONDS
            hits = self._hits[client]

            while hits and hits[0] < window_start:
                hits.popleft()

            # Lazy sweep: purge stale IPs only when dict grows too large
            if len(self._hits) > self._MAX_TRACKED_IPS:
                self._sweep_stale_clients(now)

            if len(hits) >= settings.RATE_LIMIT_REQUESTS:
                response = JSONResponse(status_code=429, content={"detail": "Too many requests"})
                response.headers["x-request-id"] = request_id
                return response

            hits.append(now)
            response = await call_next(request)

            # Add security headers
            for header, value in SECURITY_HEADERS.items():
                response.headers[header] = value

            response.headers["x-request-id"] = request_id
            logger.info(
                f"HTTP {request.method} {request.url.path} -> {response.status_code} "
                f"in {(time.monotonic() - started_at) * 1000:.1f}ms"
            )
            return response
        finally:
            reset_request_id(token)
