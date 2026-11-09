"""Health endpoints used by Docker, Ansible and Nagios. They never reveal internal details."""

import logging

from fastapi import APIRouter, Response
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import SessionLocal

router = APIRouter(tags=["health"])
logger = logging.getLogger("infradesk")


@router.get("/health", summary="Liveness check")
def health() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "app": settings.app_name, "version": settings.app_version}


@router.get("/ready", summary="Readiness check (database reachable)")
def ready(response: Response) -> dict[str, str]:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - details are logged, never returned
        logger.exception("Readiness check failed")
        response.status_code = 503
        return {"status": "not_ready"}
    return {"status": "ready"}
