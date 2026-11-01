"""Application entry point: ``uvicorn app.main:app``."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import app.models  # noqa: F401 (registers every table)
from app import __version__
from app.core import health
from app.core.config import Settings, get_settings
from app.core.error import register_error_handlers
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.modules import select_modules

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    settings.validate_for_environment()
    modules = select_modules(settings.enabled_modules)

    show_docs = settings.app_env != "production"
    application = FastAPI(
        title="College Website API",
        version=__version__,
        description="Backend for the college website. See README.md and docs/09-api-reference.md.",
        docs_url="/docs" if show_docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if show_docs else None,
    )
    register_error_handlers(application)
    register_middleware(application)

    if settings.cors_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=[
                "Authorization",
                "Content-Type",
                "X-Firebase-AppCheck",
                "X-Request-ID",
            ],
            max_age=3600,
        )

    application.include_router(health.router, prefix="/api/v1")
    for module in modules:
        if module.public_router:
            application.include_router(module.public_router, prefix="/api/v1")
        if module.admin_router:
            application.include_router(module.admin_router, prefix="/api/v1/admin")
        if module.internal_router:
            application.include_router(module.internal_router, prefix="/internal")

    if settings.storage_backend == "local":
        from app.core.dependencies import get_storage

        application.mount(
            "/media",
            StaticFiles(directory=get_storage().public_dir),
            name="media",
        )

    logger.info(
        "Application started",
        extra={
            "environment": settings.app_env,
            "modules": [m.name for m in modules],
            "version": __version__,
        },
    )
    return application


app = create_app()
