"""Simple in-memory rate limiting for FastAPI endpoints."""

from __future__ import annotations

import time
import threading
from collections import defaultdict, deque
from typing import Deque

from fastapi import Depends, HTTPException, Request, status

from app.core.config import Settings, get_settings



class RateLimiter:
    """Track request timestamps per key using a sliding time window.

    Note: this in-memory implementation is suitable for a single process.
    For multiple workers or instances, use a shared store such as Redis.
    """

    def __init__(self) -> None:
        self._hits: dict[str, Deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def hit(self, key: str, limit: int, window_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        hits = self._hits[key]

        while hits and hits[0] <= cutoff:
            hits.popleft()

        if len(hits) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": str(max(1, int(window_seconds)))},
            )

        hits.append(now)

    def reset(self) -> None:
        self._hits.clear()


limiter = RateLimiter()


def client_ip(request: Request) -> str:
    """Return the apparent client IP.

    Only trust X-Forwarded-For when it is set by a trusted reverse proxy.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(
    bucket: str,
    *,
    limit: int,
    window_seconds: int,
):
    """FastAPI dependency factory for applying a rate limit."""

    def _dependency(
        request: Request,
        settings: Settings = Depends(get_settings),
    ) -> None:
        if settings.rate_limit_enabled:
            limiter.hit(
                f"{bucket}:{client_ip(request)}",
                limit,
                window_seconds,
            )

    return _dependency
