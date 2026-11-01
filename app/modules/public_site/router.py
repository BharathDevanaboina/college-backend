from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.modules.public_site import service
from app.modules.public_site.schemas import PublicSite

public_router = APIRouter(prefix="/public", tags=["Public: website content"])


@public_router.get(
    "/site",
    response_model=PublicSite,
    summary="Everything the website displays, in one call",
)
def public_site(
    response: Response,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> PublicSite:
    # Cached by the Firebase Hosting CDN for 60 seconds; admin changes appear within a minute.
    response.headers["Cache-Control"] = "public, max-age=0, s-maxage=60"
    return service.build_site(db, settings)
