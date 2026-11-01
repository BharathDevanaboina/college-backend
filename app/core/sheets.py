"""Google Sheets writer used to record student submissions.

``GoogleSheetsClient`` calls the Sheets API v4 with the service's own Google identity
(no key files). ``FakeSheetsClient`` keeps rows in memory and in CSV files for local use.
Values are written with ``valueInputOption=RAW`` so nothing typed by a student can
become a spreadsheet formula.
"""

from __future__ import annotations

import csv
import logging
import threading
from pathlib import Path
from typing import Protocol
from urllib.parse import quote

logger = logging.getLogger(__name__)

SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets"
API_BASE = "https://sheets.googleapis.com/v4/spreadsheets"


class SheetsError(Exception):
    pass


class SheetsClient(Protocol):
    def append_row(self, tab: str, headers: list[str], row: list[str]) -> None: ...


def _a1(tab: str, cells: str) -> str:
    return "'" + tab.replace("'", "''") + "'!" + cells


class GoogleSheetsClient:
    def __init__(self, spreadsheet_id: str, timeout_seconds: float = 8.0) -> None:
        import google.auth
        from google.auth.transport.requests import AuthorizedSession

        credentials, _ = google.auth.default(scopes=[SHEETS_SCOPE])
        self._session = AuthorizedSession(credentials)
        self._base = f"{API_BASE}/{spreadsheet_id}"
        self._timeout = timeout_seconds
        self._tabs_with_headers: set[str] = set()
        self._lock = threading.Lock()

    def _request(self, method: str, path: str, **kwargs):
        try:
            response = self._session.request(
                method, self._base + path, timeout=self._timeout, **kwargs
            )
        except Exception as exc:
            raise SheetsError(f"Google Sheets request failed: {exc}") from exc
        if response.status_code >= 400:
            raise SheetsError(
                f"Google Sheets returned {response.status_code}: {response.text[:300]}"
            )
        return response.json() if response.content else {}

    def _ensure_headers(self, tab: str, headers: list[str]) -> None:
        if tab in self._tabs_with_headers:
            return
        with self._lock:
            if tab in self._tabs_with_headers:
                return
            existing = self._request(
                "GET", f"/values/{quote(_a1(tab, '1:1'), safe='')}"
            )
            if not existing.get("values"):
                self._request(
                    "PUT",
                    f"/values/{quote(_a1(tab, 'A1'), safe='')}",
                    params={"valueInputOption": "RAW"},
                    json={"values": [headers]},
                )
            self._tabs_with_headers.add(tab)

    def append_row(self, tab: str, headers: list[str], row: list[str]) -> None:
        self._ensure_headers(tab, headers)
        self._request(
            "POST",
            f"/values/{quote(_a1(tab, 'A1'), safe='')}:append",
            params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
            json={"values": [row]},
        )


class FakeSheetsClient:
    """In-memory sheet for tests; also writes CSV files when ``directory`` is given."""

    def __init__(self, directory: str | None = None) -> None:
        self.rows: dict[str, list[list[str]]] = {}
        self.fail = False
        self._dir = Path(directory) if directory else None

    def append_row(self, tab: str, headers: list[str], row: list[str]) -> None:
        if self.fail:
            raise SheetsError("Simulated Google Sheets outage")
        self.rows.setdefault(tab, []).append(list(row))
        if self._dir:
            self._dir.mkdir(parents=True, exist_ok=True)
            target = self._dir / f"{tab}.csv"
            new_file = not target.exists()
            with target.open("a", newline="", encoding="utf-8") as fh:
                writer = csv.writer(fh)
                if new_file:
                    writer.writerow(headers)
                writer.writerow(row)
