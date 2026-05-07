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

logger = get_logger("report_queue")

report_queue = asyncio.Queue(maxsize=settings.REPORT_QUEUE_LOCAL_MAXSIZE)
_redis = None
_consumer_name = f"{socket.gethostname()}-{uuid.uuid4().hex[:8]}"
_processed_local: Deque[str] = deque(maxlen=5_000)
_metrics: Dict[str, int] = {
    "enqueued": 0,
    "dequeued": 0,
    "recovered": 0,
    "completed": 0,
    "duplicates": 0,
    "failed": 0,
}


async def connect_report_queue() -> None:
    global _redis
    if settings.REDIS_URL and redis:
        try:
            _redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
            try:
                await _redis.xgroup_create(
                    settings.REPORT_STREAM_NAME,
                    settings.REPORT_CONSUMER_GROUP,
                    id="0",
                    mkstream=True,
                )
            except Exception as exc:
                if "BUSYGROUP" not in str(exc):
                    raise
            logger.info("Report queue connected to Redis Streams")
            return
        except Exception as exc:
            logger.error("Failed to connect Redis report queue; using local queue", exc_info=exc)
            _redis = None

    logger.info("Report queue running in local mode")


async def disconnect_report_queue() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None


async def enqueue_report_event(event: Event) -> bool:
    if _redis:
        await _redis.xadd(
            settings.REPORT_STREAM_NAME,
            {"event": event.model_dump_json()},
            maxlen=settings.REPORT_QUEUE_MAXLEN,
            approximate=True,
        )
        _metrics["enqueued"] += 1
        return True

    try:
        report_queue.put_nowait(event)
        _metrics["enqueued"] += 1
        return True
    except asyncio.QueueFull:
        return False


async def dequeue_report_event(timeout_ms: int = 5000) -> Tuple[Optional[Event], Optional[str]]:
    if _redis:
        recovered = await recover_pending_report_event()
        if recovered:
            return recovered

        messages = await _redis.xreadgroup(
            settings.REPORT_CONSUMER_GROUP,
            _consumer_name,
            {settings.REPORT_STREAM_NAME: ">"},
            count=1,
            block=timeout_ms,
        )
        if not messages:
            return None, None

        _stream_name, stream_messages = messages[0]
        stream_id, fields = stream_messages[0]
        _metrics["dequeued"] += 1
        return Event.model_validate_json(fields["event"]), stream_id

    event = await report_queue.get()
    _metrics["dequeued"] += 1
    return event, None


async def recover_pending_report_event() -> Optional[Tuple[Event, str]]:
    if not _redis:
        return None

    try:
        result = await _redis.xautoclaim(
            settings.REPORT_STREAM_NAME,
            settings.REPORT_CONSUMER_GROUP,
            _consumer_name,
            min_idle_time=settings.REPORT_PENDING_IDLE_MS,
            start_id="0-0",
            count=1,
        )
    except Exception as exc:
        logger.error("Failed to recover pending report messages", exc_info=exc)
        return None

    messages = result[1] if len(result) > 1 else []
    if not messages:
        return None

    stream_id, fields = messages[0]
    _metrics["recovered"] += 1
    return Event.model_validate_json(fields["event"]), stream_id


async def ack_report_event(stream_id: Optional[str]) -> None:
    if _redis and stream_id:
        await _redis.xack(settings.REPORT_STREAM_NAME, settings.REPORT_CONSUMER_GROUP, stream_id)
    elif not _redis:
        try:
            report_queue.task_done()
        except ValueError:
            pass


async def should_process_report_event(event: Event) -> bool:
    if _redis:
        done_key = f"fh:report:done:{event.event_id}"
        lock_key = f"fh:report:processing:{event.event_id}"
        if await _redis.exists(done_key):
            _metrics["duplicates"] += 1
            return False
        locked = await _redis.set(
            lock_key,
            str(time.time()),
            ex=settings.REPORT_PROCESSING_LOCK_SECONDS,
            nx=True,
        )
        if not locked:
            _metrics["duplicates"] += 1
        return bool(locked)

    if event.event_id in _processed_local:
        _metrics["duplicates"] += 1
        return False
    return True


async def complete_report_event(event: Event, stream_id: Optional[str]) -> None:
    if _redis:
        await _redis.set(f"fh:report:done:{event.event_id}", "1", ex=86400)
        await _redis.delete(f"fh:report:processing:{event.event_id}")
    else:
        _processed_local.append(event.event_id)

    _metrics["completed"] += 1
    await ack_report_event(stream_id)


async def fail_report_event(event: Optional[Event], stream_id: Optional[str]) -> None:
    _metrics["failed"] += 1
    if _redis and event:
        await _redis.delete(f"fh:report:processing:{event.event_id}")
    elif not _redis and stream_id is None:
        await ack_report_event(stream_id)


async def report_queue_metrics() -> dict:
    if _redis:
        try:
            length = await _redis.xlen(settings.REPORT_STREAM_NAME)
            groups = await _redis.xinfo_groups(settings.REPORT_STREAM_NAME)
            group = next((g for g in groups if g.get("name") == settings.REPORT_CONSUMER_GROUP), {})
            pending = group.get("pending", 0)
            alerts = {
                "pending_backlog": pending >= settings.REPORT_QUEUE_ALERT_PENDING,
                "failed_jobs": _metrics["failed"] >= settings.REPORT_QUEUE_ALERT_FAILED,
            }
            return {
                "backend": "redis_stream",
                "stream": settings.REPORT_STREAM_NAME,
                "length": length,
                "pending": pending,
                "consumers": group.get("consumers", 0),
                "last_delivered_id": group.get("last-delivered-id"),
                "counters": dict(_metrics),
                "pending_idle_recovery_ms": settings.REPORT_PENDING_IDLE_MS,
                "alerts": alerts,
            }
        except Exception as exc:
            logger.error("Failed to read Redis report queue metrics", exc_info=exc)
            return {"backend": "redis_stream", "error": "metrics_unavailable"}

    alerts = {
        "pending_backlog": report_queue.qsize() >= settings.REPORT_QUEUE_ALERT_PENDING,
        "failed_jobs": _metrics["failed"] >= settings.REPORT_QUEUE_ALERT_FAILED,
    }
    return {
        "backend": "local",
        "size": report_queue.qsize(),
        "maxsize": settings.REPORT_QUEUE_LOCAL_MAXSIZE,
        "counters": dict(_metrics),
        "alerts": alerts,
    }
