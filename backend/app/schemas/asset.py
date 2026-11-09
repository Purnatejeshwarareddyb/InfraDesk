from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.enums import AssetStatus, AssetType
from app.schemas.common import ORMModel, text


class AssetBrief(ORMModel):
    id: int
    asset_tag: str
    name: str
    status: AssetStatus


class AssetOut(ORMModel):
    id: int
    asset_tag: str
    name: str
    asset_type: AssetType
    location: str
    serial_number: str | None
    status: AssetStatus
    notes: str
    created_at: datetime
    updated_at: datetime


class AssetCreate(BaseModel):
    asset_tag: text(2, 40)
    name: text(2, 120)
    asset_type: AssetType = AssetType.OTHER
    location: text(0, 120) = ""
    serial_number: text(0, 80) | None = None
    status: AssetStatus = AssetStatus.ACTIVE
    notes: text(0, 2000) = ""

    @field_validator("asset_tag")
    @classmethod
    def _upper(cls, value: str) -> str:
        return value.upper()

    @field_validator("serial_number")
    @classmethod
    def _empty_to_none(cls, value: str | None) -> str | None:
        return value or None


class AssetUpdate(BaseModel):
    asset_tag: text(2, 40) | None = None
    name: text(2, 120) | None = None
    asset_type: AssetType | None = None
    location: text(0, 120) | None = None
    serial_number: text(0, 80) | None = None
    status: AssetStatus | None = None
    notes: text(0, 2000) | None = None

    @field_validator("asset_tag")
    @classmethod
    def _upper(cls, value: str | None) -> str | None:
        return value.upper() if value else value
