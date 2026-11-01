"""Site settings: contact numbers, email, address, Google Form link, social links."""

from app.core.module import Module
from app.modules.site_settings.router import admin_router

module = Module(
    name="site_settings",
    description="Contact details and links shown across the website.",
    admin_router=admin_router,
    depends_on=("admin_auth",),
)
