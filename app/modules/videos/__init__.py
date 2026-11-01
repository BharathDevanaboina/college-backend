"""Video links: YouTube videos, YouTube Shorts and Instagram Reels (links only, nothing uploaded)."""

from app.core.module import Module
from app.modules.videos.router import admin_router

module = Module(
    name="videos",
    description="YouTube / Shorts / Instagram Reel links with title and order.",
    admin_router=admin_router,
    depends_on=("admin_auth",),
)
