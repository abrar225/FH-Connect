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

    def __init__(self):
        origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        try:
            parsed = json.loads(origins)
            self.CORS_ORIGINS = parsed if isinstance(parsed, list) else [str(parsed)]
        except json.JSONDecodeError:
            self.CORS_ORIGINS = [origin.strip() for origin in origins.split(",") if origin.strip()]



settings = Settings()
