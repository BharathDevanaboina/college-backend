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
from app.modules.gallery import service
from app.modules.gallery.schemas import GalleryOut, GalleryUpdate

admin_router = APIRouter(
    prefix="/gallery",
    tags=["Admin: gallery"],
    dependencies=[Depends(require_admin)],
)


@admin_router.get("", response_model=list[GalleryOut], summary="List gallery images")
def list_gallery(db: Session = Depends(get_db)) -> list[GalleryOut]:
    return [service.to_out(image) for image in service.list_images(db)]


@admin_router.post(
    "",
    response_model=GalleryOut,
    status_code=201,
    summary="Add a gallery image (multipart form)",
)
def add_gallery_image(
    image: UploadFile = File(...),
    caption: str | None = Form(default=None),
    display_order: int = Form(default=0, ge=0, le=100000),
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> GalleryOut:
    data = read_upload(image, max_mb=settings.max_image_upload_mb)
    return service.add_image(db, storage, data=data, caption=caption, display_order=display_order)


@admin_router.patch(
    "/{image_id}",
    response_model=GalleryOut,
    summary="Update caption, order or visibility",
)
def update_gallery_image(
    image_id: uuid.UUID,
    body: GalleryUpdate,
    db: Session = Depends(get_db),
) -> GalleryOut:
    return service.update_image(db, image_id, body)


@admin_router.delete("/{image_id}", status_code=204, summary="Delete a gallery image")
def delete_gallery_image(
    image_id: uuid.UUID,
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_storage),
) -> Response:
    service.delete_image(db, storage, image_id)
    return Response(status_code=204)
