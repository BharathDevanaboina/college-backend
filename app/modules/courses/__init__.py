"""Courses and fees module. Exactly three fixed courses: IBFAP, Advance B.Com and PGDM."""

from app.core.module import Module
from app.modules.courses.router import admin_router

module = Module(
    name="courses",
    description="Course details and fees (fixed list of three courses, editable by the admin).",
    admin_router=admin_router,
    depends_on=("admin_auth",),
)
