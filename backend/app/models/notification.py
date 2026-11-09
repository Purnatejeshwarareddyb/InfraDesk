from datetime import datetime

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UTCDateTime, utcnow
from app.models.enums import NotificationType
from app.models.user import enum_column


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_recipient_read", "recipient_user_id", "read_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    recipient_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    ticket_id: Mapped[int | None] = mapped_column(ForeignKey("tickets.id", ondelete="RESTRICT"), nullable=True)
    type: Mapped[NotificationType] = mapped_column(enum_column(NotificationType))
    message: Mapped[str] = mapped_column(String(300))
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
