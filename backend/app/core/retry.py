"""
core/retry.py — Retry logic with exponential backoff for external services.

Provides decorators and utilities for retrying failed operations
with configurable backoff strategies.
"""

import asyncio
import functools
import random
import time
from typing import Any, Callable, Optional, Type, Tuple

from app.core.logging import get_logger

logger = get_logger("retry")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
        on_retry: Optional[Callable] = None,
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or (Exception,)
        self.on_retry = on_retry

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number."""
        delay = min(self.base_delay * (self.exponential_base ** attempt), self.max_delay)
        if self.jitter:
            delay = delay * (0.5 + random.random())  # 50-150% of calculated delay
        return delay


def with_retry(config: Optional[RetryConfig] = None):
    """
    Decorator to add retry logic to async functions.

    Usage:
        @with_retry(RetryConfig(max_attempts=3, base_delay=1.0))
        async def call_external_api():
            ...
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e

                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"Retry exhausted after {config.max_attempts} attempts [func={func.__name__}, error={type(e).__name__}]",
                            extra={"function": func.__name__, "attempts": config.max_attempts},
                        )
                        raise

                    delay = config.calculate_delay(attempt)
                    logger.warning(
                        f"Retrying after error [func={func.__name__}, attempt={attempt + 1}/{config.max_attempts}, delay={delay:.2f}s, error={type(e).__name__}]",
                        extra={
                            "function": func.__name__,
                            "attempt": attempt + 1,
                            "max_attempts": config.max_attempts,
                            "delay": delay,
                            "error_type": type(e).__name__,
                        },
                    )

                    if config.on_retry:
                        await config.on_retry(attempt, e)

                    await asyncio.sleep(delay)

            raise last_exception

        return wrapper
    return decorator


def with_retry_sync(config: Optional[RetryConfig] = None):
    """Synchronous version of with_retry decorator."""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e

                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"Retry exhausted after {config.max_attempts} attempts [func={func.__name__}, error={type(e).__name__}]",
                            extra={"function": func.__name__, "attempts": config.max_attempts},
                        )
                        raise

                    delay = config.calculate_delay(attempt)
                    logger.warning(
                        f"Retrying after error [func={func.__name__}, attempt={attempt + 1}/{config.max_attempts}, delay={delay:.2f}s]",
                        extra={"function": func.__name__, "attempt": attempt + 1, "delay": delay},
                    )

                    time.sleep(delay)

            raise last_exception

        return wrapper
    return decorator


# Predefined retry configurations for common use cases
AI_SERVICE_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
)

DATABASE_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=0.5,
    max_delay=10.0,
    exponential_base=2.0,
    jitter=True,
)

EXTERNAL_API_RETRY_CONFIG = RetryConfig(
    max_attempts=5,
    base_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True,
)


async def retry_async(
    func: Callable,
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> Any:
    """Utility function to retry an async function with config."""
    if config is None:
        config = AI_SERVICE_RETRY_CONFIG

    @with_retry(config)
    async def wrapped():
        return await func(*args, **kwargs)

    return await wrapped()