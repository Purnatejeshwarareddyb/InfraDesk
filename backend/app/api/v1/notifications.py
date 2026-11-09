from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, PageParams
from app.schemas.common import Message
from app.schemas.notification import NotificationList, NotificationOut
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationList, summary="My notifications")
def list_notifications(
    user: CurrentUser, db: DbSession, paging: PageParams, unread_only: bool = False
) -> NotificationList:
    rows, total, unread = notification_service.list_for_user(
        db, user, page=paging.page, page_size=paging.page_size, unread_only=unread_only
    )
    return NotificationList(
        items=[NotificationOut.model_validate(n) for n in rows],
        total=total,
        page=paging.page,
        page_size=paging.page_size,
        pages=max(1, -(-total // paging.page_size)),
        unread_count=unread,
    )


@router.post("/read-all", response_model=Message, summary="Mark all my notifications as read")
def read_all(user: CurrentUser, db: DbSession) -> Message:
    count = notification_service.mark_all_read(db, user)
    return Message(message=f"{count} notification(s) marked as read.")


@router.post("/{notification_id}/read", response_model=NotificationOut, summary="Mark one notification as read")
def read_one(notification_id: int, user: CurrentUser, db: DbSession) -> NotificationOut:
    return NotificationOut.model_validate(notification_service.mark_read(db, user, notification_id))
