"""Import every model so that Base.metadata knows all tables."""

from app.models.asset import Asset
from app.models.audit_event import AuditEvent
from app.models.notification import Notification
from app.models.ticket import Ticket
from app.models.ticket_comment import TicketComment
from app.models.user import User

__all__ = ["Asset", "AuditEvent", "Notification", "Ticket", "TicketComment", "User"]
