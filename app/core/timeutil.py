"""Time helpers. The college works in Indian Standard Time (IST)."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30), name="IST")


def utc_now() -> datetime:
    return datetime.now(UTC)


def ist_now() -> datetime:
    return datetime.now(IST)


def ist_today() -> date:
    return ist_now().date()


def format_ist(dt: datetime) -> str:
    return dt.astimezone(IST).strftime("%Y-%m-%d %H:%M:%S")
