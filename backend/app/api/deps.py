"""Shared FastAPI dependencies: database session, current user and role checks."""

from typing import Annotated
from urllib.parse import urlparse

from fastapi import Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User

DbSession = Annotated[Session, Depends(get_db)]

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _origin_allowed(request: Request) -> bool:
    """For requests that change data, a browser-sent Origin must be this site or a configured one.

    Browsers always send an Origin header on cross-site POST/PATCH/DELETE requests, so a
    forged request from another website is rejected. Together with the SameSite=Lax cookie
    this protects against cross-site request forgery. Non-browser clients (curl, tests)
    send no Origin header and are not affected.
    """
    origin = request.headers.get("origin")
    if origin is None:
        return True
    settings = get_settings()
    if origin in settings.cors_origin_list:
        return True
    host = request.headers.get("host", "")
    return urlparse(origin).netloc == host and bool(host)


def get_current_user(request: Request, db: DbSession) -> User:
    token = request.cookies.get(get_settings().cookie_name)
    if not token:
        raise UnauthorizedError("Authentication is required.", code="not_authenticated")

    user_id = decode_access_token(token)
    if user_id is None:
        raise UnauthorizedError("Your session has expired. Please sign in again.", code="session_expired")

    if request.method not in SAFE_METHODS and not _origin_allowed(request):
        raise ForbiddenError("Cross-site request blocked.", code="csrf_check_failed")

    # The user is loaded on every request, so deactivation takes effect immediately.
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Your session has expired. Please sign in again.", code="session_expired")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> User:
    if user.role != Role.ADMIN:
        raise ForbiddenError("Administrator access is required.", code="admin_required")
    return user


AdminUser = Annotated[User, Depends(require_admin)]


class Pagination:
    def __init__(
        self,
        page: Annotated[int, Query(ge=1, le=100000)] = 1,
        page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    ):
        self.page = page
        self.page_size = page_size


PageParams = Annotated[Pagination, Depends()]
