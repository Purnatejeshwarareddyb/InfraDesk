"""Write audit/history events. Callers commit the surrounding transaction."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent
from app.models.enums import EventType


def record(
    db: Session,
    *,
    event_type: EventType,
    actor_id: int | None,
    detail: str = "",
    ticket_id: int | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        event_type=event_type,
        actor_id=actor_id,
        ticket_id=ticket_id,
        old_value=old_value,
        new_value=new_value,
        detail=detail,
    )
    db.add(event)
    return event


def list_events(db: Session, *, page: int, page_size: int, ticket_id: int | None = None) -> tuple[list[AuditEvent], int]:
    query = select(AuditEvent)
    count_query = select(func.count(AuditEvent.id))
    if ticket_id is not None:
        query = query.where(AuditEvent.ticket_id == ticket_id)
        count_query = count_query.where(AuditEvent.ticket_id == ticket_id)
    total = db.scalar(count_query) or 0
    rows = db.scalars(
        query.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(page_size).offset((page - 1) * page_size)
    ).all()
    return list(rows), total
