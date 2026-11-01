"""Validation and processing of uploaded files (images, PDFs, Excel)."""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass

from fastapi import UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.error import PayloadTooLarge, ValidationFailed

Image.MAX_IMAGE_PIXELS = 40_000_000  # guards against "decompression bomb" images
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


def read_upload(file: UploadFile, *, max_mb: int) -> bytes:
    limit = max_mb * 1024 * 1024
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise PayloadTooLarge(f"File is larger than {max_mb} MB.")
    if not data:
        raise ValidationFailed("The uploaded file is empty.")
    return data


@dataclass(frozen=True)
class ProcessedImage:
    data: bytes
    width: int
    height: int
    content_type: str = "image/webp"


def process_image(data: bytes, sizes: dict[str, int]) -> dict[str, ProcessedImage]:
    """Validate an image, fix its rotation, strip metadata and produce WebP sizes.

    ``sizes`` maps a variant name to its maximum width, e.g. {"large": 1920, "thumb": 600}.
    """
    try:
        with Image.open(io.BytesIO(data)) as probe:
            fmt = probe.format
            probe.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValidationFailed("The file is not a valid image.", code="INVALID_IMAGE") from exc
    if fmt not in ALLOWED_IMAGE_FORMATS:
        raise ValidationFailed("Only JPEG, PNG and WebP images are allowed.", code="INVALID_IMAGE")

    with Image.open(io.BytesIO(data)) as img:
        img = ImageOps.exif_transpose(img)
        has_alpha = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
        img = img.convert("RGBA" if has_alpha else "RGB")
        result: dict[str, ProcessedImage] = {}
        for name, max_width in sizes.items():
            variant = img.copy()
            if variant.width > max_width:
                ratio = max_width / variant.width
                variant = variant.resize(
                    (max_width, max(1, round(variant.height * ratio))),
                    Image.Resampling.LANCZOS,
                )
            out = io.BytesIO()
            variant.save(out, format="WEBP", quality=82, method=4)
            result[name] = ProcessedImage(out.getvalue(), variant.width, variant.height)
        return result


def validate_pdf(data: bytes) -> None:
    if not data.startswith(b"%PDF-"):
        raise ValidationFailed("Only PDF files are allowed.", code="INVALID_PDF")


def validate_xlsx(data: bytes, *, max_uncompressed_mb: int = 60) -> None:
    """Reject non-xlsx files, macro workbooks and zip bombs."""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            names = zf.namelist()
            total = sum(info.file_size for info in zf.infolist())
    except zipfile.BadZipFile as exc:
        raise ValidationFailed("Please upload an Excel .xlsx file.", code="INVALID_EXCEL") from exc
    if "xl/workbook.xml" not in names:
        raise ValidationFailed("Please upload an Excel .xlsx file.", code="INVALID_EXCEL")
    if any(n.lower().endswith("vbaproject.bin") for n in names):
        raise ValidationFailed("Macro-enabled workbooks are not allowed.", code="INVALID_EXCEL")
    if total > max_uncompressed_mb * 1024 * 1024:
        raise ValidationFailed("The Excel file is too large once unpacked.", code="INVALID_EXCEL")
