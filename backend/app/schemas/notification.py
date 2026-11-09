from datetime import datetime

from app.models.enums import NotificationType
from app.schemas.common import ORMModel


class NotificationOut(ORMModel):
    id: int
    ticket_id: int | None
    type: NotificationType
    message: str
    read_at: datetime | None
    created_at: datetime


class NotificationList(ORMModel):
    items: list[NotificationOut]
    total: int
    page: int
    page_size: int
    pages: int
    unread_count: int
