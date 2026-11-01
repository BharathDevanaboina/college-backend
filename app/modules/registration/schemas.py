from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.validation import clean_text
from app.modules.registration.constants import (
    INDIAN_STATES_AND_UTS,
    QUALIFICATIONS,
    year_options,
)

INDIAN_MOBILE = re.compile(r"^[6-9]\d{9}$")


def normalise_indian_mobile(value: str) -> str:
    """Accept common Indian mobile formats and return a +91-prefixed number."""
    digits = re.sub(r"[\s\-()]", "", value or "")
    if digits.startswith("+91"):
        digits = digits[3:]
    elif len(digits) == 12 and digits.startswith("91"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]

    if not INDIAN_MOBILE.fullmatch(digits):
        raise ValueError("Please enter a valid 10-digit Indian mobile number")

    return "+91" + digits


class RegistrationForm(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(examples=["Ravi Kumar"])
    mobile: str = Field(examples=["9876543210"])
    email: EmailStr | None = None
    highest_qualification: str | None = Field(default=None, examples=["B.Com"])
    year_passed_out: str | None = Field(default=None, examples=["2024"])
    city: str | None = Field(default=None, examples=["Hyderabad"])
    state: str | None = Field(default=None, examples=["Telangana"])

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        value = clean_text(value, max_length=100, allow_empty=False)
        if len(value) < 2 or any(char.isdigit() for char in value):
            raise ValueError("Please enter your full name")
        return value

    @field_validator("mobile")
    @classmethod
    def _mobile(cls, value: str) -> str:
        return normalise_indian_mobile(value)

    @field_validator(
        "email",
        "highest_qualification",
        "year_passed_out",
        "city",
        "state",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("highest_qualification")
    @classmethod
    def _qualification(cls, value):
        if value is not None and value not in QUALIFICATIONS:
            raise ValueError("Please choose a qualification from the list")
        return value

    @field_validator("year_passed_out")
    @classmethod
    def _year(cls, value):
        if value is not None and value not in year_options():
            raise ValueError("Please choose a year from the list")
        return value

    @field_validator("state")
    @classmethod
    def _state(cls, value):
        if value is not None and value not in INDIAN_STATES_AND_UTS:
            raise ValueError("Please choose a state from the list")
        return value

    @field_validator("city")
    @classmethod
    def _city(cls, value):
        return clean_text(value, max_length=100)


class RegistrationSubmission(RegistrationForm):
    """Registration form plus the Firebase ID token returned after OTP verification."""

    firebase_id_token: str = Field(
        min_length=10,
        description="ID token from Firebase Phone Auth (signInWithPhoneNumber)",
    )


class RegistrationOptions(BaseModel):
    qualifications: list[str]
    years_passed_out: list[str]
    states: list[str]
