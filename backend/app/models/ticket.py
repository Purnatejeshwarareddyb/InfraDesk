from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UTCDateTime, utcnow
from app.models.asset import Asset
from app.models.enums import Category, Priority, TicketStatus
from app.models.user import User, enum_column


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_status_priority", "status", "priority"),
        Index("ix_tickets_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticket_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[Category] = mapped_column(enum_column(Category), default=Category.OTHER, index=True)
    priority: Mapped[Priority] = mapped_column(enum_column(Priority), default=Priority.MEDIUM)
    status: Mapped[TicketStatus] = mapped_column(enum_column(TicketStatus), default=TicketStatus.OPEN, index=True)

    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), index=True)
    assignee_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=True, index=True)
    related_asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id", ondelete="RESTRICT"), nullable=True)

    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    reporter: Mapped[User] = relationship(foreign_keys=[reporter_id], lazy="joined")
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id], lazy="joined")
    related_asset: Mapped[Asset | None] = relationship(foreign_keys=[related_asset_id], lazy="joined")
