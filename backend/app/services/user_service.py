from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.core.security import hash_password
from app.models.enums import EventType, Role
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.services import audit_service


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found.")
    return user


def list_users(
    db: Session,
    *,
    page: int,
    page_size: int,
    q: str | None = None,
    role: Role | None = None,
    active: bool | None = None,
) -> tuple[list[User], int]:
    conditions = []
    if q:
        like = f"%{q.strip().lower()}%"
        conditions.append(or_(func.lower(User.username).like(like), func.lower(User.display_name).like(like)))
    if role:
        conditions.append(User.role == role)
    if active is not None:
        conditions.append(User.is_active == active)
    total = db.scalar(select(func.count(User.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(User).where(*conditions).order_by(User.username).limit(page_size).offset((page - 1) * page_size)
    ).all()
    return list(rows), total


def create_user(db: Session, actor: User, data: UserCreate) -> User:
    user = User(
        username=data.username,
        display_name=data.display_name,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise ConflictError("That username is already taken.", code="username_taken") from None
    audit_service.record(
        db,
        event_type=EventType.USER_CREATED,
        actor_id=actor.id,
        detail=f"Created user '{user.username}' with role {user.role.value}.",
    )
    db.commit()
    return user


def _active_admin_count(db: Session) -> int:
    return db.scalar(select(func.count(User.id)).where(User.role == Role.ADMIN, User.is_active.is_(True))) or 0


def update_user(db: Session, actor: User, user: User, data: UserUpdate) -> User:
    changes: list[str] = []
    if data.display_name is not None and data.display_name != user.display_name:
        changes.append("display name")
        user.display_name = data.display_name
    if data.role is not None and data.role != user.role:
        if user.role == Role.ADMIN and user.is_active and _active_admin_count(db) <= 1:
            raise BusinessRuleError("At least one active administrator must remain.", code="last_admin")
        changes.append(f"role {user.role.value} -> {data.role.value}")
        user.role = data.role
    if data.password is not None:
        user.password_hash = hash_password(data.password)
        changes.append("password reset")
    if changes:
        audit_service.record(
            db,
            event_type=EventType.USER_UPDATED,
            actor_id=actor.id,
            detail=f"Updated user '{user.username}': {', '.join(changes)}.",
        )
    db.commit()
    return user


def set_active(db: Session, actor: User, user: User, active: bool) -> User:
    if user.is_active == active:
        return user
    if not active:
        if user.id == actor.id:
            raise BusinessRuleError("You cannot deactivate your own account.", code="self_deactivate")
        if user.role == Role.ADMIN and _active_admin_count(db) <= 1:
            raise BusinessRuleError("At least one active administrator must remain.", code="last_admin")
    user.is_active = active
    audit_service.record(
        db,
        event_type=EventType.USER_ACTIVATED if active else EventType.USER_DEACTIVATED,
        actor_id=actor.id,
        detail=f"{'Activated' if active else 'Deactivated'} user '{user.username}'.",
    )
    db.commit()
    return user
