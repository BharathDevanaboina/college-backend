from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validation import clean_text


class GalleryUpdate(BaseModel):
    """Only supplied fields are changed. Send caption=null to remove the caption."""

    model_config = ConfigDict(extra="forbid")

    caption: str | None = None
    display_order: int | None = Field(default=None, ge=0, le=100000)
    is_active: bool | None = None

    @field_validator("caption")
    @classmethod
    def validate_caption(cls, value: str | None) -> str | None:
        return clean_text(value, max_length=200)


class GalleryOut(BaseModel):
    id: uuid.UUID
    caption: str | None
    image_url: str
    thumb_url: str
    image_width: int
    image_height: int
    display_order: int
    is_active: bool
