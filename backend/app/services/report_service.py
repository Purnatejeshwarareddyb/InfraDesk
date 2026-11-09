"""Dashboard and report figures. Every number comes from a database query."""

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.enums import Category, Priority, Role, TicketStatus
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.report import CountItem, Summary, TicketReport

S = TicketStatus
ACTIVE_STATUSES = (S.OPEN, S.ASSIGNED, S.IN_PROGRESS, S.WAITING)


def _label(value: str) -> str:
    return value.replace("_", " ").capitalize()


def _count_by(db: Session, column, enum_cls, conditions: list) -> list[CountItem]:
    rows = dict(db.execute(select(column, func.count(Ticket.id)).where(*conditions).group_by(column)).all())
    counts = {(k.value if hasattr(k, "value") else k): v for k, v in rows.items()}
    return [CountItem(key=m.value, label=_label(m.value), count=counts.get(m.value, 0)) for m in enum_cls]


def _scope(actor: User) -> list:
    if actor.role == Role.ADMIN:
        return []
    return [or_(Ticket.reporter_id == actor.id, Ticket.assignee_id == actor.id)]


def summary(db: Session, actor: User, recent_limit: int = 10) -> Summary:
    scope = _scope(actor)
    by_status = _count_by(db, Ticket.status, TicketStatus, scope)
    by_priority = _count_by(db, Ticket.priority, Priority, scope)
    status_counts = {i.key: i.count for i in by_status}

    high_active = (
        db.scalar(
            select(func.count(Ticket.id)).where(
                *scope,
                Ticket.priority.in_([Priority.HIGH, Priority.URGENT]),
                Ticket.status.in_(ACTIVE_STATUSES),
            )
        )
        or 0
    )

    events_query = select(AuditEvent).order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(recent_limit)
    if actor.role != Role.ADMIN:
        visible = select(Ticket.id).where(*scope)
        events_query = events_query.where(AuditEvent.ticket_id.in_(visible))
    events = list(db.scalars(events_query).unique().all())

    return Summary(
        scope="all" if actor.role == Role.ADMIN else "mine",
        total=sum(status_counts.values()),
        open=status_counts[S.OPEN] + status_counts[S.ASSIGNED],
        in_progress=status_counts[S.IN_PROGRESS] + status_counts[S.WAITING],
        resolved=status_counts[S.RESOLVED] + status_counts[S.CLOSED],
        high_priority_active=high_active,
        by_status=by_status,
        by_priority=by_priority,
        recent_activity=events,  # type: ignore[arg-type]
    )


def ticket_report(db: Session, date_from: date | None, date_to: date | None) -> TicketReport:
    conditions = []
    if date_from:
        conditions.append(Ticket.created_at >= datetime.combine(date_from, time.min, tzinfo=UTC))
    if date_to:
        conditions.append(Ticket.created_at < datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC))

    by_status = _count_by(db, Ticket.status, TicketStatus, conditions)
    by_category = _count_by(db, Ticket.category, Category, conditions)
    by_priority = _count_by(db, Ticket.priority, Priority, conditions)

    assignee_rows = db.execute(
        select(User.id, User.display_name, func.count(Ticket.id))
        .select_from(Ticket)
        .outerjoin(User, User.id == Ticket.assignee_id)
        .where(*conditions)
        .group_by(User.id, User.display_name)
        .order_by(func.count(Ticket.id).desc())
    ).all()
    by_assignee = [
        CountItem(key=str(uid) if uid is not None else "unassigned", label=name or "Unassigned", count=count)
        for uid, name, count in assignee_rows
    ]

    return TicketReport(
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
        total=sum(i.count for i in by_status),
        by_status=by_status,
        by_category=by_category,
        by_priority=by_priority,
        by_assignee=by_assignee,
    )
