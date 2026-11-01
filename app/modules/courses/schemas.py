from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validation import clean_text


class FeeBreakupItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=50, examples=["Year 1"])
    amount_inr: int = Field(ge=0, le=100_000_000)

    @field_validator("label")
    @classmethod
    def clean_label(cls, value: str) -> str:
        return clean_text(value, max_length=50, allow_empty=False)


class FeeBreakupOut(FeeBreakupItem):
    amount_display: str


class CourseUpdate(BaseModel):
    """Only the fields supplied by the client are changed."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, max_length=120)
    duration_text: str | None = Field(default=None, max_length=68)
    summary: str | None = Field(default=None, max_length=3000)
    eligibility: str | None = Field(default=None, max_length=2000)
    total_fee_inr: int | None = Field(default=None, ge=0, le=100_000_000)
    fee_note: str | None = Field(default=None, max_length=300)
    fee_breakup: list[FeeBreakupItem] | None = Field(default=None, max_length=10)
    display_order: int | None = Field(default=None, ge=0, le=1000)
    is_active: bool | None = None

    @field_validator("name", "duration_text")
    @classmethod
    def required_text(cls, value: str | None) -> str | None:
        return None if value is None else clean_text(value, max_length=120, allow_empty=False)

    @field_validator("summary", "eligibility", "fee_note")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        return None if value is None else clean_text(value, max_length=3000)


class CourseOut(BaseModel):
    code: str
    name: str
    duration_text: str
    summary: str | None
    eligibility: str | None
    total_fee_inr: int
    total_fee_display: str
    fee_note: str | None
    fee_breakup: list[FeeBreakupOut]
    display_order: int
    is_active: bool
    updated_at: datetime | None
