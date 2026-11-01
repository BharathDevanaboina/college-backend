"""Delivers student submissions to Google Sheets, with automatic retry if Sheets is unavailable."""

from app.core.module import Module
from app.modules.lead_sync.router import admin_router, internal_router

module = Module(
    name="lead_sync",
    description="Google Sheets delivery plus a temporary retry queue (rows are deleted once delivered).",
    admin_router=admin_router,
    internal_router=internal_router,
    depends_on=("admin_auth",),
)
