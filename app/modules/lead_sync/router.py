from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.dependencies import get_sheets, require_internal_caller
from app.core.sheets import SheetsClient
from app.modules.admin_auth.dependencies import require_admin
from app.modules.lead_sync import service
from app.modules.lead_sync.schemas import FlushResult, SyncStatus

internal_router = APIRouter(
    prefix="/lead-sync", tags=["Internal"], dependencies=[Depends(require_internal_caller)]
)
admin_router = APIRouter(
    prefix="/lead-sync", tags=["Admin: Google Sheets sync"], dependencies=[Depends(require_admin)]
)


@internal_router.post("/flush", response_model=FlushResult, summary="Retry queued rows (Cloud Scheduler)")
def internal_flush(db: Session = Depends(get_db), sheets: SheetsClient = Depends(get_sheets)) -> FlushResult:
    return service.flush(db, sheets)


@admin_router.get(
    "/status",
    response_model=SyncStatus,
    summary="How many submissions are waiting for Google Sheets",
)
def sync_status(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> SyncStatus:
    status = service.status(db)
    if settings.sheets_spreadsheet_id:
        return status.model_copy(
            update={
                "spreadsheet_url": (
                    f"https://docs.google.com/spreadsheets/d/{settings.sheets_spreadsheet_id}"
                )
            }
        )
    return status


@admin_router.post("/flush", response_model=FlushResult, summary="Retry queued rows now")
def admin_flush(db: Session = Depends(get_db), sheets: SheetsClient = Depends(get_sheets)) -> FlushResult:
    return service.flush(db, sheets)
