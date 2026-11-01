from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validation import clean_text


class BannerUpdate(BaseModel):
    """Only the fields you send are changed. Send course_code=null to remove the brochure button."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    course_code: str | None = None
    display_order: int | None = Field(default=None, ge=0, le=1000)
    is_active: bool | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        return None if value is None else clean_text(value, max_length=150, allow_empty=False)


class BannerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    course_code: str | None
    image_url: str
    thumb_url: str
    image_width: int
    image_height: int
    display_order: int
    is_active: bool
