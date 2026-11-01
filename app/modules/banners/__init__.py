"""Banner module: image banners with optional course brochure links."""

from app.core.module import Module
from app.modules.banners.router import admin_router

module = Module(
    name="banners",
    description="Banner slider images with an optional link to a course brochure.",
    admin_router=admin_router,
    depends_on=("admin_auth", "courses"),
)
