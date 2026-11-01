"""Brochures: one PDF per course, uploaded and replaced by the admin."""

from app.core.module import Module
from app.modules.brochures.router import admin_router

module = Module(
    name="brochures",
    description="Course brochure PDFs (stored privately; students get them via brochure_download).",
    admin_router=admin_router,
    depends_on=("admin_auth", "courses"),
)
