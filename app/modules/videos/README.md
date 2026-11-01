# College Backend — Videos Module

This folder reconstructs the video-links module visible in the supplied screenshots.

## Files
- `__init__.py` — module registration
- `links.py` — validates and normalizes YouTube, YouTube Shorts, and Instagram Reel links
- `router.py` — admin API endpoints
- `schemas.py` — request and response models
- `service.py` — database operations and link parsing integration
- `models.py` — SQLAlchemy model

## API routes
All routes use the `/videos` prefix and require `require_admin`:
- `GET /videos` — list video links
- `POST /videos` — create a video link
- `PUT /videos/{video_id}` — replace/update a video link
- `DELETE /videos/{video_id}` — delete a video link

## Integration notes
These files rely on existing project modules such as `app.core.database`, `app.core.errors`,
`app.core.models`, `app.core.validation`, and `app.modules.admin_auth.dependencies`.
They are a reconstruction from screenshots, so compare with the original source and run tests
before using them in a project.
