"""Batches module: manage course batches and schedules."""

from app.core.module import Module
from app.modules.batches.router import admin_router

module = Module(
    name="batches",
    description="Upcoming and ongoing batches for each course.",
    admin_router=admin_router,
    depends_on=("admin_auth", "courses"),
)
