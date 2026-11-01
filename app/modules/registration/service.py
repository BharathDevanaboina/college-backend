"""Verify that the student confirmed the submitted mobile number using Firebase Phone Auth."""

from __future__ import annotations

import time
from dataclasses import dataclass

from app.core.config import Settings
from app.core.error import Unauthorized, ValidationFailed
from app.core.identity import IdentityVerifier
from app.core.timeutil import format_ist, utc_now
from app.modules.registration.schemas import RegistrationSubmission

SHEET_BASE_HEADERS = [
    "Submitted At (IST)",
    "Name",
    "Mobile",
    "Email",
    "Highest Qualification",
    "Year Passed Out",
    "City",
    "State",
]


@dataclass(frozen=True)
class VerifiedRegistration:
    name: str
    mobile: str  # +91XXXXXXXXXX, verified by OTP
    email: str | None
    highest_qualification: str | None
    year_passed_out: str | None
    city: str | None
    state: str | None
    firebase_uid: str

    def sheet_values(self) -> list[str]:
        return [
            format_ist(utc_now()),
            self.name,
            self.mobile,
            self.email or "",
            self.highest_qualification or "",
            self.year_passed_out or "",
            self.city or "",
            self.state or "",
        ]


def verify_submission(
    submission: RegistrationSubmission,
    verifier: IdentityVerifier,
    settings: Settings,
) -> VerifiedRegistration:
    identity = verifier.verify_phone_token(submission.firebase_id_token)

    if identity.sign_in_provider != "phone" or not identity.phone_number:
        raise Unauthorized(
            "Please verify your mobile number with the OTP.",
            code="OTP_REQUIRED",
        )

    if identity.phone_number != submission.mobile:
        raise ValidationFailed(
            "The verified mobile number does not match the number in the form.",
            code="MOBILE_MISMATCH",
        )

    now = time.time()
    if identity.auth_time > now + 60 or now - identity.auth_time > settings.otp_max_age_seconds:
        raise Unauthorized(
            "Your OTP verification has expired. Please verify again.",
            code="OTP_EXPIRED",
        )

    return VerifiedRegistration(
        name=submission.name,
        mobile=submission.mobile,
        email=str(submission.email) if submission.email else None,
        highest_qualification=submission.highest_qualification,
        year_passed_out=submission.year_passed_out,
        city=submission.city,
        state=submission.state,
        firebase_uid=identity.uid,
    )


def release_phone_user(
    verified: VerifiedRegistration,
    verifier: IdentityVerifier,
    settings: Settings,
) -> None:
    """Delete the temporary Firebase phone user after the number is stored in Google Sheets."""
    if settings.delete_firebase_phone_user:
        verifier.delete_user(verified.firebase_uid)
