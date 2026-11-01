"""Builds the downloadable Excel template for question sets."""

from __future__ import annotations

import io

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from app.modules.exam.constants import EXPECTED_SUBSECTION_COUNTS, REQUIRED_SECTION_COUNTS, SECTION_TITLES
from app.modules.exam.importer import PASSAGE_COLUMNS, QUESTION_COLUMNS

QUESTION_HEADER = QUESTION_COLUMNS[:2] + ["passage_id"] + QUESTION_COLUMNS[2:]

SAMPLE_QUESTIONS = [
    [
        "A",
        "Problem Solving",
        "",
        "Find the missing number in the sequence: 4, 9, 19, 39, 79, ?",
        "119",
        "139",
        "159",
        "169",
        "C",
    ],
    [
        "B",
        "Arithmetical Ability",
        "",
        "A sum of money doubles itself in 5 years at a certain rate of simple interest. "
        "In how many years will it become 4 times itself at the same rate?",
        "10 years",
        "12 years",
        "15 years",
        "20 years",
        "C",
    ],
    [
        "B",
        "Statistical Ability",
        "",
        "The table shows the sales of a shop (in lakhs):\\n| Year | Sales |\\n| 2023 | 450 |\\n| 2024 | 540 |\\n"
        "What is the percentage increase in sales?",
        "10%",
        "15%",
        "20%",
        "25%",
        "C",
    ],
    [
        "C",
        "Business and Computer Terminology",
        "",
        'What does the term "Bulls" signify in the stock market?',
        "Investors who expect stock prices to fall",
        "Investors who expect stock prices to rise",
        "Government regulatory authorities",
        "Short-term borrowers",
        "B",
    ],
    [
        "C",
        "Reading Comprehension",
        "P1",
        "According to the passage, what is the main benefit of saving early?",
        "Higher taxes",
        "Compound growth",
        "Lower income",
        "Fewer expenses",
        "B",
    ],
    [
        "C",
        "Reading Comprehension",
        "P1",
        "Which word in the passage means 'steady'?",
        "Consistent",
        "Rapid",
        "Rare",
        "Uncertain",
        "A",
    ],
]

SAMPLE_PASSAGES = [
    [
        "P1",
        "Saving a small amount consistently from an early age allows money to grow through compounding. "
        "Over many years, the interest earned also starts earning interest, which can multiply savings "
        "far beyond the amount originally invested.",
    ],
]


def build_template() -> bytes:
    wb = Workbook()
    bold = Font(bold=True, color="FFFFFF")
    fill = PatternFill("solid", fgColor="1F4E78")
    wrap = Alignment(wrap_text=True, vertical="top")

    ws = wb.active
    ws.title = "questions"
    ws.append(QUESTION_HEADER)
    for row in SAMPLE_QUESTIONS:
        ws.append(row)

    widths = {"A": 9, "B": 34, "C": 12, "D": 70, "E": 24, "F": 24, "G": 24, "H": 24, "I": 9}
    for col, width in widths.items():
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"

    ps = wb.create_sheet("passages")
    ps.append(PASSAGE_COLUMNS)
    for row in SAMPLE_PASSAGES:
        ps.append(row)
    ps.column_dimensions["A"].width = 12
    ps.column_dimensions["B"].width = 120

    for sheet in (ws, ps):
        for cell in sheet[1]:
            cell.font, cell.fill = bold, fill
        for row in sheet.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = wrap

    guide = wb.create_sheet("instructions")
    lines = [
        "HOW TO FILL THIS TEMPLATE",
        "",
        "1. Delete the sample rows in 'questions' and 'passages' and add your own.",
        f"2. A set must have exactly {sum(REQUIRED_SECTION_COUNTS.values())} questions:",
    ]
    lines += [
        f"   Section {s} - {SECTION_TITLES[s]}: {n} questions"
        for s, n in REQUIRED_SECTION_COUNTS.items()
    ]
    lines += [
        "3. Section: A, B or C. Correct: A, B, C or D (the right option).",
        "4. Subsection: use these names (counts are recommended, not enforced):",
    ]
    for s, subs in EXPECTED_SUBSECTION_COUNTS.items():
        lines += [f"   {s}: {name} ({n})" for name, n in subs.items()]
    lines += [
        "5. Reading Comprehension: put the passage in the 'passages' sheet with an id (P1, P2, ...),",
        "   and write that id in the passage_id column of each question about it. Leave passage_id",
        "   empty for normal questions.",
        "6. Tables inside a question: press Alt+Enter for a new line and type one table row per line,",
        "   with cells separated by | (the first row is the header). Example:",
        "   | Year | Sales |",
        "   | 2023 | 450 |",
        "7. Every option must have different text. No images are supported.",
        "8. Upload in the admin portal: Exam sets -> choose an empty slot -> upload.",
        "   Use 'Validate' first to check the file without saving it.",
    ]
    for line in lines:
        guide.append([line])
    guide.column_dimensions["A"].width = 110
    guide["A1"].font = Font(bold=True, size=13)
    for row in guide.iter_rows():
        for cell in row:
            cell.alignment = wrap
    wb.move_sheet("instructions", offset=-2)

    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()
