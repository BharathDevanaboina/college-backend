from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.error import NotFound
from app.core.timeutil import utc_now
from app.modules.announcements.models import Announcement
from app.modules.announcements.schemas import AnnouncementIn, AnnouncementOut


def to_out(a: Announcement) -> AnnouncementOut:
    return AnnouncementOut.model_validate(a, from_attributes=True)


def list_all(db: Session) -> list[Announcement]:
    return list(
        db.scalars(
            select(Announcement).order_by(
                Announcement.display_order, Announcement.created_at.desc()
            )
        )
    )


def list_public(db: Session) -> list[Announcement]:
    now = utc_now()
    stmt = (
        select(Announcement)
        .where(
            Announcement.is_active.is_(True),
            or_(Announcement.starts_at.is_(None), Announcement.starts_at <= now),
            or_(Announcement.ends_at.is_(None), Announcement.ends_at >= now),
        )
        .order_by(Announcement.display_order, Announcement.created_at.desc())
    )
    return list(db.scalars(stmt))


def _get(db: Session, item_id: uuid.UUID) -> Announcement:
    item = db.get(Announcement, item_id)
    if item is None:
        raise NotFound("Announcement not found.")
    return item


def create(db: Session, data: AnnouncementIn) -> AnnouncementOut:
    item = Announcement(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return to_out(item)


def replace(
    db: Session, item_id: uuid.UUID, data: AnnouncementIn
) -> AnnouncementOut:
    item = _get(db, item_id)
    for key, value in data.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return to_out(item)


def delete(db: Session, item_id: uuid.UUID) -> None:
    db.delete(_get(db, item_id))
    db.commit()
