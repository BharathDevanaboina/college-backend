# Gallery module

This package recreates the gallery-module code visible in the supplied screenshots.

## Files
- `__init__.py`: module registration
- `models.py`: SQLAlchemy model
- `router.py`: admin API routes
- `schemas.py`: Pydantic request/response schemas
- `service.py`: database and storage operations

## Integration notes
1. Confirm the names and signatures of project-specific helpers in `app.core.*`.
2. Confirm `TimestampMixin` provides `created_at` and that `UUIDPrimaryKeyMixin` provides `id`.
3. Confirm `store_image()` returns `large_path`, `large_url`, `thumb_path`, `thumb_url`, `width`, and `height`.
4. Confirm `read_upload()` validates image type/content, not only file extension and size.
5. Verify the gallery router is registered by the application's module loader.
6. Run your project's tests and migrations before using this code.

The code is reconstructed from photographs, so a few details may differ from the original source.
