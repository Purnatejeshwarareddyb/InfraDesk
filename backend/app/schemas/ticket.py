from datetime import datetime

from pydantic import BaseModel

from app.models.enums import Category, EventType, Priority, TicketStatus
from app.schemas.asset import AssetBrief
from app.schemas.common import ORMModel, text
from app.schemas.user import UserBrief


class TicketOut(ORMModel):
    id: int
    ticket_number: str
    title: str
    description: str
    category: Category
    priority: Priority
    status: TicketStatus
    reporter: UserBrief
    assignee: UserBrief | None
    related_asset: AssetBrief | None
    resolution_note: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None
    # Statuses the signed-in user may move this ticket to right now.
    allowed_transitions: list[TicketStatus] = []


class TicketCreate(BaseModel):
    title: text(5, 160)
    description: text(10, 5000)
    category: Category = Category.OTHER
    priority: Priority = Priority.MEDIUM
    related_asset_id: int | None = None


class TicketUpdate(BaseModel):
    """Fields an administrator may edit. Status and assignee have their own endpoints."""

    title: text(5, 160) | None = None
    description: text(10, 5000) | None = None
    category: Category | None = None
    priority: Priority | None = None
    related_asset_id: int | None = None
    clear_related_asset: bool = False


class AssignRequest(BaseModel):
    assignee_id: int
    note: text(0, 1000) | None = None


class TransitionRequest(BaseModel):
    status: TicketStatus
    resolution_note: text(0, 5000) | None = None


class CommentCreate(BaseModel):
    body: text(1, 5000)


class CommentOut(ORMModel):
    id: int
    ticket_id: int
    author: UserBrief
    body: str
    created_at: datetime


class EventOut(ORMModel):
    id: int
    ticket_id: int | None
    actor: UserBrief | None
    event_type: EventType
    old_value: str | None
    new_value: str | None
    detail: str
    created_at: datetime


class TicketDetail(BaseModel):
    ticket: TicketOut
    comments: list[CommentOut]
    history: list[EventOut]
