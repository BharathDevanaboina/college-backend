from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.dependencies import get_storage
from app.core.storage import FileStorage
from app.core.uploads import read_upload
from app.modules.admin_auth.dependencies import require_admin
from app.modules.banners import service
from app.modules.banners.schemas import BannerOut, BannerUpdate

admin_router = APIRouter(
    prefix="/banners",
    tags=["Admin: banners"],
    dependencies=[Depends(require_admin)],
)


@admin_router.get("/", response_model=list[BannerOut], summary="List all banners")
def list_banners(
    db: Session = Depends(get_db),
) -> list[BannerOut]:
    return [service.to_out(banner) for banner in service.list_banners(db)]


@admin_router.post(
    "/",
    response_model=BannerOut,
    status_code=201,
    summary="Add a banner (multipart form)",
)
def create_banner(
    title: str = Form(...),
    course_code: str | None = Form(
        default=None, description="IBFAP, ADV_BCOM or PGDM; leave empty for no button"
    ),
    display_order: int = Form(default=0),
    is_active: bool = Form(default=True),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> BannerOut:
    data = read_upload(image, max_mb=settings.max_image_upload_mb)
    return service.create_banner(
        db,
        storage,
        title=title,
        course_code=course_code or None,
        display_order=display_order,
        is_active=is_active,
        image_data=data,
    )


@admin_router.patch(
    "/{banner_id}",
    response_model=BannerOut,
    summary="Update banner details",
)
def update_banner(
    banner_id: uuid.UUID,
    body: BannerUpdate,
    db: Session = Depends(get_db),
) -> BannerOut:
    return service.update_banner(db, banner_id, body)


@admin_router.put(
    "/{banner_id}/image",
    response_model=BannerOut,
    summary="Replace the banner image",
)
def replace_banner_image(
    banner_id: uuid.UUID,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> BannerOut:
    return service.replace_image(
        db,
        storage,
        banner_id,
        read_upload(image, max_mb=settings.max_image_upload_mb),
    )


@admin_router.delete(
    "/{banner_id}",
    status_code=204,
    summary="Delete a banner",
)
def delete_banner(
    banner_id: uuid.UUID,
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_storage),
) -> Response:
    service.delete_banner(db, storage, banner_id)
    return Response(status_code=204)
