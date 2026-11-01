from __future__ import annotations

import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.validation import clean_text

Mode = Literal["online", "offline"]


class BatchCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    course_code: str = Field(examples=["PGDM"])
    start_date: date
    end_date: date
    timings: str = Field(examples=["10:00 AM - 1:00 PM"])
    mode: Mode
    is_active: bool = True

    @field_validator("timings")
    @classmethod
    def _timings(cls, value: str) -> str:
        return clean_text(value, max_length=100, allow_empty=False)

    @model_validator(mode="after")
    def _dates(self) -> BatchCreate:
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class BatchUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: date | None = None
    end_date: date | None = None
    timings: str | None = None
    mode: Mode | None = None
    is_active: bool | None = None

    @field_validator("timings")
    @classmethod
    def _timings(cls, value: str | None) -> str | None:
        return None if value is None else clean_text(value, max_length=100, allow_empty=False)


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_code: str
    course_name: str
    start_date: date
    end_date: date
    timings: str
    mode: Mode
    is_active: bool
