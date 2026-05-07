import asyncio

from app.core.event_bus import Event
from app.workers import queue


def _drain_local_queue():
    while not queue.task_queue.empty():
        queue.task_queue.get_nowait()
        queue.task_queue.task_done()
    queue._processed_local.clear()
    for key in queue._metrics:
        queue._metrics[key] = 0


def test_local_intent_queue_round_trip(monkeypatch):
    monkeypatch.setattr(queue, "_redis", None)
    _drain_local_queue()

    event = Event(event_type="intent.requested", meeting_id="room-a", payload={"text": "hello"})

    assert asyncio.run(queue.enqueue_intent_event(event)) is True
    received, stream_id = asyncio.run(queue.dequeue_intent_event())

    assert stream_id is None
    assert received.event_id == event.event_id
    asyncio.run(queue.ack_intent_event(stream_id))


def test_local_intent_queue_idempotency(monkeypatch):
    monkeypatch.setattr(queue, "_redis", None)
    _drain_local_queue()

    event = Event(event_type="intent.requested")

    assert asyncio.run(queue.should_process_intent_event(event)) is True
    asyncio.run(queue.complete_intent_event(event, None))
    assert asyncio.run(queue.should_process_intent_event(event)) is False


def test_local_intent_queue_failure_metrics(monkeypatch):
    monkeypatch.setattr(queue, "_redis", None)
    monkeypatch.setattr(queue.settings, "INTENT_QUEUE_ALERT_FAILED", 1)
    _drain_local_queue()

    event = Event(event_type="intent.requested")

    asyncio.run(queue.fail_intent_event(event, None))

    metrics = asyncio.run(queue.intent_queue_metrics())
    assert metrics["counters"]["failed"] == 1
    assert metrics["alerts"]["failed_jobs"] is True


def test_local_intent_queue_metrics(monkeypatch):
    monkeypatch.setattr(queue, "_redis", None)
    _drain_local_queue()

    metrics = asyncio.run(queue.intent_queue_metrics())

    assert metrics["backend"] == "local"
    assert "size" in metrics
    assert "maxsize" in metrics
    assert metrics["counters"]["enqueued"] == 0
    assert metrics["alerts"]["pending_backlog"] is False
