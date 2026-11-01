"""Reusable require_admin dependency for admin routes."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.dependencies import get_identity_verifier
from app.core.error import Forbidden, Unauthorized
from app.core.identity import IdentityVerifier
from app.modules.admin_auth import service


@dataclass(frozen=True)
class AdminPrincipal:
    admin_id: str
    email: str
    firebase_uid: str


def require_admin(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    verifier: IdentityVerifier = Depends(get_identity_verifier),
) -> AdminPrincipal:
    if not authorization or not authorization.startswith("Bearer "):
        raise Unauthorized("Missing admin sign-in.")

    identity = verifier.verify_admin_token(authorization.removeprefix("Bearer ").strip())
    if not identity.email or not identity.email_verified:
        raise Forbidden("Your email address is not verified.", code="EMAIL_NOT_VERIFIED")
    if settings.require_admin_mfa and not identity.mfa_verified:
        raise Forbidden("Please complete the Google Authenticator step.", code="MFA_REQUIRED")

    admin = service.get_active_admin(db, identity.email)
    if admin is None:
        raise Forbidden("This account does not have admin access.", code="NOT_AN_ADMIN")

    service.record_login(db, admin, identity.uid)
    return AdminPrincipal(
        admin_id=str(admin.id),
        email=admin.email,
        firebase_uid=identity.uid,
    )
