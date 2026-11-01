from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.validation import clean_text, validate_http_url


class _AnnouncementFields(BaseModel):
    model_config = ConfigDict(extra="forbid")

    link_url: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    display_order: int = Field(default=0, ge=0, le=1000)
    is_active: bool = True

    _link = field_validator("link_url")(validate_http_url)

    @model_validator(mode="after")
    def _window(self):
        if self.starts_at and self.ends_at and self.ends_at < self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class AnnouncementIn(_AnnouncementFields):
    """Used for both create (POST) and full update (PUT)."""

    message: str

    @field_validator("message")
    @classmethod
    def _message(cls, v: str) -> str:
        return clean_text(v, max_length=500, allow_empty=False)


class AnnouncementOut(BaseModel):
    id: uuid.UUID
    message: str
    link_url: str | None
    starts_at: datetime | None
    ends_at: datetime | None
    display_order: int
    is_active: bool
