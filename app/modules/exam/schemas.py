from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class IssueOut(BaseModel):
    sheet: str
    row: int | None
    message: str


class ValidationReport(BaseModel):
    ok: bool
    question_count: int
    section_counts: dict[str, int]
    subsection_counts: dict[str, dict[str, int]]
    passage_count: int
    errors: list[IssueOut]
    warnings: list[IssueOut]


class ExamSetOut(BaseModel):
    id: uuid.UUID
    slot: int
    name: str
    source_filename: str
    question_count: int
    uploaded_by: str
    created_at: datetime


class SlotOut(BaseModel):
    slot: int
    exam_set: ExamSetOut | None


class UploadResult(BaseModel):
    exam_set: ExamSetOut
    warnings: list[IssueOut]


# ---- student side ----

class OptionPublic(BaseModel):
    id: uuid.UUID
    content: str


class QuestionPublic(BaseModel):
    id: uuid.UUID
    number: int
    subsection: str
    content: list[dict[str, Any]]
    options: list[OptionPublic]


class PassagePublic(BaseModel):
    id: uuid.UUID
    content: list[dict[str, Any]]


class PaperItem(BaseModel):
    type: Literal["question", "passage"]
    question: QuestionPublic | None = None
    passage: PassagePublic | None = None
    questions: list[QuestionPublic] | None = None


class PaperSection(BaseModel):
    code: str
    title: str
    question_count: int
    items: list[PaperItem]


class ExamStartResponse(BaseModel):
    attempt_token: str = Field(
        description="Send this back with the answers. Keep it with the saved progress."
    )
    set_name: str
    duration_seconds: int
    started_at: datetime
    ends_at: datetime
    total_questions: int
    sections: list[PaperSection]


class Answer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: uuid.UUID
    option_id: uuid.UUID | None = None


class ExamSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    attempt_token: str = Field(min_length=20)
    answers: list[Answer] = Field(max_length=400)


class SectionScore(BaseModel):
    code: str
    title: str
    score: int
    max_score: int
    correct: int
    incorrect: int
    unanswered: int


class ReviewItem(BaseModel):
    question_id: uuid.UUID
    section: str
    selected_option_id: uuid.UUID | None
    correct_option_id: uuid.UUID
    status: Literal["correct", "incorrect", "unanswered"]
    is_correct: bool


class ExamResult(BaseModel):
    set_name: str
    total_score: int
    max_score: int
    correct: int
    incorrect: int
    unanswered: int
    submitted_after_time_limit: bool
    sections: list[SectionScore]
    review: list[ReviewItem]


class ExamInfo(BaseModel):
    available: bool
    duration_minutes: int
    total_questions: int
    sections: dict[str, int]
