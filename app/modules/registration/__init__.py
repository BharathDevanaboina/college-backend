"""The single student registration form + OTP check, shared by brochure downloads and the exam."""

from app.core.module import Module
from app.modules.registration.router import public_router

module = Module(
    name="registration",
    description="Registration form fields, dropdown options and Firebase phone-OTP verification.",
    public_router=public_router,
)
