from __future__ import annotations

from sqlalchemy.orm import Session

from app.modules.site_settings.models import SiteSettings
from app.modules.site_settings.schemas import (
    SiteSettingsOut,
    SiteSettingsUpdate,
    SocialLinks,
)


def _get_or_create(db: Session) -> SiteSettings:
    row = db.get(SiteSettings, 1)
    if row is None:
        row = SiteSettings(id=1, social_links={})
        db.add(row)
        db.flush()
    return row


def to_out(row: SiteSettings) -> SiteSettingsOut:
    return SiteSettingsOut(
        phone=row.phone,
        whatsapp=row.whatsapp,
        email=row.email,
        address=row.address,
        google_form_url=row.google_form_url,
        social_links=SocialLinks(**(row.social_links or {})),
    )


def get_settings_out(db: Session) -> SiteSettingsOut:
    return to_out(_get_or_create(db))


def update_settings(
    db: Session,
    data: SiteSettingsUpdate,
) -> SiteSettingsOut:
    row = _get_or_create(db)
    row.phone = data.phone
    row.whatsapp = data.whatsapp
    row.email = str(data.email) if data.email else None
    row.address = data.address
    row.google_form_url = data.google_form_url
    row.social_links = data.social_links.model_dump(exclude_none=True)
    db.commit()
    return to_out(row)
