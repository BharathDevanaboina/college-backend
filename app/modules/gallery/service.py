from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.error import NotFound
from app.core.media import delete_files, store_image
from app.core.storage import FileStorage
from app.core.validation import clean_text
from app.modules.gallery.models import GalleryImage
from app.modules.gallery.schemas import GalleryOut, GalleryUpdate


def to_out(image: GalleryImage) -> GalleryOut:
    return GalleryOut.model_validate(image, from_attributes=True)


def list_images(db: Session, *, active_only: bool = False) -> list[GalleryImage]:
    stmt = select(GalleryImage).order_by(GalleryImage.display_order, GalleryImage.created_at.desc())
    if active_only:
        stmt = stmt.where(GalleryImage.is_active.is_(True))
    return list(db.scalars(stmt))


def get(db: Session, image_id: uuid.UUID) -> GalleryImage:
    item = db.get(GalleryImage, image_id)
    if item is None:
        raise NotFound("Gallery image not found.")
    return item


def add_image(
    db: Session,
    storage: FileStorage,
    *,
    data: bytes,
    caption: str | None,
    display_order: int,
) -> GalleryOut:
    caption = clean_text(caption, max_length=200)
    stored = store_image(storage, "gallery", data)
    item = GalleryImage(
        caption=caption,
        image_path=stored.large_path,
        image_url=stored.large_url,
        thumb_path=stored.thumb_path,
        thumb_url=stored.thumb_url,
        image_width=stored.width,
        image_height=stored.height,
        display_order=display_order,
    )
    try:
        db.add(item)
        db.commit()
        db.refresh(item)
    except Exception:
        db.rollback()
        # Storage cleanup may be needed here if the database insert fails.
        raise
    return to_out(item)


def update_image(db: Session, image_id: uuid.UUID, data: GalleryUpdate) -> GalleryOut:
    item = get(db, image_id)
    fields = data.model_fields_set
    if "caption" in fields:
        item.caption = data.caption
    if "display_order" in fields and data.display_order is not None:
        item.display_order = data.display_order
    if "is_active" in fields and data.is_active is not None:
        item.is_active = data.is_active
    db.commit()
    db.refresh(item)
    return to_out(item)


def delete_image(db: Session, storage: FileStorage, image_id: uuid.UUID) -> None:
    item = get(db, image_id)
    paths = (item.image_path, item.thumb_path)
    db.delete(item)
    db.commit()
    delete_files(storage, *paths)
