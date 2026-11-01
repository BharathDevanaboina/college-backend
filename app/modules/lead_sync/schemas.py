from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class FlushResult(BaseModel):
    delivered: int
    failed: int
    still_pending: int


class SyncStatus(BaseModel):
    pending_rows: int
    oldest_pending_since: datetime | None
    max_attempts_so_far: int
    spreadsheet_url: str | None = None
