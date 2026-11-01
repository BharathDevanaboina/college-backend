from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.admin_auth.dependencies import require_admin
from app.modules.videos import service
from app.modules.videos.schemas import VideoIn, VideoOut

admin_router = APIRouter(
    prefix="/videos",
    tags=["Admin: videos"],
    dependencies=[Depends(require_admin)],
)


@admin_router.get("", response_model=list[VideoOut], summary="List video links")
def list_videos(db: Session = Depends(get_db)) -> list[VideoOut]:
    return [service.to_out(v) for v in service.list_videos(db)]


@admin_router.post("", response_model=VideoOut, status_code=201, summary="Add a video link")
def create_video(body: VideoIn, db: Session = Depends(get_db)) -> VideoOut:
    return service.create(db, body)


@admin_router.put("/{video_id}", response_model=VideoOut, summary="Update a video link")
def update_video(
    video_id: uuid.UUID,
    body: VideoIn,
    db: Session = Depends(get_db),
) -> VideoOut:
    return service.replace(db, video_id, body)


@admin_router.delete("/{video_id}", status_code=204, summary="Delete a video link")
def delete_video(
    video_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    service.delete(db, video_id)
    return Response(status_code=204)
