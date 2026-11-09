from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UTCDateTime, utcnow
from app.models.enums import AssetStatus, AssetType
from app.models.user import enum_column


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True)
    asset_tag: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    asset_type: Mapped[AssetType] = mapped_column(enum_column(AssetType), default=AssetType.OTHER)
    location: Mapped[str] = mapped_column(String(120), default="")
    serial_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[AssetStatus] = mapped_column(enum_column(AssetStatus), default=AssetStatus.ACTIVE, index=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
