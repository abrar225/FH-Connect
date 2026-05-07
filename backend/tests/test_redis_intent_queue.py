import asyncio
import os
import uuid

import pytest

from app.core.event_bus import Event
from app.workers import queue

redis = pytest.importorskip("redis.asyncio")


def _redis_url() -> str:
    url = os.getenv("REDIS_TEST_URL")
    if not url:
        pytest.skip("REDIS_TEST_URL is not configured")
    return url


async def _cleanup(url: str, stream: str, group: str, event_id: str | None = None) -> None:
    client = redis.from_url(url, decode_responses=True)
    try:
        try:
            await client.xgroup_destroy(stream, group)
        except Exception:
            pass
        await client.delete(stream)
        if event_id:
            await client.delete(f"fh:intent:done:{event_id}", f"fh:intent:processing:{event_id}")
    finally:
        await client.aclose()


def _reset_metrics() -> None:
    for key in queue._metrics:
        queue._metrics[key] = 0


def test_redis_stream_recovers_pending_intent_message(monkeypatch):
    async def scenario():
        url = _redis_url()
        suffix = uuid.uuid4().hex
        stream = f"fh:test:intent:{suffix}"
        group = f"fh-test-intent-{suffix}"
        event = Event(event_type="intent.requested", meeting_id="room-a", payload={"text": "hello"})

        monkeypatch.setattr(queue.settings, "REDIS_URL", url)
        monkeypatch.setattr(queue.settings, "INTENT_STREAM_NAME", stream)
        monkeypatch.setattr(queue.settings, "INTENT_CONSUMER_GROUP", group)
        monkeypatch.setattr(queue.settings, "INTENT_PENDING_IDLE_MS", 0)
        monkeypatch.setattr(queue, "_consumer_name", "consumer-a")
        _reset_metrics()

        try:
            await queue.connect_intent_queue()
            assert await queue.enqueue_intent_event(event) is True

            received, stream_id = await queue.dequeue_intent_event()
            assert received.event_id == event.event_id
            assert stream_id is not None

            monkeypatch.setattr(queue, "_consumer_name", "consumer-b")
            recovered = await queue.recover_pending_intent_event()
            assert recovered is not None
            recovered_event, recovered_stream_id = recovered
            assert recovered_event.event_id == event.event_id
            assert recovered_stream_id == stream_id

            await queue.complete_intent_event(recovered_event, recovered_stream_id)
            metrics = await queue.intent_queue_metrics()
            assert metrics["backend"] == "redis_stream"
            assert metrics["pending"] == 0
            assert metrics["counters"]["recovered"] == 1
            assert metrics["counters"]["completed"] == 1
            assert metrics["alerts"]["pending_backlog"] is False
        finally:
            await queue.disconnect_intent_queue()
            await _cleanup(url, stream, group, event.event_id)

    asyncio.run(scenario())


def test_redis_stream_duplicate_done_marker_is_skipped(monkeypatch):
    async def scenario():
        url = _redis_url()
        suffix = uuid.uuid4().hex
        stream = f"fh:test:intent:{suffix}"
        group = f"fh-test-intent-{suffix}"
        event = Event(event_type="intent.requested", meeting_id="room-a")

        monkeypatch.setattr(queue.settings, "REDIS_URL", url)
        monkeypatch.setattr(queue.settings, "INTENT_STREAM_NAME", stream)
        monkeypatch.setattr(queue.settings, "INTENT_CONSUMER_GROUP", group)
        _reset_metrics()

        try:
            await queue.connect_intent_queue()
            assert await queue.should_process_intent_event(event) is True
            await queue.complete_intent_event(event, None)
            assert await queue.should_process_intent_event(event) is False

            metrics = await queue.intent_queue_metrics()
            assert metrics["counters"]["duplicates"] == 1
            assert metrics["counters"]["completed"] == 1
        finally:
            await queue.disconnect_intent_queue()
            await _cleanup(url, stream, group, event.event_id)

    asyncio.run(scenario())
