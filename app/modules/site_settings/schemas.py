from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.core.validation import clean_text, validate_http_url, validate_phone

SOCIAL_NETWORKS = ("facebook", "instagram", "youtube", "linkedin", "x")


class SocialLinks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facebook: str | None = None
    instagram: str | None = None
    youtube: str | None = None
    linkedin: str | None = None
    x: str | None = None

    _urls = field_validator(*SOCIAL_NETWORKS)(validate_http_url)


class SiteSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phone: str | None = None
    whatsapp: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    google_form_url: str | None = None
    social_links: SocialLinks = SocialLinks()

    _phones = field_validator("phone", "whatsapp")(validate_phone)
    _form = field_validator("google_form_url")(validate_http_url)

    @field_validator("email", mode="before")
    @classmethod
    def _empty_email(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("address")
    @classmethod
    def _address(cls, value):
        return clean_text(value, max_length=500)


class SiteSettingsOut(BaseModel):
    phone: str | None
    whatsapp: str | None
    email: str | None
    address: str | None
    google_form_url: str | None
    social_links: SocialLinks
