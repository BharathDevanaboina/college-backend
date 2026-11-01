from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class GalleryImage(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "gallery_images"

    caption: Mapped[str | None] = mapped_column(String(200), nullable=True)
    image_path: Mapped[str] = mapped_column(String(300), nullable=False)
    image_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    thumb_path: Mapped[str] = mapped_column(String(300), nullable=False)
    thumb_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    image_width: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    image_height: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=true())
