"""Saving processed images to storage."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from app.core.storage import FileStorage
from app.core.uploads import process_image

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StoredImage:
    large_path: str
    large_url: str
    thumb_path: str
    thumb_url: str
    width: int
    height: int


def store_image(
    storage: FileStorage,
    folder: str,
    data: bytes,
    *,
    large: int = 1920,
    thumb: int = 600,
) -> StoredImage:
    variants = process_image(data, {"large": large, "thumb": thumb})
    stem = uuid.uuid4().hex
    large_path = f"public/{folder}/{stem}-large.webp"
    thumb_path = f"public/{folder}/{stem}-thumb.webp"
    large_url = storage.save_public(large_path, variants["large"].data, "image/webp")
    thumb_url = storage.save_public(thumb_path, variants["thumb"].data, "image/webp")
    return StoredImage(
        large_path,
        large_url,
        thumb_path,
        thumb_url,
        variants["large"].width,
        variants["large"].height,
    )


def delete_files(storage: FileStorage, *paths: str | None) -> None:
    """Best-effort clean-up of files that are no longer referenced."""
    for path in paths:
        if not path:
            continue
        try:
            storage.delete(path)
        except Exception:
            logger.warning(
                "Could not delete stored file",
                extra={"path": path},
                exc_info=True,
            )
