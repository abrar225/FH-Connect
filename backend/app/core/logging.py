"""
core/logging.py — Structured logging for the entire backend.

Provides a consistent logger factory with structured output format.
Every log line includes the module name, making it easy to trace
which domain produced a log entry.
"""

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone

from app.core.config import settings

request_id_var = contextvars.ContextVar("request_id", default="-")


def set_request_id(request_id: str):
    return request_id_var.set(request_id)


def reset_request_id(token) -> None:
    request_id_var.reset(token)


def get_request_id() -> str:
    return request_id_var.get()


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def get_logger(name: str) -> logging.Logger:
    """
    Returns a named logger with a consistent format.

    Usage:
        from app.core.logging import get_logger
        logger = get_logger("transcript")
        logger.info("Processing chunk", extra={"room_id": "abc"})
    """
    logger = logging.getLogger(f"fh.{name}")

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        if settings.ENVIRONMENT == "production":
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)-7s | %(name)-20s | req=%(request_id)s | %(message)s",
                datefmt="%H:%M:%S",
            )
        handler.setFormatter(formatter)
        handler.addFilter(RequestContextFilter())
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

    return logger
