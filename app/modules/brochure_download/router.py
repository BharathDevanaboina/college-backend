from __future__ import annotations

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.core.dependencies import (
    get_identity_verifier,
    get_sheets,
    get_storage,
    require_app_check,
)
from app.core.identity import IdentityVerifier
from app.core.rate_limit import rate_limit
from app.core.sheets import SheetsClient
from app.core.storage import FileStorage
from app.modules.brochure_download import service
from app.modules.registration.schemas import RegistrationSubmission

public_router = APIRouter(prefix="/brochures", tags=["Public: brochures"])


@public_router.post(
    "/{course_code}/download",
    summary="Submit the registration form (after OTP) and receive the course brochure PDF",
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}, "description": "The brochure PDF"}},
    dependencies=[
        Depends(require_app_check),
        Depends(rate_limit("brochure_download", limit=20, window_seconds=3600)),
    ],
)
def download_brochure(
    course_code: str,
    body: RegistrationSubmission,
    db: Session = Depends(get_db),
    storage: FileStorage = Depends(get_storage),
    sheets: SheetsClient = Depends(get_sheets),
    verifier: IdentityVerifier = Depends(get_identity_verifier),
    settings: Settings = Depends(get_settings),
) -> Response:
    pdf, filename = service.download(db, storage, sheets, verifier, settings, course_code, body)
    return Response(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
