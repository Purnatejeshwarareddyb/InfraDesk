from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, DbSession, PageParams
from app.models.enums import Role
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Page[UserOut], summary="List users (admin)")
def list_users(
    admin: AdminUser,
    db: DbSession,
    paging: PageParams,
    q: Annotated[str | None, Query(max_length=80)] = None,
    role: Role | None = None,
    active: bool | None = None,
) -> Page[UserOut]:
    rows, total = user_service.list_users(db, page=paging.page, page_size=paging.page_size, q=q, role=role, active=active)
    return Page.build([UserOut.model_validate(u) for u in rows], total, paging.page, paging.page_size)


@router.post("", response_model=UserOut, status_code=201, summary="Create a user (admin)")
def create_user(data: UserCreate, admin: AdminUser, db: DbSession) -> UserOut:
    return UserOut.model_validate(user_service.create_user(db, admin, data))


@router.get("/{user_id}", response_model=UserOut, summary="Get a user (admin)")
def get_user(user_id: int, admin: AdminUser, db: DbSession) -> UserOut:
    return UserOut.model_validate(user_service.get_user(db, user_id))


@router.patch("/{user_id}", response_model=UserOut, summary="Update a user (admin)")
def update_user(user_id: int, data: UserUpdate, admin: AdminUser, db: DbSession) -> UserOut:
    user = user_service.get_user(db, user_id)
    return UserOut.model_validate(user_service.update_user(db, admin, user, data))


@router.post("/{user_id}/deactivate", response_model=UserOut, summary="Deactivate a user (admin)")
def deactivate_user(user_id: int, admin: AdminUser, db: DbSession) -> UserOut:
    user = user_service.get_user(db, user_id)
    return UserOut.model_validate(user_service.set_active(db, admin, user, False))


@router.post("/{user_id}/activate", response_model=UserOut, summary="Activate a user (admin)")
def activate_user(user_id: int, admin: AdminUser, db: DbSession) -> UserOut:
    user = user_service.get_user(db, user_id)
    return UserOut.model_validate(user_service.set_active(db, admin, user, True))
