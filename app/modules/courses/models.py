from __future__ import annotations

from sqlalchemy import Boolean, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Course(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "courses"

    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    duration_text: Mapped[str] = mapped_column(String(68), nullable=False, default="")
    summary: Mapped[str | None] = mapped_column(Text)
    eligibility: Mapped[str | None] = mapped_column(Text)
    total_fee_inr: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fee_note: Mapped[str | None] = mapped_column(String(300))
    # Example: [{"label": "Year 1", "amount_inr": 100000}]
    fee_breakup: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
