from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, String, true,Uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.courses.models import Course


class Batch(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "batches"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="dates_in_order"),
        CheckConstraint("mode IN ('online', 'offline')", name="valid_mode"),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    timings: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[str] = mapped_column(
        String(10), nullable=False, default="online", server_default="true"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )

    course: Mapped[Course] = relationship(lazy="joined")
