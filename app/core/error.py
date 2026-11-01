"""Application errors and the JSON error format (RFC 9457 'problem details')."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import request_id_var

logger = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 400
    code = "BAD_REQUEST"
    title = "Bad request"

    def __init__(
        self,
        detail: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(detail)
        self.detail = detail
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        self.extra = extra or {}


class Unauthorized(AppError):
    status_code, code, title = 401, "UNAUTHENTICATED", "Authentication required"


class Forbidden(AppError):
    status_code, code, title = 403, "FORBIDDEN", "Not allowed"


class NotFound(AppError):
    status_code, code, title = 404, "NOT_FOUND", "Not found"


class Conflict(AppError):
    status_code, code, title = 409, "CONFLICT", "Conflict"


class Gone(AppError):
    status_code, code, title = 410, "GONE", "No longer available"


class PayloadTooLarge(AppError):
    status_code, code, title = 413, "PAYLOAD_TOO_LARGE", "File too large"


class ValidationFailed(AppError):
    status_code, code, title = 422, "VALIDATION_FAILED", "Validation failed"


class TooManyRequests(AppError):
    status_code, code, title = 429, "RATE_LIMITED", "Too many requests"


class ServiceUnavailable(AppError):
    status_code, code, title = 503, "SERVICE_UNAVAILABLE", "Service unavailable"


def _problem(
    status: int,
    title: str,
    code: str,
    detail: str,
    extra: dict[str, Any] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": title,
        "status": status,
        "code": code,
        "detail": detail,
        "request_id": request_id_var.get(),
    }
    if extra:
        body.update(jsonable_encoder(extra))
    headers = {}
    if "retry_after_seconds" in body:
        headers["Retry-After"] = str(body["retry_after_seconds"])
    return JSONResponse(
        body,
        status_code=status,
        media_type="application/problem+json",
        headers=headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return _problem(exc.status_code, exc.title, exc.code, exc.detail, exc.extra)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "field": ".".join(str(p) for p in err.get("loc", ()) if p != "body"),
                "message": err.get("msg"),
            }
            for err in exc.errors()
        ]
        return _problem(
            422,
            "Validation failed",
            "VALIDATION_FAILED",
            "Some fields are invalid.",
            {"errors": errors},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "HTTP_ERROR")
        return _problem(
            exc.status_code,
            str(exc.detail),
            code,
            str(exc.detail),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error", exc_info=exc)
        return _problem(
            500,
            "Internal error",
            "INTERNAL",
            "Something went wrong. Please try again.",
        )
