from datetime import date

from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.core.exceptions import BusinessRuleError
from app.schemas.report import Summary, TicketReport
from app.services import report_service

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/summary", response_model=Summary, summary="Dashboard figures (all tickets for admins, own tickets for workers)")
def summary(user: CurrentUser, db: DbSession) -> Summary:
    return report_service.summary(db, user)


@router.get("/tickets", response_model=TicketReport, summary="Ticket counts by status, category, priority, assignee (admin)")
def ticket_report(admin: AdminUser, db: DbSession, date_from: date | None = None, date_to: date | None = None) -> TicketReport:
    if date_from and date_to and date_from > date_to:
        raise BusinessRuleError("date_from must not be after date_to.", code="invalid_date_range")
    return report_service.ticket_report(db, date_from, date_to)
