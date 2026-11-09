from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.asset import Asset
from app.models.enums import AssetStatus, AssetType, EventType
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetUpdate
from app.services import audit_service


def get_asset(db: Session, asset_id: int) -> Asset:
    asset = db.get(Asset, asset_id)
    if asset is None:
        raise NotFoundError("Asset not found.")
    return asset


def list_assets(
    db: Session,
    *,
    page: int,
    page_size: int,
    q: str | None = None,
    status: AssetStatus | None = None,
    asset_type: AssetType | None = None,
    include_retired: bool = True,
) -> tuple[list[Asset], int]:
    conditions = []
    if q:
        like = f"%{q.strip().lower()}%"
        conditions.append(
            or_(
                func.lower(Asset.asset_tag).like(like),
                func.lower(Asset.name).like(like),
                func.lower(Asset.location).like(like),
                func.lower(func.coalesce(Asset.serial_number, "")).like(like),
            )
        )
    if status:
        conditions.append(Asset.status == status)
    elif not include_retired:
        conditions.append(Asset.status != AssetStatus.RETIRED)
    if asset_type:
        conditions.append(Asset.asset_type == asset_type)
    total = db.scalar(select(func.count(Asset.id)).where(*conditions)) or 0
    rows = db.scalars(
        select(Asset).where(*conditions).order_by(Asset.asset_tag).limit(page_size).offset((page - 1) * page_size)
    ).all()
    return list(rows), total


def create_asset(db: Session, actor: User, data: AssetCreate) -> Asset:
    asset = Asset(**data.model_dump())
    db.add(asset)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise ConflictError("An asset with that tag already exists.", code="asset_tag_taken") from None
    audit_service.record(
        db, event_type=EventType.ASSET_CREATED, actor_id=actor.id, detail=f"Created asset {asset.asset_tag} ({asset.name})."
    )
    db.commit()
    return asset


def update_asset(db: Session, actor: User, asset: Asset, data: AssetUpdate) -> Asset:
    changes = data.model_dump(exclude_unset=True)
    changed_fields = []
    for field, value in changes.items():
        if field == "serial_number":
            value = value or None
        if value is not None or field == "serial_number":
            if getattr(asset, field) != value:
                setattr(asset, field, value)
                changed_fields.append(field)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise ConflictError("An asset with that tag already exists.", code="asset_tag_taken") from None
    if changed_fields:
        audit_service.record(
            db,
            event_type=EventType.ASSET_UPDATED,
            actor_id=actor.id,
            detail=f"Updated asset {asset.asset_tag}: {', '.join(changed_fields)}.",
        )
    db.commit()
    return asset


def retire_asset(db: Session, actor: User, asset: Asset) -> Asset:
    """Assets are retired, never deleted, so tickets that refer to them stay valid."""
    if asset.status != AssetStatus.RETIRED:
        asset.status = AssetStatus.RETIRED
        audit_service.record(
            db, event_type=EventType.ASSET_RETIRED, actor_id=actor.id, detail=f"Retired asset {asset.asset_tag}."
        )
        db.commit()
    return asset
