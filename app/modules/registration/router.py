from __future__ import annotations

from fastapi import APIRouter, Response

from app.modules.registration.constants import (
    INDIAN_STATES_AND_UTS,
    QUALIFICATIONS,
    year_options,
)
from app.modules.registration.schemas import RegistrationOptions

public_router = APIRouter(
    prefix="/registration",
    tags=["Public: registration"],
)


@public_router.get(
    "/options",
    response_model=RegistrationOptions,
    summary="Dropdown values for the registration form",
)
def registration_options(response: Response) -> RegistrationOptions:
    response.headers["Cache-Control"] = "public, max-age=3600"
    return RegistrationOptions(
        qualifications=list(QUALIFICATIONS),
        years_passed_out=year_options(),
        states=list(INDIAN_STATES_AND_UTS),
    )
