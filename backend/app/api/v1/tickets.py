import csv
import io
from datetime import UTC, date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from app.api.deps import AdminUser, CurrentUser, DbSession, PageParams
from app.models.enums import Category, Priority, TicketStatus
from app.schemas.common import Page
from app.schemas.ticket import (
    AssignRequest,
    CommentCreate,
    CommentOut,
    EventOut,
    TicketCreate,
    TicketDetail,
    TicketOut,
    TicketUpdate,
    TransitionRequest,
)
from app.services import ticket_service
from app.services.ticket_service import TicketFilters

router = APIRouter(prefix="/tickets", tags=["tickets"])


def ticket_filters(
    q: Annotated[str | None, Query(max_length=80, description="Search ticket number, title, reporter, assignee")] = None,
    status: TicketStatus | None = None,
    priority: Priority | None = None,
    category: Category | None = None,
    assignee_id: int | None = None,
    reporter_id: int | None = None,
    mine: bool = False,
    created_from: date | None = None,
    created_to: date | None = None,
    sort: Literal["newest", "oldest", "updated", "priority"] = "newest",
) -> TicketFilters:
    return TicketFilters(
        q=q,
        status=status,
        priority=priority,
        category=category,
        assignee_id=assignee_id,
        reporter_id=reporter_id,
        mine=mine,
        created_from=created_from,
        created_to=created_to,
        sort=sort,
    )


Filters = Annotated[TicketFilters, Depends(ticket_filters)]


@router.get("", response_model=Page[TicketOut], summary="List tickets visible to the current user")
def list_tickets(user: CurrentUser, db: DbSession, paging: PageParams, filters: Filters) -> Page[TicketOut]:
    rows, total = ticket_service.list_tickets(db, user, filters, page=paging.page, page_size=paging.page_size)
    return Page.build([ticket_service.serialize(t, user) for t in rows], total, paging.page, paging.page_size)


@router.post("", response_model=TicketOut, status_code=201, summary="Report a new ticket")
def create_ticket(data: TicketCreate, user: CurrentUser, db: DbSession) -> TicketOut:
    return ticket_service.serialize(ticket_service.create_ticket(db, user, data), user)


# NOTE: this route must be declared before "/{ticket_id}".
CSV_COLUMNS = [
    "ticket_number", "title", "category", "priority", "status", "reporter", "assignee",
    "asset", "created_at", "updated_at", "resolved_at", "closed_at", "resolution_note",
]


def _safe_cell(value: object) -> str:
    """Prevent spreadsheet formula injection by neutralising cells that start with =, +, - or @."""
    text = "" if value is None else str(value)
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


@router.get("/export.csv", summary="Export tickets as CSV (admin)")
def export_csv(admin: AdminUser, db: DbSession, filters: Filters) -> Response:
    tickets = ticket_service.export_rows(db, admin, filters)
    buffer = io.StringIO()
    writer = csv.writer(buffer, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    writer.writerow(CSV_COLUMNS)

    def iso(dt: datetime | None) -> str:
        return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if dt else ""

    for t in tickets:
        writer.writerow(
            [
                _safe_cell(v)
                for v in (
                    t.ticket_number, t.title, t.category.value, t.priority.value, t.status.value,
                    t.reporter.display_name, t.assignee.display_name if t.assignee else "",
                    t.related_asset.asset_tag if t.related_asset else "",
                    iso(t.created_at), iso(t.updated_at), iso(t.resolved_at), iso(t.closed_at),
                    t.resolution_note or "",
                )
            ]
        )
    filename = f"infradesk-tickets-{datetime.now(UTC):%Y%m%d}.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{ticket_id}", response_model=TicketDetail, summary="Ticket with comments and history")
def get_ticket(ticket_id: int, user: CurrentUser, db: DbSession) -> TicketDetail:
    ticket = ticket_service.get_visible_ticket(db, user, ticket_id)
    return TicketDetail(
        ticket=ticket_service.serialize(ticket, user),
        comments=[CommentOut.model_validate(c) for c in ticket_service.list_comments(db, ticket)],
        history=[EventOut.model_validate(e) for e in ticket_service.list_history(db, ticket)],
    )


@router.patch("/{ticket_id}", response_model=TicketOut, summary="Edit ticket details (admin)")
def update_ticket(ticket_id: int, data: TicketUpdate, admin: AdminUser, db: DbSession) -> TicketOut:
    ticket = ticket_service.get_ticket(db, ticket_id)
    return ticket_service.serialize(ticket_service.update_ticket(db, admin, ticket, data), admin)


@router.post("/{ticket_id}/assign", response_model=TicketOut, summary="Assign a ticket (admin)")
def assign_ticket(ticket_id: int, data: AssignRequest, admin: AdminUser, db: DbSession) -> TicketOut:
    ticket = ticket_service.get_ticket(db, ticket_id)
    updated = ticket_service.assign_ticket(db, admin, ticket, data.assignee_id, data.note)
    return ticket_service.serialize(updated, admin)


@router.post("/{ticket_id}/transition", response_model=TicketOut, summary="Change ticket status")
def transition_ticket(ticket_id: int, data: TransitionRequest, user: CurrentUser, db: DbSession) -> TicketOut:
    ticket = ticket_service.get_visible_ticket(db, user, ticket_id)
    updated = ticket_service.transition_ticket(db, user, ticket, data.status, data.resolution_note)
    return ticket_service.serialize(updated, user)


@router.post("/{ticket_id}/comments", response_model=CommentOut, status_code=201, summary="Add a comment / work note")
def add_comment(ticket_id: int, data: CommentCreate, user: CurrentUser, db: DbSession) -> CommentOut:
    ticket = ticket_service.get_visible_ticket(db, user, ticket_id)
    return CommentOut.model_validate(ticket_service.add_comment(db, user, ticket, data.body))


@router.get("/{ticket_id}/history", response_model=list[EventOut], summary="Ticket history")
def ticket_history(ticket_id: int, user: CurrentUser, db: DbSession) -> list[EventOut]:
    ticket = ticket_service.get_visible_ticket(db, user, ticket_id)
    return [EventOut.model_validate(e) for e in ticket_service.list_history(db, ticket)]
