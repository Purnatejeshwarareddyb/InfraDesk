from pydantic import BaseModel

from app.schemas.ticket import EventOut


class CountItem(BaseModel):
    key: str
    label: str
    count: int


class Summary(BaseModel):
    scope: str  # "all" for administrators, "mine" for workers
    total: int
    open: int  # statuses OPEN and ASSIGNED
    in_progress: int  # IN_PROGRESS and WAITING
    resolved: int  # RESOLVED and CLOSED
    high_priority_active: int  # HIGH or URGENT, not yet resolved/closed/cancelled
    by_status: list[CountItem]
    by_priority: list[CountItem]
    recent_activity: list[EventOut]


class TicketReport(BaseModel):
    date_from: str | None
    date_to: str | None
    total: int
    by_status: list[CountItem]
    by_category: list[CountItem]
    by_priority: list[CountItem]
    by_assignee: list[CountItem]
