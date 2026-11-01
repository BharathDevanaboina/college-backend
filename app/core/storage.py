"""File storage for images and brochures.

* ``FirebaseStorage`` - Cloud Storage for Firebase (staging/production). Public images get a
  Firebase download-token URL; private files (brochures, uploads) are only read by the API.
* ``LocalStorage`` - a folder on disk for local development; public files are served
  by the API at ``/media``.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Protocol
from urllib.parse import quote

logger = logging.getLogger(__name__)


class FileStorage(Protocol):
    def save_public(self, path: str, data: bytes, content_type: str) -> str:
        """Store a public file and return its URL."""

    def save_private(self, path: str, data: bytes, content_type: str) -> None: ...

    def read(self, path: str) -> bytes: ...

    def delete(self, path: str) -> None: ...


def _check_path(path: str) -> str:
    if path.startswith("/") or ".." in path.split("/"):
        raise ValueError(f"Unsafe storage path: {path}")
    return path


class FirebaseStorage:
    def __init__(self, bucket_name: str, project_id: str | None = None) -> None:
        from google.cloud import storage

        self._bucket_name = bucket_name
        self._bucket = storage.Client(project=project_id).bucket(bucket_name)

    def save_public(self, path: str, data: bytes, content_type: str) -> str:
        blob = self._bucket.blob(_check_path(path))
        download_token = str(uuid.uuid4())
        blob.metadata = {"firebaseStorageDownloadTokens": download_token}
        blob.cache_control = "public, max-age=31536000, immutable"
        blob.upload_from_string(data, content_type=content_type)
        return (
            f"https://firebasestorage.googleapis.com/v0/b/{self._bucket_name}/o/"
            f"{quote(path, safe='')}?alt=media&token={download_token}"
        )

    def save_private(self, path: str, data: bytes, content_type: str) -> None:
        blob = self._bucket.blob(_check_path(path))
        blob.cache_control = "private, no-store"
        blob.upload_from_string(data, content_type=content_type)

    def read(self, path: str) -> bytes:
        return self._bucket.blob(_check_path(path)).download_as_bytes()

    def delete(self, path: str) -> None:
        from google.api_core.exceptions import NotFound

        try:
            self._bucket.blob(_check_path(path)).delete()
        except NotFound:
            logger.info("File already deleted", extra={"path": path})


class LocalStorage:
    def __init__(self, base_dir: str, public_base_url: str) -> None:
        self.base = Path(base_dir).resolve()
        self.base.mkdir(parents=True, exist_ok=True)
        self.public_base_url = public_base_url.rstrip("/")

    @property
    def public_dir(self) -> Path:
        path = self.base / "public"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _file(self, path: str) -> Path:
        return self.base / _check_path(path)

    def save_public(self, path: str, data: bytes, content_type: str) -> str:
        if not path.startswith("public/"):
            raise ValueError("Public files must live under public/")
        target = self._file(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return f"{self.public_base_url}/media/{path.removeprefix('public/')}"

    def save_private(self, path: str, data: bytes, content_type: str) -> None:
        target = self._file(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def read(self, path: str) -> bytes:
        return self._file(path).read_bytes()

    def delete(self, path: str) -> None:
        self._file(path).unlink(missing_ok=True)
