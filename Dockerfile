# Production image for the college backend (FastAPI). Used for Cloud Run and Docker Compose.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8080

WORKDIR /app

# Install dependencies first so they are cached between code changes.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Application code, migrations and the Excel template.
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .
COPY templates ./templates

# Run as a non-root user.
RUN useradd --uid 10001 --create-home appuser && mkdir -p /app/var && chown -R appuser /app/var
USER appuser

EXPOSE 8080
# Cloud Run sets $PORT. One worker per container; Cloud Run adds containers when busy.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
