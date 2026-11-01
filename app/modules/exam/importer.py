"""Reads and validates an uploaded question-set Excel file. Format: docs/10-exam-question-format.md."""

from __future__ import annotations

import io
from collections import Counter
from dataclasses import dataclass, field

from openpyxl import load_workbook

from app.core.uploads import validate_xlsx
from app.modules.exam.constants import (
    EXPECTED_SUBSECTION_COUNTS,
    MAX_OPTION_LENGTH,
    MAX_ROWS,
    MAX_TEXT_LENGTH,
    OPTION_LABELS,
    REQUIRED_SECTION_COUNTS,
    SECTION_TITLES,
    TOTAL_QUESTIONS,
)
from app.modules.exam.content import ContentError, parse_content


QUESTION_COLUMNS = [
    "section",
    "subsection",
    "question",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct",
]
PASSAGE_COLUMNS = ["passage_id", "passage_text"]
MAX_ISSUES = 300


@dataclass
class Issue:
    sheet: str
    row: int | None
    message: str


@dataclass
class ParsedPassage:
    key: str
    content: list[dict]
    section: str | None = None


@dataclass
class ParsedQuestion:
    row: int
    section: str
    subsection: str
    passage_key: str | None
    content: list[dict]
    options: list[tuple[str, str]]  # (label, text)
    correct: str


@dataclass
class ImportReport:
    questions: list[ParsedQuestion] = field(default_factory=list)
    passages: dict[str, ParsedPassage] = field(default_factory=dict)
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    section_counts: dict[str, int] = field(default_factory=dict)
    subsection_counts: dict[str, dict[str, int]] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, sheet: str, row: int | None, message: str) -> None:
        if len(self.errors) < MAX_ISSUES:
            self.errors.append(Issue(sheet, row, message))

    def warn(self, sheet: str, row: int | None, message: str) -> None:
        if len(self.warnings) < MAX_ISSUES:
            self.warnings.append(Issue(sheet, row, message))


def _text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _rows(ws) -> tuple[list[str], list[tuple[int, dict[str, str]]]]:
    iterator = ws.iter_rows(values_only=True)
    try:
        header = [
            _text(c).lower().replace(" ", "_")
            for c in next(iterator)
        ]
    except StopIteration:
        return [], []

    rows = []
    for index, values in enumerate(iterator, start=2):
        record = {
            header[i]: _text(value)
            for i, value in enumerate(values)
            if i < len(header) and header[i]
        }
        if any(record.values()):
            rows.append((index, record))
    return header, rows


def _section(raw: str) -> str | None:
    value = raw.strip().upper().removeprefix("SECTION").strip(" :-")
    return value if value in SECTION_TITLES else None


def _correct(raw: str) -> str | None:
    value = raw.strip().upper().removeprefix("OPTION").strip(" :-")
    return value[:1] if value[:1] in OPTION_LABELS and len(value) <= 1 else None


def parse_workbook(data: bytes) -> ImportReport:
    validate_xlsx(data)
    report = ImportReport()
    workbook = load_workbook(
        io.BytesIO(data),
        read_only=True,
        data_only=True,
    )
    sheets = {ws.title.strip().lower(): ws for ws in workbook.worksheets}

    # Passages (optional sheet)
    if "passages" in sheets:
        header, rows = _rows(sheets["passages"])
        missing = [column for column in PASSAGE_COLUMNS if column not in header]
        if missing:
            report.error(
                "passages",
                1,
                f"Missing column(s): {', '.join(missing)}",
            )
        else:
            for row, rec in rows:
                key = rec.get("passage_id", "")
                if not key:
                    report.error("passages", row, "passage_id is empty")
                    continue
                if key in report.passages:
                    report.error(
                        "passages",
                        row,
                        f"passage_id '{key}' is used twice",
                    )
                    continue
                passage_text = rec.get("passage_text", "")
                try:
                    if len(passage_text) > MAX_TEXT_LENGTH:
                        raise ContentError(
                            f"text is longer than {MAX_TEXT_LENGTH} characters"
                        )
                    report.passages[key] = ParsedPassage(
                        key,
                        parse_content(passage_text),
                    )
                except ContentError as exc:
                    report.error("passages", row, f"passage_text: {exc}")

    # Questions
    if "questions" not in sheets:
        report.error(
            "questions",
            None,
            "The workbook must have a sheet named 'questions'.",
        )
        return report

    header, rows = _rows(sheets["questions"])
    missing = [column for column in QUESTION_COLUMNS if column not in header]
    if missing:
        report.error(
            "questions",
            1,
            f"Missing column(s): {', '.join(missing)}",
        )
        return report

    if len(rows) > MAX_ROWS:
        report.error(
            "questions",
            None,
            f"Too many rows ({len(rows)}). A set has {TOTAL_QUESTIONS} questions.",
        )
        return report

    used_passages: set[str] = set()
    for row, rec in rows:
        problems: list[str] = []

        section = _section(rec.get("section", ""))
        if section is None:
            problems.append("section must be A, B or C")

        subsection = rec.get("subsection", "").strip()
        if not subsection:
            problems.append("subsection is empty")
        elif len(subsection) > 100:
            problems.append("subsection is longer than 100 characters")

        content: list[dict] = []
        question_text = rec.get("question", "")
        try:
            if len(question_text) > MAX_TEXT_LENGTH:
                raise ContentError(
                    f"text is longer than {MAX_TEXT_LENGTH} characters"
                )
            content = parse_content(question_text)
        except ContentError as exc:
            problems.append(f"question: {exc}")

        options: list[tuple[str, str]] = []
        for label in OPTION_LABELS:
            text = rec.get(f"option_{label.lower()}", "")
            if not text:
                problems.append(f"option_{label.lower()} is empty")
            elif len(text) > MAX_OPTION_LENGTH:
                problems.append(
                    f"option_{label.lower()} is longer than "
                    f"{MAX_OPTION_LENGTH} characters"
                )
            options.append((label, text))

        texts = [text.lower() for _, text in options if text]
        if len(texts) != len(set(texts)):
            problems.append("two or more options have the same text")

        correct = _correct(rec.get("correct", ""))
        if correct is None:
            problems.append("correct must be A, B, C or D")

        passage_key = rec.get("passage_id", "").strip() or None
        if passage_key:
            passage = report.passages.get(passage_key)
            if passage is None:
                problems.append(
                    f"passage_id '{passage_key}' is not in the 'passages' sheet"
                )
            elif section:
                if passage.section and passage.section != section:
                    problems.append(
                        f"passage '{passage_key}' is used in more than one section"
                    )
                passage.section = passage.section or section
                used_passages.add(passage_key)

        if problems:
            report.error("questions", row, "; ".join(problems))
            continue

        report.questions.append(
            ParsedQuestion(
                row,
                section,
                subsection,
                passage_key,
                content,
                options,
                correct,
            )
        )

    # Pattern checks
    section_counts = Counter(question.section for question in report.questions)
    report.section_counts = {
        section: section_counts.get(section, 0)
        for section in SECTION_TITLES
    }

    for section, titles in EXPECTED_SUBSECTION_COUNTS.items():
        found = Counter(
            question.subsection
            for question in report.questions
            if question.section == section
        )
        report.subsection_counts[section] = dict(found)
        known = {name.lower(): name for name in titles}

        for name, count in found.items():
            if name.lower() not in known:
                report.warn(
                    "questions",
                    None,
                    f"Section {section}: unexpected subsection '{name}' "
                    f"({count} questions)",
                )

        for name, expected in titles.items():
            actual = sum(
                count
                for found_name, count in found.items()
                if found_name.lower() == name.lower()
            )
            if actual != expected:
                report.warn(
                    "questions",
                    None,
                    f"Section {section} '{name}': expected {expected}, "
                    f"found {actual}",
                )

    if not report.errors:
        total = len(report.questions)
        if total != TOTAL_QUESTIONS:
            report.error(
                "questions",
                None,
                f"A set must have exactly {TOTAL_QUESTIONS} questions; "
                f"found {total}.",
            )

        for section, required in REQUIRED_SECTION_COUNTS.items():
            if report.section_counts.get(section, 0) != required:
                report.error(
                    "questions",
                    None,
                    f"Section {section} ({SECTION_TITLES[section]}) must have "
                    f"exactly {required} questions; "
                    f"found {report.section_counts.get(section, 0)}.",
                )

    for key in report.passages:
        if key not in used_passages:
            report.warn(
                "passages",
                None,
                f"passage '{key}' is not used by any question",
            )

    return report
