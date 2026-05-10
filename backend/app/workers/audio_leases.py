import json
import socket
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings
from app.core.database import db
from app.core.logging import get_logger

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

logger = get_logger("audio_leases")
INSTANCE_ID = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"

RENEW_LEASE_SCRIPT = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
  return redis.call("PEXPIRE", KEYS[1], ARGV[2])
end
return 0
"""

RELEASE_LEASE_SCRIPT = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
  return redis.call("DEL", KEYS[1])
end
return 0
"""


@dataclass
class AudioWorkerLease:
    room_id: str
    instance_id: str
    fencing_token: str
    redis_client: object | None


def _lease_key(room_id: str) -> str:
    return f"fh:audio-worker:lease:{room_id}"


async def _persist_lease(lease: AudioWorkerLease, ttl_ms: int) -> None:
    if not db.pool:
        return
    expires_at = datetime.now(timezone.utc) + timedelta(milliseconds=ttl_ms)
    await db.pool.execute(
        """INSERT INTO audio_worker_leases (room_id, instance_id, fencing_token, lease_expires_at, last_renewed_at)
           VALUES ($1, $2, $3, $4, timezone('utc'::text, now()))
           ON CONFLICT (room_id) DO UPDATE
           SET instance_id = EXCLUDED.instance_id,
               fencing_token = EXCLUDED.fencing_token,
               lease_expires_at = EXCLUDED.lease_expires_at,
               last_renewed_at = timezone('utc'::text, now())""",
        lease.room_id,
        lease.instance_id,
        lease.fencing_token,
        expires_at,
    )


async def acquire_audio_worker_lease(room_id: str) -> Optional[AudioWorkerLease]:
    fencing_token = uuid.uuid4().hex
    payload = json.dumps({
        "room_id": room_id,
        "instance_id": INSTANCE_ID,
        "fencing_token": fencing_token,
        "started_at": datetime.now(timezone.utc).isoformat(),
    })

    if not settings.REDIS_URL or redis is None:
        if settings.ENVIRONMENT == "production" or settings.REQUIRE_REDIS_FOR_DISTRIBUTED_WORKERS:
            raise RuntimeError("Redis is required for distributed audio worker leases")
        logger.warning("REDIS_URL is not configured; audio worker lease is local-dev only")
        lease = AudioWorkerLease(room_id, INSTANCE_ID, fencing_token, None)
        await _persist_lease(lease, settings.AUDIO_WORKER_LEASE_TTL_MS)
        return lease

    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    acquired = await client.set(
        _lease_key(room_id),
        payload,
        nx=True,
        px=settings.AUDIO_WORKER_LEASE_TTL_MS,
    )
    if not acquired:
        await client.aclose()
        return None

    lease = AudioWorkerLease(room_id, INSTANCE_ID, fencing_token, client)
    await _persist_lease(lease, settings.AUDIO_WORKER_LEASE_TTL_MS)
    return lease


async def renew_audio_worker_lease(lease: AudioWorkerLease) -> bool:
    if lease.redis_client is None:
        await _persist_lease(lease, settings.AUDIO_WORKER_LEASE_TTL_MS)
        return True

    current = await lease.redis_client.get(_lease_key(lease.room_id))
    if not current:
        return False
    try:
        current_data = json.loads(current)
    except json.JSONDecodeError:
        return False
    if current_data.get("fencing_token") != lease.fencing_token:
        return False
    result = await lease.redis_client.eval(
        RENEW_LEASE_SCRIPT,
        1,
        _lease_key(lease.room_id),
        current,
        settings.AUDIO_WORKER_LEASE_TTL_MS,
    )
    if not result:
        return False
    await _persist_lease(lease, settings.AUDIO_WORKER_LEASE_TTL_MS)
    return True


async def release_audio_worker_lease(lease: AudioWorkerLease) -> None:
    try:
        if lease.redis_client is not None:
            current = await lease.redis_client.get(_lease_key(lease.room_id))
            if current:
                current_data = json.loads(current)
                if current_data.get("fencing_token") == lease.fencing_token:
                    await lease.redis_client.eval(RELEASE_LEASE_SCRIPT, 1, _lease_key(lease.room_id), current)
            await lease.redis_client.aclose()
        if db.pool:
            await db.pool.execute(
                "DELETE FROM audio_worker_leases WHERE room_id = $1 AND fencing_token = $2",
                lease.room_id,
                lease.fencing_token,
            )
    except Exception:
        logger.warning("Failed to release audio worker lease", exc_info=True)
