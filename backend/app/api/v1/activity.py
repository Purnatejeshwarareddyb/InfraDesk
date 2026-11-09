from fastapi import APIRouter

from app.api.deps import AdminUser, DbSession, PageParams
from app.schemas.common import Page
from app.schemas.ticket import EventOut
from app.services import audit_service

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=Page[EventOut], summary="Audit trail of ticket and administrative events (admin)")
def list_activity(admin: AdminUser, db: DbSession, paging: PageParams) -> Page[EventOut]:
    rows, total = audit_service.list_events(db, page=paging.page, page_size=paging.page_size)
    return Page.build([EventOut.model_validate(e) for e in rows], total, paging.page, paging.page_size)
