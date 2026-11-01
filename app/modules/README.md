# Feature modules

Each module owns its routes, schemas, business logic, and (when needed) database access.
Keep shared infrastructure in `app/core`, database configuration in `db`, and app-wide
models in `app/models.py`. Add only the files a module actually needs.

- `router.py`: FastAPI endpoints
- `schemas.py`: request/response validation
- `service.py`: business rules and orchestration
- `repository.py`: database queries
- `models.py`: module-specific ORM models, if appropriate
- `dependencies.py`: module-specific dependencies/access checks
- `tests/`: module tests
