"""SQLAlchemy models reconstructed from the supplied screenshots.

The screenshots show definitions through ExamOption. Additional fields or classes
may exist beyond the visible area of the original file.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON, Boolean, CheckConstraint, DateTime, ForeignKey, Integer,
    String, Text, Uuid, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models import Base, UUIDPrimaryKeyMixin


class ExamSet(UUIDPrimaryKeyMixin, Base):
    """One of the three question sets. Sets are never edited: delete one and upload a new one."""

    __tablename__ = "exam_sets"
    __table_args__ = (CheckConstraint("slot BETWEEN 1 AND 3", name="valid_slot"),)

    slot: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    source_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by: Mapped[str] = mapped_column(String(320), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ExamPassage(UUIDPrimaryKeyMixin, Base):
    """A reading passage shared by several questions (kept together when shuffling)."""

    __tablename__ = "exam_passages"

    exam_set_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exam_sets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    passage_key: Mapped[str] = mapped_column(String(50), nullable=False)
    section: Mapped[str] = mapped_column(String(1), nullable=False)
    content: Mapped[list] = mapped_column(JSON, nullable=False)


class ExamQuestion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "exam_questions"

    exam_set_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exam_sets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    passage_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("exam_passages.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)  # row order in uploaded file
    section: Mapped[str] = mapped_column(String(1), nullable=False)
    subsection: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[list] = mapped_column(JSON, nullable=False)
    options: Mapped[list["ExamOption"]] = relationship(
        order_by="ExamOption.label", lazy="selectin"
    )


class ExamOption(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "exam_options"

    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exam_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(1), nullable=False)  # A-D as in Excel
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
