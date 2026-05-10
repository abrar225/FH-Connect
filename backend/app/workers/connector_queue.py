import asyncio
import json
import socket
import time
import uuid
from datetime import datetime
from typing import Optional, Tuple

from app.core.config import settings
from app.core.database import db
from app.core.logging import get_logger

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

logger = get_logger("connector_queue")
local_connector_queue = asyncio.Queue(maxsize=100)
_redis = None
_consumer_name = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"


async def connect_connector_queue() -> None:
    global _redis
    if settings.REDIS_URL and redis:
        _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        try:
            await _redis.xgroup_create(settings.CONNECTOR_STREAM_NAME, settings.CONNECTOR_CONSUMER_GROUP, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise
        logger.info("Connector queue connected to Redis Streams")
        return
    if settings.ENVIRONMENT == "production" or settings.REQUIRE_REDIS_FOR_DISTRIBUTED_WORKERS:
        raise RuntimeError("Redis is required for connector queues in production")
    logger.warning("Connector queue running in local mode")


async def disconnect_connector_queue() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def enqueue_connector_job(job_id: str) -> bool:
    payload = {"job_id": job_id}
    if _redis:
        await _redis.xadd(settings.CONNECTOR_STREAM_NAME, payload, maxlen=settings.CONNECTOR_QUEUE_MAXLEN, approximate=True)
        return True
    try:
        local_connector_queue.put_nowait(payload)
        return True
    except asyncio.QueueFull:
        return False


async def schedule_connector_job(job_id: str, run_at: datetime) -> bool:
    if _redis:
        await _redis.zadd(settings.CONNECTOR_SCHEDULED_ZSET_NAME, {job_id: run_at.timestamp()})
        return True
    return await enqueue_connector_job(job_id)


async def promote_due_connector_jobs(limit: int = 100) -> int:
    if not _redis:
        return 0
    now = time.time()
    job_ids = await _redis.zrangebyscore(settings.CONNECTOR_SCHEDULED_ZSET_NAME, min=0, max=now, start=0, num=limit)
    promoted = 0
    for job_id in job_ids:
        removed = await _redis.zrem(settings.CONNECTOR_SCHEDULED_ZSET_NAME, job_id)
        if removed:
            await enqueue_connector_job(job_id)
            promoted += 1
    return promoted


async def dequeue_connector_job(timeout_ms: int = 5000) -> Tuple[Optional[str], Optional[str]]:
    if _redis:
        messages = await _redis.xreadgroup(
            settings.CONNECTOR_CONSUMER_GROUP,
            _consumer_name,
            {settings.CONNECTOR_STREAM_NAME: ">"},
            count=1,
            block=timeout_ms,
        )
        if not messages:
            return None, None
        _stream_name, stream_messages = messages[0]
        stream_id, fields = stream_messages[0]
        return fields.get("job_id"), stream_id

    item = await local_connector_queue.get()
    return item.get("job_id"), None


async def ack_connector_job(stream_id: Optional[str]) -> None:
    if _redis and stream_id:
        await _redis.xack(settings.CONNECTOR_STREAM_NAME, settings.CONNECTOR_CONSUMER_GROUP, stream_id)
    elif not _redis:
        try:
            local_connector_queue.task_done()
        except ValueError:
            pass


async def should_process_connector_job(job_id: str) -> bool:
    if not _redis:
        return True
    locked = await _redis.set(
        f"fh:connector:processing:{job_id}",
        str(time.time()),
        nx=True,
        ex=settings.CONNECTOR_PROCESSING_LOCK_SECONDS,
    )
    return bool(locked)


async def release_connector_job_lock(job_id: str) -> None:
    if _redis:
        await _redis.delete(f"fh:connector:processing:{job_id}")


async def send_connector_dead_letter(job: dict, error_class: str, error_message: str) -> None:
    if _redis:
        await _redis.xadd(
            settings.CONNECTOR_DLQ_STREAM_NAME,
            {"job": json.dumps(job, default=str), "error_class": error_class, "error_message": error_message},
            maxlen=settings.CONNECTOR_QUEUE_MAXLEN,
            approximate=True,
        )
    if db.pool:
        await db.pool.execute(
            """INSERT INTO connector_dead_letters (job_id, provider, action, room_id, actor_id, payload_hash, error_class, error_message)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
            job["id"],
            job["provider"],
            job["action"],
            job.get("room_id"),
            job["actor_id"],
            job["payload_hash"],
            error_class,
            error_message[:1000],
        )
