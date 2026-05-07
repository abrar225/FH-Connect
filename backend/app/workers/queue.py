import asyncio
import socket
import time
import uuid
from collections import deque
from typing import Deque, Dict, Optional, Tuple

from app.core.config import settings
from app.core.event_bus import Event
from app.core.logging import get_logger

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

logger = get_logger("intent_queue")

task_queue = asyncio.Queue(maxsize=settings.INTENT_QUEUE_LOCAL_MAXSIZE)
_redis = None
_consumer_name = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
_processed_local: Deque[str] = deque(maxlen=10_000)
_metrics: Dict[str, int] = {
    "enqueued": 0,
    "dequeued": 0,
    "recovered": 0,
    "completed": 0,
    "duplicates": 0,
    "failed": 0,
}


async def connect_intent_queue() -> None:
    global _redis
    if settings.REDIS_URL and redis:
        try:
            _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            try:
                await _redis.xgroup_create(
                    settings.INTENT_STREAM_NAME,
                    settings.INTENT_CONSUMER_GROUP,
                    id="0",
                    mkstream=True,
                )
            except Exception as exc:
                if "BUSYGROUP" not in str(exc):
                    raise
            logger.info("Intent queue connected to Redis Streams")
            return
        except Exception as exc:
            logger.error("Failed to connect Redis intent queue; using local queue", exc_info=exc)
            _redis = None

    logger.info("Intent queue running in local mode")


async def disconnect_intent_queue() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def enqueue_intent_event(event: Event) -> bool:
    if _redis:
        await _redis.xadd(
            settings.INTENT_STREAM_NAME,
            {"event": event.model_dump_json()},
            maxlen=settings.INTENT_QUEUE_MAXLEN,
            approximate=True,
        )
        _metrics["enqueued"] += 1
        return True

    try:
        task_queue.put_nowait(event)
        _metrics["enqueued"] += 1
        return True
    except asyncio.QueueFull:
        return False


async def dequeue_intent_event(timeout_ms: int = 5000) -> Tuple[Optional[Event], Optional[str]]:
    if _redis:
        recovered = await recover_pending_intent_event()
        if recovered:
            return recovered

        messages = await _redis.xreadgroup(
            settings.INTENT_CONSUMER_GROUP,
            _consumer_name,
            {settings.INTENT_STREAM_NAME: ">"},
            count=1,
            block=timeout_ms,
        )
        if not messages:
            return None, None

        _stream_name, stream_messages = messages[0]
        stream_id, fields = stream_messages[0]
        _metrics["dequeued"] += 1
        return Event.model_validate_json(fields["event"]), stream_id

    event = await task_queue.get()
    _metrics["dequeued"] += 1
    return event, None


async def recover_pending_intent_event() -> Optional[Tuple[Event, str]]:
    if not _redis:
        return None

    try:
        result = await _redis.xautoclaim(
            settings.INTENT_STREAM_NAME,
            settings.INTENT_CONSUMER_GROUP,
            _consumer_name,
            min_idle_time=settings.INTENT_PENDING_IDLE_MS,
            start_id="0-0",
            count=1,
        )
    except Exception as exc:
        logger.error("Failed to recover pending intent messages", exc_info=exc)
        return None

    messages = result[1] if len(result) > 1 else []
    if not messages:
        return None

    stream_id, fields = messages[0]
    _metrics["recovered"] += 1
    return Event.model_validate_json(fields["event"]), stream_id


async def ack_intent_event(stream_id: Optional[str]) -> None:
    if _redis and stream_id:
        await _redis.xack(settings.INTENT_STREAM_NAME, settings.INTENT_CONSUMER_GROUP, stream_id)
    elif not _redis:
        try:
            task_queue.task_done()
        except ValueError:
            pass


async def should_process_intent_event(event: Event) -> bool:
    if _redis:
        done_key = f"fh:intent:done:{event.event_id}"
        lock_key = f"fh:intent:processing:{event.event_id}"
        if await _redis.exists(done_key):
            _metrics["duplicates"] += 1
            return False
        locked = await _redis.set(
            lock_key,
            str(time.time()),
            ex=settings.INTENT_PROCESSING_LOCK_SECONDS,
            nx=True,
        )
        if not locked:
            _metrics["duplicates"] += 1
        return bool(locked)

    if event.event_id in _processed_local:
        _metrics["duplicates"] += 1
        return False
    return True


async def complete_intent_event(event: Event, stream_id: Optional[str]) -> None:
    if _redis:
        await _redis.set(f"fh:intent:done:{event.event_id}", "1", ex=86400)
        await _redis.delete(f"fh:intent:processing:{event.event_id}")
    else:
        _processed_local.append(event.event_id)

    _metrics["completed"] += 1
    await ack_intent_event(stream_id)


async def fail_intent_event(event: Optional[Event], stream_id: Optional[str]) -> None:
    _metrics["failed"] += 1
    if _redis and event:
        await _redis.delete(f"fh:intent:processing:{event.event_id}")
    elif not _redis and stream_id is None:
        try:
            task_queue.task_done()
        except ValueError:
            pass


async def intent_queue_metrics() -> dict:
    if _redis:
        try:
            length = await _redis.xlen(settings.INTENT_STREAM_NAME)
            groups = await _redis.xinfo_groups(settings.INTENT_STREAM_NAME)
            group = next((g for g in groups if g.get("name") == settings.INTENT_CONSUMER_GROUP), {})
            pending = group.get("pending", 0)
            alerts = {
                "pending_backlog": pending >= settings.INTENT_QUEUE_ALERT_PENDING,
                "failed_jobs": _metrics["failed"] >= settings.INTENT_QUEUE_ALERT_FAILED,
            }
            return {
                "backend": "redis_stream",
                "stream": settings.INTENT_STREAM_NAME,
                "length": length,
                "pending": pending,
                "consumers": group.get("consumers", 0),
                "last_delivered_id": group.get("last-delivered-id"),
                "counters": dict(_metrics),
                "pending_idle_recovery_ms": settings.INTENT_PENDING_IDLE_MS,
                "alerts": alerts,
            }
        except Exception as exc:
            logger.error("Failed to read Redis intent queue metrics", exc_info=exc)
            return {"backend": "redis_stream", "error": "metrics_unavailable"}

    alerts = {
        "pending_backlog": task_queue.qsize() >= settings.INTENT_QUEUE_ALERT_PENDING,
        "failed_jobs": _metrics["failed"] >= settings.INTENT_QUEUE_ALERT_FAILED,
    }
    return {
        "backend": "local",
        "size": task_queue.qsize(),
        "maxsize": settings.INTENT_QUEUE_LOCAL_MAXSIZE,
        "counters": dict(_metrics),
        "alerts": alerts,
    }
