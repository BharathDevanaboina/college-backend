"""Request ID, access logging and security headers."""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request

from app.core.logging import request_id_var

logger = logging.getLogger("app.request")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "X-Frame-Options": "DENY",
}


def _request_id(request: Request) -> str:
    incoming = request.headers.get("x-request-id")
    if incoming and len(incoming) <= 100:
        return incoming
    trace = request.headers.get("x-cloud-trace-context")
    if trace:
        return trace.split("/")[0][:64]
    return uuid.uuid4().hex


def register_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def request_context(request: Request, call_next):
        token = request_id_var.set(_request_id(request))
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
            try:
                response.headers["X-Request-ID"] = request_id_var.get() or ""
                for key, value in SECURITY_HEADERS.items():
                    response.headers.setdefault(key, value)
                if "cache-control" not in response.headers:
                    response.headers["Cache-Control"] = "no-store"
                if request.url.path not in ("/api/v1/healthz",):
                    logger.info(
                        "request",
                        extra={
                            "method": request.method,
                            "path": request.url.path,
                            "status": response.status_code,
                            "duration_ms": elapsed_ms,
                        },
                    )
            finally:
                request_id_var.reset(token)
        return response
