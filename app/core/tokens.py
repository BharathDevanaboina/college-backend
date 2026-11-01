"""Short-lived signed tokens issued by this backend (e.g. the exam attempt token)."""

from __future__ import annotations

import time
from typing import Any

import jwt

from app.core.error import Gone, Unauthorized

ISSUER = "college-backend"


def sign_token(payload: dict[str, Any], *, audience: str, expires_in_seconds: int, secret: str) -> str:
    now = int(time.time())
    claims = {**payload, "iss": ISSUER, "aud": audience, "iat": now, "exp": now + expires_in_seconds}
    return jwt.encode(claims, secret, algorithm="HS256")


def verify_token(token: str, *, audience: str, secret: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, secret, algorithms=["HS256"], audience=audience, issuer=ISSUER)
    except jwt.ExpiredSignatureError as exc:
        raise Gone("This exam session has expired.", code="TOKEN_EXPIRED") from exc
    except jwt.InvalidTokenError as exc:
        raise Unauthorized("Invalid or tampered token.", code="TOKEN_INVALID") from exc
