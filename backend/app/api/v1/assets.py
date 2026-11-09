from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, CurrentUser, DbSession, PageParams
from app.models.enums import AssetStatus, AssetType
from app.schemas.asset import AssetCreate, AssetOut, AssetUpdate
from app.schemas.common import Page
from app.services import asset_service

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=Page[AssetOut], summary="List assets (any signed-in user)")
def list_assets(
    user: CurrentUser,
    db: DbSession,
    paging: PageParams,
    q: Annotated[str | None, Query(max_length=80)] = None,
    status: AssetStatus | None = None,
    asset_type: AssetType | None = None,
    include_retired: bool = True,
) -> Page[AssetOut]:
    rows, total = asset_service.list_assets(
        db,
        page=paging.page,
        page_size=paging.page_size,
        q=q,
        status=status,
        asset_type=asset_type,
        include_retired=include_retired,
    )
    return Page.build([AssetOut.model_validate(a) for a in rows], total, paging.page, paging.page_size)


@router.post("", response_model=AssetOut, status_code=201, summary="Create an asset (admin)")
def create_asset(data: AssetCreate, admin: AdminUser, db: DbSession) -> AssetOut:
    return AssetOut.model_validate(asset_service.create_asset(db, admin, data))


@router.get("/{asset_id}", response_model=AssetOut, summary="Get an asset")
def get_asset(asset_id: int, user: CurrentUser, db: DbSession) -> AssetOut:
    return AssetOut.model_validate(asset_service.get_asset(db, asset_id))


@router.patch("/{asset_id}", response_model=AssetOut, summary="Update an asset (admin)")
def update_asset(asset_id: int, data: AssetUpdate, admin: AdminUser, db: DbSession) -> AssetOut:
    asset = asset_service.get_asset(db, asset_id)
    return AssetOut.model_validate(asset_service.update_asset(db, admin, asset, data))


@router.post("/{asset_id}/retire", response_model=AssetOut, summary="Retire an asset (admin)")
def retire_asset(asset_id: int, admin: AdminUser, db: DbSession) -> AssetOut:
    asset = asset_service.get_asset(db, asset_id)
    return AssetOut.model_validate(asset_service.retire_asset(db, admin, asset))
