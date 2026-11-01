from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings
from app.core.database import check_database
from app.core.error import ServiceUnavailable

router = APIRouter(tags=["Health"])


@router.get("/healthz", summary="Liveness: the process is running")
def healthz() -> dict:
    return {"status": "ok", "version": __version__}


@router.get("/readyz", summary="Readiness: the database is reachable")
def readyz() -> dict:
    try:
        check_database()
    except Exception as exc:
        raise ServiceUnavailable(
            "Database is not reachable.",
            code="DB_UNAVAILABLE",
        ) from exc

    return {
        "status": "ready",
        "environment": get_settings().app_env,
        "version": __version__,
    }
