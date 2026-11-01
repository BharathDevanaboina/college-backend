from __future__ import annotations

import logging
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.sheets import SheetsClient
from app.core.timeutil import utc_now
from app.modules.lead_sync.models import PendingSheetRow
from app.modules.lead_sync.schemas import FlushResult, SyncStatus

logger = logging.getLogger(__name__)
MAX_BACKOFF_SECONDS = 3600


def deliver(db: Session, sheets: SheetsClient, tab: str, headers: list[str], row: list[str]) -> str:
    """Write a row to Google Sheets now; if it fails keep it in the retry queue. Never raises."""
    try:
        sheets.append_row(tab, headers, row)
        return "delivered"
    except Exception as exc:
        logger.warning(
            "Google Sheets write failed; queued for retry",
            extra={"tab": tab, "error": str(exc)[:300]},
        )
        db.add(
            PendingSheetRow(
                tab=tab,
                headers=headers,
                row=row,
                attempts=1,
                last_error=str(exc)[:1000],
                next_attempt_at=utc_now() + timedelta(seconds=60),
            )
        )
        db.commit()
        return "queued"


def flush(db: Session, sheets: SheetsClient, *, limit: int = 200) -> FlushResult:
    """Retry queued rows (called every few minutes by Cloud Scheduler)."""
    stmt = (
        select(PendingSheetRow)
        .where(PendingSheetRow.next_attempt_at <= utc_now())
        .order_by(PendingSheetRow.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    delivered = failed = 0
    for item in db.scalars(stmt).all():
        try:
            sheets.append_row(item.tab, item.headers, item.row)
            db.delete(item)
            delivered += 1
        except Exception as exc:
            item.attempts += 1
            item.last_error = str(exc)[:1000]
            item.next_attempt_at = utc_now() + timedelta(
                seconds=min(MAX_BACKOFF_SECONDS, 60 * 2**item.attempts)
            )
            failed += 1
            if item.attempts >= 10:
                logger.error(
                    "Google Sheets row still failing",
                    extra={"tab": item.tab, "attempts": item.attempts},
                )
    db.commit()
    remaining = db.scalar(select(func.count()).select_from(PendingSheetRow)) or 0
    if delivered or failed:
        logger.info(
            "Lead sync flush",
            extra={"delivered": delivered, "failed": failed, "remaining": remaining},
        )
    return FlushResult(delivered=delivered, failed=failed, still_pending=remaining)


def status(db: Session) -> SyncStatus:
    count, oldest, max_attempts = db.execute(
        select(
            func.count(),
            func.min(PendingSheetRow.created_at),
            func.max(PendingSheetRow.attempts),
        )
    ).one()
    return SyncStatus(
        pending_rows=count or 0,
        oldest_pending_since=oldest,
        max_attempts_so_far=max_attempts or 0,
    )
