from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validation import clean_text


class VideoIn(BaseModel):
    """Used for both create (POST) and full update (PUT)."""

    model_config = ConfigDict(extra="forbid")

    title: str
    url: str = Field(examples=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"])
    display_order: int = Field(default=0, ge=0, le=1000)
    is_active: bool = True

    @field_validator("title")
    @classmethod
    def _title(cls, v: str) -> str:
        return clean_text(v, max_length=150, allow_empty=False)


class VideoOut(BaseModel):
    id: uuid.UUID
    title: str
    url: str
    platform: str
    video_id: str
    embed_url: str
    display_order: int
    is_active: bool
