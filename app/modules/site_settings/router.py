from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.admin_auth.dependencies import require_admin
from app.modules.site_settings import service
from app.modules.site_settings.schemas import SiteSettingsOut, SiteSettingsUpdate

admin_router = APIRouter(
    prefix="/site-settings",
    tags=["Admin: site settings"],
    dependencies=[Depends(require_admin)],
)


@admin_router.get(
    "",
    response_model=SiteSettingsOut,
    summary="Get site settings",
)
def get_site_settings(
    db: Session = Depends(get_db),
) -> SiteSettingsOut:
    return service.get_settings_out(db)


@admin_router.put(
    "",
    response_model=SiteSettingsOut,
    summary="Replace site settings",
)
def put_site_settings(
    body: SiteSettingsUpdate,
    db: Session = Depends(get_db),
) -> SiteSettingsOut:
    return service.update_settings(db, body)
