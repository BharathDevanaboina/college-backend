from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.identity import IdentityVerifier
from app.core.sheets import SheetsClient
from app.core.storage import FileStorage
from app.modules.brochures import service as brochures
from app.modules.lead_sync import service as lead_sync
from app.modules.registration import service as registration
from app.modules.registration.schemas import RegistrationSubmission

SHEET_HEADERS = registration.SHEET_BASE_HEADERS + ["Course"]


def download(
    db: Session,
    storage: FileStorage,
    sheets: SheetsClient,
    verifier: IdentityVerifier,
    settings: Settings,
    course_code: str,
    submission: RegistrationSubmission,
) -> tuple[bytes, str]:
    verified = registration.verify_submission(submission, verifier, settings)
    pdf, filename, course_name = brochures.read_brochure(db, storage, course_code)
    lead_sync.deliver(
        db,
        sheets,
        settings.sheets_tab_brochure,
        SHEET_HEADERS,
        verified.sheet_values() + [course_name],
    )
    registration.release_phone_user(verified, verifier, settings)
    return pdf, filename
