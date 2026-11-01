from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.admin_auth.dependencies import require_admin
from app.modules.announcements import service
from app.modules.announcements.schemas import AnnouncementIn, AnnouncementOut

admin_router = APIRouter(
    prefix="/announcements", tags=["Admin: announcements"], dependencies=[Depends(require_admin)]
)


@admin_router.get("", response_model=list[AnnouncementOut], summary="List all announcements")
def list_announcements(db: Session = Depends(get_db)) -> list[AnnouncementOut]:
    return [service.to_out(a) for a in service.list_all(db)]


@admin_router.post("", response_model=AnnouncementOut, status_code=201, summary="Add an announcement")
def create_announcement(body: AnnouncementIn, db: Session = Depends(get_db)) -> AnnouncementOut:
    return service.create(db, body)


@admin_router.put("/{item_id}", response_model=AnnouncementOut, summary="Update an announcement")
def update_announcement(
    item_id: uuid.UUID, body: AnnouncementIn, db: Session = Depends(get_db)
) -> AnnouncementOut:
    return service.replace(db, item_id, body)


@admin_router.delete("/{item_id}", status_code=204, summary="Delete an announcement")
def delete_announcement(item_id: uuid.UUID, db: Session = Depends(get_db)) -> Response:
    service.delete(db, item_id)
    return Response(status_code=204)
