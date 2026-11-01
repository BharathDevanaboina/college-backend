from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models import Base, UUIDPrimaryKeyMixin


class PendingSheetRow(UUIDPrimaryKeyMixin, Base):
    """A submission that could not be written to Google Sheets yet. Deleted as soon as it is delivered."""

    __tablename__ = "pending_sheet_rows"

    tab: Mapped[str] = mapped_column(String(160), nullable=False)
    headers: Mapped[list] = mapped_column(JSON, nullable=False)
    row: Mapped[list] = mapped_column(JSON, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    next_attempt_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
