from __future__ import annotations

from sqlalchemy import JSON, CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin


class SiteSettings(TimestampMixin, Base):
    """A single row (id = 1) holding site-wide contact details."""

    __tablename__ = "site_settings"
    __table_args__ = (CheckConstraint("id = 1", name="single_row"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    phone: Mapped[str | None] = mapped_column(String(30))
    whatsapp: Mapped[str | None] = mapped_column(String(30))
    email: Mapped[str | None] = mapped_column(String(320))
    address: Mapped[str | None] = mapped_column(Text)
    google_form_url: Mapped[str | None] = mapped_column(String(500))
    social_links: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
