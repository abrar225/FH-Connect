from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

audio_worker_active = Gauge(
    "fh_audio_worker_active",
    "Whether an audio worker currently owns a room",
    ["room_id"],
)
livekit_track_subscribed_total = Counter(
    "fh_livekit_track_subscribed_total",
    "LiveKit audio tracks subscribed by backend workers",
    ["room_id"],
)
deepgram_ws_connect_total = Counter(
    "fh_deepgram_ws_connect_total",
    "Deepgram websocket connections opened",
    ["room_id"],
)
deepgram_ws_reconnect_total = Counter(
    "fh_deepgram_ws_reconnect_total",
    "Deepgram websocket reconnect attempts",
    ["room_id"],
)
deepgram_audio_frames_sent_total = Counter(
    "fh_deepgram_audio_frames_sent_total",
    "Audio frames sent to Deepgram",
    ["room_id"],
)
deepgram_audio_bytes_sent_total = Counter(
    "fh_deepgram_audio_bytes_sent_total",
    "Audio bytes sent to Deepgram",
    ["room_id"],
)
deepgram_transcript_final_total = Counter(
    "fh_deepgram_transcript_final_total",
    "Final transcripts received from Deepgram",
    ["room_id"],
)
deepgram_transcript_interim_total = Counter(
    "fh_deepgram_transcript_interim_total",
    "Interim transcripts received from Deepgram",
    ["room_id"],
)
deepgram_transcript_latency_seconds = Histogram(
    "fh_deepgram_transcript_latency_seconds",
    "Seconds between utterance start and Deepgram final transcript",
    ["room_id"],
    buckets=(0.25, 0.5, 1, 2, 5, 10, 30),
)
deepgram_dropped_frames_total = Counter(
    "fh_deepgram_dropped_frames_total",
    "Audio frames dropped before reaching Deepgram",
    ["room_id"],
)
deepgram_estimated_cost_usd_total = Counter(
    "fh_deepgram_estimated_cost_usd_total",
    "Estimated Deepgram transcription cost in USD",
    ["room_id"],
)
connector_jobs_total = Counter(
    "fh_connector_jobs_total",
    "Connector jobs by provider, action, and status",
    ["provider", "action", "status"],
)

# Error tracking metrics
api_errors_total = Counter(
    "fh_api_errors_total",
    "API errors by endpoint, method, and error code",
    ["endpoint", "method", "error_code"],
)
ai_service_errors_total = Counter(
    "fh_ai_service_errors_total",
    "AI service errors by provider and error type",
    ["provider", "error_type"],
)
circuit_breaker_open_total = Counter(
    "fh_circuit_breaker_open_total",
    "Circuit breaker open events by service",
    ["service"],
)
retry_attempts_total = Counter(
    "fh_retry_attempts_total",
    "Retry attempts by service and attempt number",
    ["service", "attempt"],
)
fallback_triggered_total = Counter(
    "fh_fallback_triggered_total",
    "Fallback behaviors triggered by service and type",
    ["service", "fallback_type"],
)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
