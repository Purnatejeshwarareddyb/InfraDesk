"""Ticket business rules: visibility, workflow transitions, assignment, comments, history."""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models.asset import Asset
from app.models.audit_event import AuditEvent
from app.models.enums import (
    AssetStatus,
    Category,
    EventType,
    NotificationType,
    Priority,
    Role,
    TicketStatus,
)
from app.models.ticket import Ticket
from app.models.ticket_comment import TicketComment
from app.models.user import User
from app.schemas.ticket import TicketCreate, TicketOut, TicketUpdate
from app.services import audit_service, notification_service

S = TicketStatus

# The complete workflow. A move that is not listed here is never allowed.
TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    S.OPEN: {S.ASSIGNED, S.IN_PROGRESS, S.CANCELLED},
    S.ASSIGNED: {S.IN_PROGRESS, S.WAITING, S.CANCELLED},
    S.IN_PROGRESS: {S.WAITING, S.RESOLVED},
    S.WAITING: {S.IN_PROGRESS, S.RESOLVED},
    S.RESOLVED: {S.CLOSED, S.IN_PROGRESS},
    S.CLOSED: {S.IN_PROGRESS},
    S.CANCELLED: set(),
}

ASSIGNABLE_STATUSES = {S.OPEN, S.ASSIGNED, S.IN_PROGRESS, S.WAITING}
PRIORITY_RANK = {Priority.URGENT: 0, Priority.HIGH: 1, Priority.MEDIUM: 2, Priority.LOW: 3}


def _label(status: TicketStatus) -> str:
    """Human-readable status name for messages, e.g. IN_PROGRESS -> "In progress"."""
    return status.value.replace("_", " ").capitalize()


# ---------------------------------------------------------------- permissions


def can_view(actor: User, ticket: Ticket) -> bool:
    return actor.role == Role.ADMIN or actor.id in (ticket.reporter_id, ticket.assignee_id)


def can_transition(actor: User, ticket: Ticket, target: TicketStatus) -> bool:
    """Whether `actor` may move `ticket` to `target` through the transition endpoint."""
    if target not in TRANSITIONS[ticket.status] or target == S.ASSIGNED:
        return False  # assignment has its own endpoint
    if actor.role == Role.ADMIN:
        return True
    is_assignee = ticket.assignee_id == actor.id
    is_reporter = ticket.reporter_id == actor.id
    if target == S.CANCELLED:
        return is_reporter and ticket.status == S.OPEN
    if ticket.status == S.OPEN:
        return False  # starting work from OPEN is an administrator action (takes ownership)
    if ticket.status == S.CLOSED:
        return False  # reopening a closed ticket is administrator only
    if target == S.CLOSED:
        return False  # only administrators close tickets
    return is_assignee and target in {S.IN_PROGRESS, S.WAITING, S.RESOLVED}


def allowed_transitions(actor: User, ticket: Ticket) -> list[TicketStatus]:
    return [t for t in TicketStatus if can_transition(actor, ticket, t)]


def serialize(ticket: Ticket, actor: User) -> TicketOut:
    out = TicketOut.model_validate(ticket)
    out.allowed_transitions = allowed_transitions(actor, ticket)
    return out


# ------------------------------------------------------------------- lookups


def get_ticket(db: Session, ticket_id: int) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise NotFoundError("Ticket not found.")
    return ticket


def get_visible_ticket(db: Session, actor: User, ticket_id: int) -> Ticket:
    """Return the ticket, or a 404 if it does not exist or the actor may not see it."""
    ticket = db.get(Ticket, ticket_id)
    if ticket is None or not can_view(actor, ticket):
        raise NotFoundError("Ticket not found.")
    return ticket


def _check_asset(db: Session, asset_id: int | None) -> None:
    if asset_id is None:
        return
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise BusinessRuleError("The selected asset does not exist.", code="asset_not_found")
    if asset.status == AssetStatus.RETIRED:
        raise BusinessRuleError("A retired asset cannot be linked to a ticket.", code="asset_retired")


# --------------------------------------------------------------------- list


@dataclass
class TicketFilters:
    q: str | None = None
    status: TicketStatus | None = None
    priority: Priority | None = None
    category: Category | None = None
    assignee_id: int | None = None
    reporter_id: int | None = None
    mine: bool = False
    created_from: date | None = None
    created_to: date | None = None
    sort: str = "newest"


def _conditions(actor: User, f: TicketFilters) -> list:
    conditions = []
    if actor.role != Role.ADMIN:
        conditions.append(or_(Ticket.reporter_id == actor.id, Ticket.assignee_id == actor.id))
    if f.mine:
        conditions.append(or_(Ticket.reporter_id == actor.id, Ticket.assignee_id == actor.id))
    if f.q:
        term = f.q.strip().lower()
        like = f"%{term}%"
        matching_users = select(User.id).where(
            or_(func.lower(User.username).like(like), func.lower(User.display_name).like(like))
        )
        clauses = [
            func.lower(Ticket.ticket_number).like(like),
            func.lower(Ticket.title).like(like),
            Ticket.reporter_id.in_(matching_users),
            Ticket.assignee_id.in_(matching_users),
        ]
        digits = term.removeprefix("hd-").lstrip("0")
        if digits.isdigit():
            clauses.append(Ticket.id == int(digits))
        conditions.append(or_(*clauses))
    if f.status:
        conditions.append(Ticket.status == f.status)
    if f.priority:
        conditions.append(Ticket.priority == f.priority)
    if f.category:
        conditions.append(Ticket.category == f.category)
    if f.assignee_id is not None:
        conditions.append(Ticket.assignee_id == f.assignee_id)
    if f.reporter_id is not None:
        conditions.append(Ticket.reporter_id == f.reporter_id)
    if f.created_from:
        conditions.append(Ticket.created_at >= datetime.combine(f.created_from, time.min, tzinfo=UTC))
    if f.created_to:
        conditions.append(
            Ticket.created_at < datetime.combine(f.created_to + timedelta(days=1), time.min, tzinfo=UTC)
        )
    return conditions


def _ordering(sort: str) -> list:
    if sort == "oldest":
        return [Ticket.created_at.asc(), Ticket.id.asc()]
    if sort == "updated":
        return [Ticket.updated_at.desc(), Ticket.id.desc()]
    if sort == "priority":
        rank = case(*[(Ticket.priority == p, r) for p, r in PRIORITY_RANK.items()], else_=9)
        return [rank.asc(), Ticket.created_at.desc(), Ticket.id.desc()]
    return [Ticket.created_at.desc(), Ticket.id.desc()]


def list_tickets(
    db: Session, actor: User, filters: TicketFilters, *, page: int, page_size: int
) -> tuple[list[Ticket], int]:
    conditions = _conditions(actor, filters)
    total = db.scalar(select(func.count(Ticket.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(Ticket)
        .where(*conditions)
        .order_by(*_ordering(filters.sort))
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).unique().all()
    return list(rows), total


def export_rows(db: Session, actor: User, filters: TicketFilters, limit: int = 20000) -> list[Ticket]:
    conditions = _conditions(actor, filters)
    return list(
        db.scalars(select(Ticket).where(*conditions).order_by(*_ordering(filters.sort)).limit(limit)).unique().all()
    )


# ------------------------------------------------------------------- create


def create_ticket(db: Session, actor: User, data: TicketCreate) -> Ticket:
    _check_asset(db, data.related_asset_id)
    ticket = Ticket(
        ticket_number=f"TMP-{uuid.uuid4().hex[:12]}",
        title=data.title,
        description=data.description,
        category=data.category,
        priority=data.priority,
        status=S.OPEN,
        reporter_id=actor.id,
        related_asset_id=data.related_asset_id,
    )
    db.add(ticket)
    db.flush()
    ticket.ticket_number = f"HD-{ticket.id:06d}"
    audit_service.record(
        db,
        event_type=EventType.TICKET_CREATED,
        actor_id=actor.id,
        ticket_id=ticket.id,
        new_value=S.OPEN.value,
        detail=f"Ticket created with priority {ticket.priority.value}.",
    )
    notification_service.notify(
        db,
        recipient_ids=notification_service.active_admin_ids(db) - {actor.id},
        ticket_id=ticket.id,
        type_=NotificationType.TICKET_CREATED,
        message=f"{actor.display_name} reported {ticket.ticket_number}: {ticket.title}",
    )
    db.commit()
    db.refresh(ticket)
    return ticket


# ------------------------------------------------------------------- update


def update_ticket(db: Session, actor: User, ticket: Ticket, data: TicketUpdate) -> Ticket:
    changes = data.model_dump(exclude_unset=True)
    clear_asset = changes.pop("clear_related_asset", False)
    if clear_asset:
        changes["related_asset_id"] = None
    if "related_asset_id" in changes and changes["related_asset_id"] is not None:
        _check_asset(db, changes["related_asset_id"])

    for field, new in changes.items():
        if field != "related_asset_id" and new is None:
            continue
        old = getattr(ticket, field)
        if old == new:
            continue
        setattr(ticket, field, new)
        shown_old = old.value if hasattr(old, "value") else (None if old is None else str(old))
        shown_new = new.value if hasattr(new, "value") else (None if new is None else str(new))
        long_text = field in {"title", "description"}
        audit_service.record(
            db,
            event_type=EventType.TICKET_UPDATED,
            actor_id=actor.id,
            ticket_id=ticket.id,
            old_value=None if long_text else (shown_old[:255] if shown_old else None),
            new_value=None if long_text else (shown_new[:255] if shown_new else None),
            detail=f"Changed {field.replace('_', ' ')}.",
        )
    db.commit()
    db.refresh(ticket)
    return ticket


# ------------------------------------------------------------------- assign


def assign_ticket(db: Session, actor: User, ticket: Ticket, assignee_id: int, note: str | None = None) -> Ticket:
    assignee = db.get(User, assignee_id)
    if assignee is None or not assignee.is_active:
        raise BusinessRuleError("The selected user does not exist or is inactive.", code="invalid_assignee")
    if ticket.status not in ASSIGNABLE_STATUSES:
        raise BusinessRuleError(
            f"A ticket in status {ticket.status.value} cannot be assigned.", code="not_assignable"
        )
    if ticket.assignee_id == assignee.id:
        raise BusinessRuleError(f"The ticket is already assigned to {assignee.display_name}.", code="same_assignee")

    previous = ticket.assignee
    ticket.assignee_id = assignee.id
    ticket.assignee = assignee
    audit_service.record(
        db,
        event_type=EventType.TICKET_ASSIGNED,
        actor_id=actor.id,
        ticket_id=ticket.id,
        old_value=previous.display_name if previous else None,
        new_value=assignee.display_name,
        detail=note or "",
    )
    if ticket.status == S.OPEN:
        ticket.status = S.ASSIGNED
        audit_service.record(
            db,
            event_type=EventType.STATUS_CHANGED,
            actor_id=actor.id,
            ticket_id=ticket.id,
            old_value=S.OPEN.value,
            new_value=S.ASSIGNED.value,
            detail="Status changed by assignment.",
        )
    if assignee.id != actor.id:
        notification_service.notify(
            db,
            recipient_ids={assignee.id},
            ticket_id=ticket.id,
            type_=NotificationType.TICKET_ASSIGNED,
            message=f"You were assigned {ticket.ticket_number}: {ticket.title}",
        )
    if ticket.reporter_id not in (actor.id, assignee.id):
        notification_service.notify(
            db,
            recipient_ids={ticket.reporter_id},
            ticket_id=ticket.id,
            type_=NotificationType.TICKET_ASSIGNED,
            message=f"{ticket.ticket_number} was assigned to {assignee.display_name}.",
        )
    db.commit()
    db.refresh(ticket)
    return ticket


# --------------------------------------------------------------- transition


def transition_ticket(
    db: Session, actor: User, ticket: Ticket, target: TicketStatus, resolution_note: str | None = None
) -> Ticket:
    if target == S.ASSIGNED:
        raise BusinessRuleError("Use the assign action to assign a ticket.", code="use_assign")
    if target not in TRANSITIONS[ticket.status]:
        raise BusinessRuleError(
            f"A ticket cannot move from {ticket.status.value} to {target.value}.", code="invalid_transition"
        )
    if not can_transition(actor, ticket, target):
        raise BusinessRuleError(
            f"You are not allowed to move this ticket to {target.value}.", code="transition_not_permitted"
        )
    if target == S.RESOLVED and not (resolution_note and resolution_note.strip()):
        raise BusinessRuleError("A resolution note is required to resolve a ticket.", code="resolution_required")

    old = ticket.status
    now = datetime.now(UTC)

    if target == S.IN_PROGRESS and ticket.assignee_id is None:
        # Only reachable by an administrator starting an unassigned ticket: they take ownership.
        ticket.assignee_id = actor.id
        ticket.assignee = actor
        audit_service.record(
            db,
            event_type=EventType.TICKET_ASSIGNED,
            actor_id=actor.id,
            ticket_id=ticket.id,
            new_value=actor.display_name,
            detail="Administrator took ownership of the ticket.",
        )

    ticket.status = target
    if target == S.RESOLVED:
        ticket.resolution_note = resolution_note.strip()
        ticket.resolved_at = now
    elif target == S.CLOSED:
        ticket.closed_at = now
    elif target == S.IN_PROGRESS and old in (S.RESOLVED, S.CLOSED):
        ticket.resolved_at = None
        ticket.closed_at = None

    audit_service.record(
        db,
        event_type=EventType.STATUS_CHANGED,
        actor_id=actor.id,
        ticket_id=ticket.id,
        old_value=old.value,
        new_value=target.value,
        detail=(resolution_note.strip()[:250] if target == S.RESOLVED and resolution_note else ""),
    )

    recipients = {ticket.reporter_id}
    if ticket.assignee_id:
        recipients.add(ticket.assignee_id)
    if target == S.RESOLVED:
        recipients |= notification_service.active_admin_ids(db)
    recipients.discard(actor.id)
    notification_service.notify(
        db,
        recipient_ids=recipients,
        ticket_id=ticket.id,
        type_=NotificationType.TICKET_STATUS,
        message=f"{ticket.ticket_number} changed from {_label(old)} to {_label(target)} by {actor.display_name}.",
    )
    db.commit()
    db.refresh(ticket)
    return ticket


# ----------------------------------------------------------------- comments


def add_comment(db: Session, actor: User, ticket: Ticket, body: str) -> TicketComment:
    comment = TicketComment(ticket_id=ticket.id, author_id=actor.id, body=body)
    db.add(comment)
    ticket.updated_at = datetime.now(UTC)
    db.flush()
    audit_service.record(
        db,
        event_type=EventType.COMMENT_ADDED,
        actor_id=actor.id,
        ticket_id=ticket.id,
        detail=body[:120],
    )
    recipients = {ticket.reporter_id}
    if ticket.assignee_id:
        recipients.add(ticket.assignee_id)
    recipients.discard(actor.id)
    notification_service.notify(
        db,
        recipient_ids=recipients,
        ticket_id=ticket.id,
        type_=NotificationType.TICKET_COMMENT,
        message=f"{actor.display_name} commented on {ticket.ticket_number}.",
    )
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(db: Session, ticket: Ticket) -> list[TicketComment]:
    return list(
        db.scalars(
            select(TicketComment).where(TicketComment.ticket_id == ticket.id).order_by(TicketComment.created_at, TicketComment.id)
        )
        .unique()
        .all()
    )


def list_history(db: Session, ticket: Ticket) -> list[AuditEvent]:
    return list(
        db.scalars(
            select(AuditEvent).where(AuditEvent.ticket_id == ticket.id).order_by(AuditEvent.created_at, AuditEvent.id)
        )
        .unique()
        .all()
    )
