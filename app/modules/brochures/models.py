from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.courses.models import Course


class Brochure(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "brochures"

    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    file_path: Mapped[str] = mapped_column(String(300), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    course: Mapped[Course] = relationship(lazy="joined")
