"""Reusable field validators."""

from __future__ import annotations

import re
from urllib.parse import urlparse

PHONE_RE = re.compile(r"^\+?[0-9][0-9 \-()]{6,18}[0-9]$")


def clean_text(value: str | None, *, max_length: int, allow_empty: bool = True) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        if allow_empty:
            return None
        raise ValueError("must not be empty")
    if len(value) > max_length:
        raise ValueError(f"must be at most {max_length} characters")
    if "<" in value or ">" in value:
        raise ValueError("must not contain < or >")
    return value


def validate_http_url(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc or len(value) > 500:
        raise ValueError("must be a valid http(s) link")
    return value


def validate_phone(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    value = value.strip()
    if not PHONE_RE.match(value):
        raise ValueError("must be a valid phone number")
    return value
