"""One read-only endpoint with everything the public website needs to display."""

from app.core.module import Module
from app.modules.public_site.router import public_router

module = Module(
    name="public_site",
    description="Aggregated, cacheable content for the website (settings, banners, courses, gallery, ...).",
    public_router=public_router,
    depends_on=(
        "site_settings",
        "courses",
        "batches",
        "brochures",
        "banners",
        "announcements",
        "gallery",
        "videos",
        "exam",
    ),
)
