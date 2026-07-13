"""Timeout, retry, and rate-limit handling for LLM providers."""
from __future__ import annotations

import logging
import time
import threading
from functools import wraps
from typing import Callable, TypeVar

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ---- Rate limiter (simple token bucket) ----

class RateLimiter:
    def __init__(self, calls_per_minute: int):
        self.min_interval = 60.0 / max(calls_per_minute, 1)
        self._lock = threading.Lock()
        self._next_call = 0.0

    def acquire(self):
        with self._lock:
            now = time.monotonic()
            wait = max(0.0, self._next_call - now)
            self._next_call = max(now, self._next_call) + self.min_interval
        # Reserve the slot under the lock, but do not hold the lock while sleeping.
        if wait > 0:
            logger.debug("Rate limiter: waiting %.1fs", wait)
            time.sleep(wait)


_rate_limiter = RateLimiter(settings.ai_rate_limit_per_minute)

# ---- Retryable errors ----

RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


def is_retryable(exc: Exception) -> bool:
    """Check if an exception is transient and worth retrying."""
    if hasattr(exc, "status_code"):
        return getattr(exc, "status_code") in RETRYABLE_STATUSES
    # Check for common transient error messages
    msg = str(exc).lower()
    transient = ("timeout", "connection", "rate limit", "too many requests",
                 "server error", "service unavailable", "overloaded")
    return any(t in msg for t in transient)


def with_retry(fn: Callable[[], T], description: str = "") -> T:
    """Execute fn with timeout, rate limiting, and retry logic.
    Raises the last exception if all retries are exhausted."""
    last_exc: Exception | None = None

    for attempt in range(settings.ai_max_retries + 1):
        try:
            _rate_limiter.acquire()
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt < settings.ai_max_retries and is_retryable(exc):
                wait = 2 ** attempt  # 1s, 2s, 4s
                logger.warning(
                    "%s attempt %d/%d failed (retryable), retrying in %ds: %s",
                    description, attempt + 1, settings.ai_max_retries + 1, wait, exc
                )
                time.sleep(wait)
            else:
                break

    logger.error("%s failed after %d attempts: %s", description, settings.ai_max_retries + 1, last_exc)
    raise last_exc  # type: ignore[misc]
