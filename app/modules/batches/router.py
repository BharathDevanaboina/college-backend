from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.admin_auth.dependencies import require_admin
from app.modules.batches import service
from app.modules.batches.schemas import BatchCreate, BatchOut, BatchUpdate

admin_router = APIRouter(
    prefix="/batches",
    tags=["Admin: batches"],
    dependencies=[Depends(require_admin)],
)


@admin_router.get(
    "",
    response_model=list[BatchOut],
    summary="List batches (optionally for one course)",
)
def list_batches(
    course: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[BatchOut]:
    return [service.to_out(batch) for batch in service.list_batches(db, course)]


@admin_router.post(
    "",
    response_model=BatchOut,
    status_code=201,
    summary="Add a batch",
)
def create_batch(
    body: BatchCreate,
    db: Session = Depends(get_db),
) -> BatchOut:
    return service.create_batch(db, body)


@admin_router.patch(
    "/{batch_id}",
    response_model=BatchOut,
    summary="Update a batch",
)
def update_batch(
    batch_id: uuid.UUID,
    body: BatchUpdate,
    db: Session = Depends(get_db),
) -> BatchOut:
    return service.update_batch(db, batch_id, body)


@admin_router.delete(
    "/{batch_id}",
    status_code=204,
    summary="Delete a batch",
)
def delete_batch(
    batch_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Response:
    service.delete_batch(db, batch_id)
    return Response(status_code=204)
