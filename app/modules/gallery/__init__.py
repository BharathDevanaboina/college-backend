"""Photo gallery: images, optional caption, display order."""

from app.core.module import Module
from app.modules.gallery.router import admin_router

module = Module(
    name="gallery",
    description="Photo gallery images.",
    admin_router=admin_router,
    depends_on=("admin_auth",),
)
