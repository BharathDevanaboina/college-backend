"""Shared FastAPI dependencies. Tests replace these with fakes via
``app.dependency_overrides``.
"""

from __future__ import annotations

import hmac
from functools import lru_cache

from fastapi import Depends, Header

from app.core.config import Settings, get_settings
from app.core.error import Forbidden, Unauthorized
from app.core.identity import (
    FakeIdentityVerifier,
    FirebaseIdentityVerifier,
    IdentityVerifier,
)
from app.core.sheets import FakeSheetsClient, GoogleSheetsClient, SheetsClient
from app.core.storage import FileStorage, FirebaseStorage, LocalStorage


@lru_cache
def _storage() -> FileStorage:
    settings = get_settings()
    if settings.storage_backend == "local":
        return LocalStorage(settings.local_storage_dir, settings.public_base_url)
    return FirebaseStorage(settings.storage_bucket or "", settings.gcp_project_id)


@lru_cache
def _sheets() -> SheetsClient:
    settings = get_settings()
    if settings.sheets_backend == "fake":
        return FakeSheetsClient(settings.fake_sheets_dir)
    return GoogleSheetsClient(
        settings.sheets_spreadsheet_id or "",
        settings.sheets_timeout_seconds,
    )


@lru_cache
def _identity() -> IdentityVerifier:
    settings = get_settings()
    if settings.auth_mode == "fake":
        return FakeIdentityVerifier()
    return FirebaseIdentityVerifier(settings.gcp_project_id, settings.storage_bucket)


def get_storage() -> FileStorage:
    return _storage()


def get_sheets() -> SheetsClient:
    return _sheets()


def get_identity_verifier() -> IdentityVerifier:
    return _identity()


def require_app_check(
    x_firebase_appcheck: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    verifier: IdentityVerifier = Depends(get_identity_verifier),
) -> None:
    """Public write endpoints must come from the real website (Firebase App Check)."""
    if not settings.app_check_enabled:
        return
    if not x_firebase_appcheck:
        raise Unauthorized(
            "App verification is missing. Please reload the page.",
            code="APP_CHECK_FAILED",
        )
    verifier.verify_app_check(x_firebase_appcheck)


def require_internal_caller(
    authorization: str | None = Header(default=None),
    x_internal_token: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Protects /internal endpoints that Cloud Scheduler calls."""
    if settings.internal_auth_mode == "token":
        expected = settings.internal_task_token
        if not expected or not x_internal_token or not hmac.compare_digest(expected, x_internal_token):
            raise Unauthorized("Internal endpoint.", code="INTERNAL_AUTH_FAILED")
        return

    if not authorization or not authorization.startswith("Bearer "):
        raise Unauthorized("Internal endpoint.", code="INTERNAL_AUTH_FAILED")

    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token

    try:
        claims = id_token.verify_oauth2_token(
            authorization.removeprefix("Bearer "),
            google_requests.Request(),
            audience=settings.internal_oidc_audience,
        )
    except Exception as exc:
        raise Unauthorized("Internal endpoint.", code="INTERNAL_AUTH_FAILED") from exc

    email = (claims.get("email") or "").lower()
    if not claims.get("email_verified") or email not in settings.allowed_internal_service_accounts:
        raise Forbidden("Caller is not allowed.", code="INTERNAL_AUTH_FAILED")
