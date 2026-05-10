"""
core/config.py — Centralized configuration management.

All environment variables and settings are loaded once here.
Modules import from this file instead of calling os.getenv() themselves.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application-wide settings derived from environment variables."""

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")

    # ── LiveKit ───────────────────────────────────────────────────────────
    LIVEKIT_URL: str = os.getenv("LIVEKIT_URL", "")
    LIVEKIT_API_KEY: str = os.getenv("LIVEKIT_API_KEY", "")
    LIVEKIT_API_SECRET: str = os.getenv("LIVEKIT_API_SECRET", "")

    # ── Deepgram ──────────────────────────────────────────────────────────
    DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")

    # ── AI / LLM ──────────────────────────────────────────────────────────
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_PRIMARY_MODEL: str = os.getenv("GROQ_PRIMARY_MODEL", "llama-3.3-70b-versatile")
    GROQ_FALLBACK_MODEL: str = os.getenv("GROQ_FALLBACK_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_PRIMARY_MODEL: str = os.getenv("GEMINI_PRIMARY_MODEL", "gemini-2.5-flash")
    AI_KEY_ENCRYPTION_SECRET: str = os.getenv("AI_KEY_ENCRYPTION_SECRET", "")

    # ── Supabase ──────────────────────────────────────────────────────────
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # ── Application ───────────────────────────────────────────────────────
    APP_VERSION: str = "0.2.0"
    APP_NAME: str = "FH-Connect Backend"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    CORS_ORIGINS: list = []
    MAX_REQUEST_BYTES: int = int(os.getenv("MAX_REQUEST_BYTES", str(512 * 1024)))
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "240"))
    RATE_LIMIT_WINDOW_SECONDS: int = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

    # ── Intelligence thresholds ───────────────────────────────────────────
    INTENT_CONFIDENCE_THRESHOLD: float = float(os.getenv("INTENT_CONFIDENCE_THRESHOLD", "0.7"))
    FUZZY_MATCH_THRESHOLD: float = float(os.getenv("FUZZY_MATCH_THRESHOLD", "0.6"))

    # ── Redis ─────────────────────────────────────────────────────────────
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    INTENT_STREAM_NAME: str = os.getenv("INTENT_STREAM_NAME", "fh:intent:stream")
    INTENT_CONSUMER_GROUP: str = os.getenv("INTENT_CONSUMER_GROUP", "fh:intent-workers")
    INTENT_QUEUE_MAXLEN: int = int(os.getenv("INTENT_QUEUE_MAXLEN", "10000"))
    INTENT_QUEUE_LOCAL_MAXSIZE: int = int(os.getenv("INTENT_QUEUE_LOCAL_MAXSIZE", "100"))
    INTENT_PENDING_IDLE_MS: int = int(os.getenv("INTENT_PENDING_IDLE_MS", "60000"))
    INTENT_PROCESSING_LOCK_SECONDS: int = int(os.getenv("INTENT_PROCESSING_LOCK_SECONDS", "300"))
    REPORT_STREAM_NAME: str = os.getenv("REPORT_STREAM_NAME", "fh:report:stream")
    REPORT_CONSUMER_GROUP: str = os.getenv("REPORT_CONSUMER_GROUP", "fh:report-workers")
    REPORT_QUEUE_MAXLEN: int = int(os.getenv("REPORT_QUEUE_MAXLEN", "5000"))
    REPORT_QUEUE_LOCAL_MAXSIZE: int = int(os.getenv("REPORT_QUEUE_LOCAL_MAXSIZE", "50"))
    REPORT_PENDING_IDLE_MS: int = int(os.getenv("REPORT_PENDING_IDLE_MS", "120000"))
    REPORT_PROCESSING_LOCK_SECONDS: int = int(os.getenv("REPORT_PROCESSING_LOCK_SECONDS", "900"))
    INTENT_QUEUE_ALERT_PENDING: int = int(os.getenv("INTENT_QUEUE_ALERT_PENDING", "100"))
    INTENT_QUEUE_ALERT_FAILED: int = int(os.getenv("INTENT_QUEUE_ALERT_FAILED", "10"))
    REPORT_QUEUE_ALERT_PENDING: int = int(os.getenv("REPORT_QUEUE_ALERT_PENDING", "25"))
    REPORT_QUEUE_ALERT_FAILED: int = int(os.getenv("REPORT_QUEUE_ALERT_FAILED", "5"))
    RUN_EMBEDDED_WORKERS: bool = os.getenv("RUN_EMBEDDED_WORKERS", "true").lower() == "true"
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "true").lower() == "true"
    ENABLE_DEBUG_ENDPOINTS: bool = os.getenv("ENABLE_DEBUG_ENDPOINTS", "false").lower() == "true"
    METRICS_BEARER_TOKEN: str = os.getenv("METRICS_BEARER_TOKEN", "")
    REQUIRE_REDIS_FOR_DISTRIBUTED_WORKERS: bool = os.getenv("REQUIRE_REDIS_FOR_DISTRIBUTED_WORKERS", "false").lower() == "true"

    # ── Security Settings ─────────────────────────────────────────────────
    ENABLE_AUDIT_LOGGING: bool = os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true"
    AUDIT_LOG_MAX_DETENTION_DAYS: int = int(os.getenv("AUDIT_LOG_MAX_DETENTION_DAYS", "365"))
    ENABLE_INPUT_SANITIZATION: bool = os.getenv("ENABLE_INPUT_SANITIZATION", "true").lower() == "true"
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOGIN_LOCKOUT_DURATION_SECONDS: int = int(os.getenv("LOGIN_LOCKOUT_DURATION_SECONDS", "300"))

    # ── Distributed audio worker leases ───────────────────────────────────
    AUDIO_WORKER_LEASE_TTL_MS: int = int(os.getenv("AUDIO_WORKER_LEASE_TTL_MS", "90000"))
    AUDIO_WORKER_LEASE_RENEW_INTERVAL_SECONDS: int = int(os.getenv("AUDIO_WORKER_LEASE_RENEW_INTERVAL_SECONDS", "30"))
    AUDIO_WORKER_FRAME_QUEUE_MAXSIZE: int = int(os.getenv("AUDIO_WORKER_FRAME_QUEUE_MAXSIZE", "256"))
    DEEPGRAM_COST_PER_AUDIO_HOUR: float = float(os.getenv("DEEPGRAM_COST_PER_AUDIO_HOUR", "0.0043"))

    # ── Connector durable queue ───────────────────────────────────────────
    CONNECTOR_STREAM_NAME: str = os.getenv("CONNECTOR_STREAM_NAME", "fh:connector:stream")
    CONNECTOR_DLQ_STREAM_NAME: str = os.getenv("CONNECTOR_DLQ_STREAM_NAME", "fh:connector:dlq")
    CONNECTOR_CONSUMER_GROUP: str = os.getenv("CONNECTOR_CONSUMER_GROUP", "fh:connector-workers")
    CONNECTOR_QUEUE_MAXLEN: int = int(os.getenv("CONNECTOR_QUEUE_MAXLEN", "10000"))
    CONNECTOR_PENDING_IDLE_MS: int = int(os.getenv("CONNECTOR_PENDING_IDLE_MS", "120000"))
    CONNECTOR_PROCESSING_LOCK_SECONDS: int = int(os.getenv("CONNECTOR_PROCESSING_LOCK_SECONDS", "900"))
    CONNECTOR_MAX_ATTEMPTS: int = int(os.getenv("CONNECTOR_MAX_ATTEMPTS", "5"))
    CONNECTOR_BACKOFF_SECONDS: list[int] = [60, 300, 900, 3600]
    CONNECTOR_SCHEDULED_ZSET_NAME: str = os.getenv("CONNECTOR_SCHEDULED_ZSET_NAME", "fh:connector:scheduled")
    CONNECTOR_SCHEDULER_INTERVAL_SECONDS: int = int(os.getenv("CONNECTOR_SCHEDULER_INTERVAL_SECONDS", "5"))

    def validate_production(self) -> None:
        if self.ENVIRONMENT != "production":
            return
        missing = [
            name for name, value in {
                "DATABASE_URL": self.DATABASE_URL,
                "REDIS_URL": self.REDIS_URL,
                "LIVEKIT_URL": self.LIVEKIT_URL,
                "LIVEKIT_API_KEY": self.LIVEKIT_API_KEY,
                "LIVEKIT_API_SECRET": self.LIVEKIT_API_SECRET,
                "DEEPGRAM_API_KEY": self.DEEPGRAM_API_KEY,
                "AI_KEY_ENCRYPTION_SECRET": self.AI_KEY_ENCRYPTION_SECRET,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing production configuration: {', '.join(missing)}")
        if self.ENABLE_METRICS and not self.METRICS_BEARER_TOKEN:
            raise RuntimeError("METRICS_BEARER_TOKEN is required when metrics are enabled in production")

    def __init__(self):
        origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        try:
            parsed = json.loads(origins)
            self.CORS_ORIGINS = parsed if isinstance(parsed, list) else [str(parsed)]
        except json.JSONDecodeError:
            self.CORS_ORIGINS = [origin.strip() for origin in origins.split(",") if origin.strip()]



settings = Settings()
