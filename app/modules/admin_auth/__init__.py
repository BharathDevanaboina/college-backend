"""Admin authentication module.

Firebase email/password sign-in plus a SQL allow-list.
"""

from app.core.module import Module
from app.modules.admin_auth.router import admin_router

module = Module(
    name="admin_auth",
    description="Checks admin Firebase tokens against the admin allow-list.",
    admin_router=admin_router,
)
