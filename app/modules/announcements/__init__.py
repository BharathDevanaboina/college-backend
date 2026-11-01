"""Announcements shown on the website (e.g. "Admissions open for 2026")."""

from app.core.module import Module
from app.modules.announcements.router import admin_router

module = Module(
    name="announcements",
    description="Short announcements with optional link and optional start/end dates.",
    admin_router=admin_router,
    depends_on=("admin_auth",),
)
