"""Student brochure download: registration form + OTP -> row in Google Sheets -> PDF."""

from app.core.module import Module
from app.modules.brochure_download.router import public_router

module = Module(
    name="brochure_download",
    description="Verified brochure downloads, recorded in the 'Brochure Downloads' sheet.",
    public_router=public_router,
    depends_on=("registration", "brochures", "courses", "lead_sync"),
)
