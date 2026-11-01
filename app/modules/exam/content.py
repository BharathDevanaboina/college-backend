"""Question and passage text with optional tables.

In Excel, a table is typed inside the cell (Alt+Enter for new lines), one row per line,
cells separated by '|'. The first row is the header. A separator line such as
'|---|---|' is optional.
"""

from __future__ import annotations

import re

SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")


class ContentError(ValueError):
    pass


def _cells(line: str) -> list[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|"):
        inner = inner[:-1]
    return [cell.strip() for cell in inner.split("|")]


def _table(lines: list[str]) -> dict:
    rows = [_cells(line) for line in lines]
    rows = [row for row in rows if not all(SEPARATOR_CELL.match(cell) for cell in row if cell)]
    if len(rows) < 2:
        raise ContentError("a table needs a header row and at least one data row")
    width = len(rows[0])
    if width < 2:
        raise ContentError("a table needs at least two columns")
    for n, row in enumerate(rows[1:], start=2):
        if len(row) != width:
            raise ContentError(f"table row {n} has {len(row)} cells but the header has {width}")
    return {"type": "table", "header": rows[0], "rows": rows[1:]}


def parse_content(text: str) -> list[dict]:
    text = (text or "").replace("\\r\\n", "\\n").replace("\\r", "\\n").strip()
    if not text:
        raise ContentError("text is empty")

    blocks: list[dict] = []
    buffer: list[str] = []
    table_lines: list[str] = []

    def flush_text() -> None:
        if buffer:
            joined = "\\n".join(buffer).strip()
            if joined:
                blocks.append({"type": "text", "text": joined})
            buffer.clear()

    for line in text.split("\\n"):
        if line.strip().startswith("|"):
            flush_text()
            table_lines.append(line)
        else:
            if table_lines:
                blocks.append(_table(table_lines))
                table_lines = []
            buffer.append(line)

    if table_lines:
        blocks.append(_table(table_lines))
    flush_text()
    return blocks
