from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP

from app.db.base import Base


class InventoryTxnType(str, enum.Enum):
    ADJUSTMENT = "ADJUSTMENT"
    IN = "IN"
    OUT = "OUT"
    TRANSFER = "TRANSFER"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"


class InventoryItem(Base):
    __tablename__ = "inventory_item"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product.id", ondelete="CASCADE"),
        nullable=False
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("location.id", ondelete="CASCADE"),
        nullable=False
    )
    on_hand: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    reserved: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    updated_at: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )


class InventoryTxn(Base):
    __tablename__ = "inventory_txn"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("product.id"),
        nullable=False
    )
    from_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("location.id"),
        nullable=True
    )
    to_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("location.id"),
        nullable=True
    )
    qty: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    txn_type: Mapped[InventoryTxnType] = mapped_column(
        Enum(InventoryTxnType, name="inventory_txn_type"),
        nullable=False
    )
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[object] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
