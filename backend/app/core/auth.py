import asyncio
import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException, WebSocket

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("auth")
_CACHE_TTL_SECONDS = 60
_user_cache: Dict[str, tuple[float, "AuthUser"]] = {}


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: Optional[str] = None
    name: Optional[str] = None


def _extract_bearer(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authentication required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    return token


def _fetch_supabase_user(token: str) -> AuthUser:
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise HTTPException(status_code=500, detail="Authentication service is not configured")

    req = urllib.request.Request(
        f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user",
        headers={
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {token}",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            payload: Dict[str, Any] = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            raise HTTPException(status_code=401, detail="Invalid or expired session") from exc
        logger.error("Supabase auth request failed", exc_info=exc)
        raise HTTPException(status_code=503, detail="Authentication service unavailable") from exc
    except Exception as exc:
        logger.error("Supabase auth request failed", exc_info=exc)
        raise HTTPException(status_code=503, detail="Authentication service unavailable") from exc

    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid session")

    metadata = payload.get("user_metadata") or {}
    return AuthUser(
        id=user_id,
        email=payload.get("email"),
        name=metadata.get("full_name") or metadata.get("name"),
    )


async def verify_supabase_token(token: str) -> AuthUser:
    cached = _user_cache.get(token)
    now = time.time()
    if cached and cached[0] > now:
        return cached[1]

    user = await asyncio.to_thread(_fetch_supabase_user, token)
    _user_cache[token] = (now + _CACHE_TTL_SECONDS, user)
    return user


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> AuthUser:
    return await verify_supabase_token(_extract_bearer(authorization))


async def get_websocket_user(websocket: WebSocket) -> Optional[AuthUser]:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return None

    try:
        return await verify_supabase_token(token)
    except HTTPException:
        await websocket.close(code=1008, reason="Invalid session")
        return None


async def require_meeting_admin(room_id: str, user: AuthUser) -> None:
    from app.modules.meeting.permissions import require_admin

    await require_admin(room_id, user)
