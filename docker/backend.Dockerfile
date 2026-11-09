# syntax=docker/dockerfile:1
# InfraDesk backend image (FastAPI + SQLite). Build context: the repository root.
#   docker build -f docker/backend.Dockerfile -t infradesk-backend:latest .
FROM python:3.13-slim

# No .pyc files, unbuffered logs (so `docker compose logs` is live).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Non-root user with a fixed uid, so volume ownership is predictable.
RUN groupadd --system --gid 10001 infradesk \
 && useradd  --system --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin infradesk \
 && mkdir -p /app /data \
 && chown infradesk:infradesk /data

WORKDIR /app

# Dependencies first: this layer is cached until requirements.txt changes.
# The cache mount keeps downloaded wheels between builds (needs BuildKit, default in Docker 23+).
COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Application code, Alembic migrations and the admin scripts (backup, restore, seed...).
COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY backend/scripts ./scripts

RUN find /app -type d -exec chmod 0755 {} \; \
 && find /app -type f -exec chmod 0644 {} \;
# The database lives on a named volume mounted at /data (first mount inherits this ownership).
ENV DATABASE_URL=sqlite:////data/infradesk.db
VOLUME ["/data"]

USER 10001:10001
EXPOSE 8000

# Liveness only; docker-compose.yml overrides this with a /ready check.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"]

# Migrate, then serve. `exec` makes uvicorn PID 1 so it receives SIGTERM on `docker stop`.
# One worker keeps memory low (an 8 GB laptop is shared with the browser and IDE).
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
