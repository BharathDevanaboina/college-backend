"""Feature module definition for the application.

Each folder in ``app/modules`` exposes one ``module`` object.
``app.main`` mounts the routers of every enabled module, so each feature
can run as its own Cloud Run service by setting ``ENABLED_MODULES``
(see ``docs/01-architecture.md``).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from fastapi import APIRouter


@dataclass(frozen=True)
class Module:
    name: str
    description: str
    public_router: APIRouter | None = None  # mounted under /api/v1
    admin_router: APIRouter | None = None  # mounted under /api/v1/admin
    internal_router: APIRouter | None = None  # mounted under /internal (scheduler only)
    depends_on: tuple[str, ...] = field(default_factory=tuple)
