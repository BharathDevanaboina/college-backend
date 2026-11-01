from __future__ import annotations

from fastapi import APIRouter, Depends, File, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.dependencies import get_storage
from app.core.storage import FileStorage
from app.core.uploads import read_upload
from app.modules.admin_auth.dependencies import require_admin
from app.modules.brochures import service
from app.modules.brochures.schemas import BrochureStatus

admin_router = APIRouter(
    prefix="/brochures",
    tags=["Admin: brochures"],
    dependencies=[Depends(require_admin)],
)


@admin_router.get(
    "",
    response_model=list[BrochureStatus],
    summary="Brochure status for each course",
)
def list_brochures(db: Session = Depends(get_db)) -> list[BrochureStatus]:
    return service.list_status(db)


@admin_router.put(
    "/{course_code}",
    response_model=BrochureStatus,
    summary="Upload or replace a course brochure (PDF)",
)
def upload_brochure(
    course_code: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> BrochureStatus:
    data = read_upload(file, max_mb=settings.max_pdf_upload_mb)
    return service.upload_brochure(
        db,
        storage,
        course_code,
        data,
        file.filename or "brochure.pdf",
    )


@admin_router.get(
    "/{course_code}/file",
    summary="Download the current brochure (admin preview)",
)
def get_brochure_file(
    course_code: str,
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_storage),
) -> Response:
    data, filename, _course_name = service.read_brochure(db, storage, course_code)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@admin_router.delete(
    "/{course_code}",
    status_code=204,
    summary="Remove a course brochure",
)
def delete_brochure(
    course_code: str,
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_storage),
) -> Response:
    service.delete_brochure(db, storage, course_code)
    return Response(status_code=204)
