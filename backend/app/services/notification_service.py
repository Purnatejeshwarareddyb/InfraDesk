from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.enums import NotificationType, Role
from app.models.notification import Notification
from app.models.user import User


def notify(
    db: Session,
    *,
    recipient_ids: set[int],
    ticket_id: int | None,
    type_: NotificationType,
    message: str,
) -> None:
    """Create one in-app notification per recipient. The caller commits."""
    for recipient_id in recipient_ids:
        db.add(Notification(recipient_user_id=recipient_id, ticket_id=ticket_id, type=type_, message=message[:300]))


def active_admin_ids(db: Session) -> set[int]:
    return set(db.scalars(select(User.id).where(User.role == Role.ADMIN, User.is_active.is_(True))).all())


def list_for_user(
    db: Session, user: User, *, page: int, page_size: int, unread_only: bool = False
) -> tuple[list[Notification], int, int]:
    base = [Notification.recipient_user_id == user.id]
    conditions = base + ([Notification.read_at.is_(None)] if unread_only else [])
    total = db.scalar(select(func.count(Notification.id)).where(*conditions)) or 0
    unread = db.scalar(select(func.count(Notification.id)).where(*base, Notification.read_at.is_(None))) or 0
    rows = db.scalars(
        select(Notification)
        .where(*conditions)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()
    return list(rows), total, unread


def mark_read(db: Session, user: User, notification_id: int) -> Notification:
    notification = db.get(Notification, notification_id)
    # A user can only touch their own notifications; others look like "not found".
    if notification is None or notification.recipient_user_id != user.id:
        raise NotFoundError("Notification not found.")
    if notification.read_at is None:
        notification.read_at = datetime.now(UTC)
        db.commit()
    return notification


def mark_all_read(db: Session, user: User) -> int:
    result = db.execute(
        update(Notification)
        .where(Notification.recipient_user_id == user.id, Notification.read_at.is_(None))
        .values(read_at=datetime.now(UTC))
    )
    db.commit()
    return result.rowcount or 0
