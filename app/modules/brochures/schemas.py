from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class BrochureStatus(BaseModel):
    course_code: str
    course_name: str
    has_brochure: bool
    original_filename: str | None = None
    size_bytes: int | None = None
    updated_at: datetime | None = None
