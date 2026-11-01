from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.error import NotFound, ValidationFailed
from app.modules.videos.links import parse_video_link
from app.modules.videos.models import Video
from app.modules.videos.schemas import VideoIn, VideoOut


def to_out(v: Video) -> VideoOut:
    return VideoOut.model_validate(v, from_attributes=True)


def list_videos(db: Session, *, active_only: bool = False) -> list[Video]:
    stmt = select(Video).order_by(
        Video.display_order, Video.created_at.desc()
    )
    if active_only:
        stmt = stmt.where(Video.is_active.is_(True))
    return list(db.scalars(stmt))


def _get(db: Session, video_id: uuid.UUID) -> Video:
    item = db.get(Video, video_id)
    if item is None:
        raise NotFound("Video not found.")
    return item


def _apply(item: Video, data: VideoIn) -> None:
    try:
        link = parse_video_link(data.url)
    except ValueError as exc:
        raise ValidationFailed(str(exc), code="INVALID_VIDEO_LINK") from exc

    item.title = data.title
    item.url, item.platform, item.video_id, item.embed_url = (
        link.url,
        link.platform,
        link.video_id,
        link.embed_url,
    )
    item.display_order = data.display_order
    item.is_active = data.is_active


def create(db: Session, data: VideoIn) -> VideoOut:
    item = Video()
    _apply(item, data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return to_out(item)


def replace(db: Session, video_id: uuid.UUID, data: VideoIn) -> VideoOut:
    item = _get(db, video_id)
    _apply(item, data)
    db.commit()
    db.refresh(item)
    return to_out(item)


def delete(db: Session, video_id: uuid.UUID) -> None:
    db.delete(_get(db, video_id))
    db.commit()
