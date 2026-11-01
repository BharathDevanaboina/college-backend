from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.admin_auth.dependencies import require_admin
from app.modules.courses import service
from app.modules.courses.schemas import CourseOut, CourseUpdate

admin_router = APIRouter(
    prefix="/courses",
    tags=["Admin: courses and fees"],
    dependencies=[Depends(require_admin)],
)


@admin_router.get("", response_model=list[CourseOut], summary="List the three courses")
def list_courses(db: Session = Depends(get_db)) -> list[CourseOut]:
    return [service.to_out(course) for course in service.list_courses(db)]


@admin_router.get("/{code}", response_model=CourseOut, summary="Get one course")
def get_course(code: str, db: Session = Depends(get_db)) -> CourseOut:
    return service.to_out(service.get_course(db, code))


@admin_router.patch(
    "/{code}",
    response_model=CourseOut,
    summary="Update course details or fees",
)
def update_course(
    code: str,
    body: CourseUpdate,
    db: Session = Depends(get_db),
) -> CourseOut:
    return service.update_course(db, code, body)
