from __future__ import annotations

import enum
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Index, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPKMixin


class InventoryTxnType(str, enum.Enum):
    ADJUSTMENT = "ADJUSTMENT"
    IN = "IN"
    OUT = "OUT"
    TRANSFER = "TRANSFER"
    RESERVE = "RESERVE"
    RELEASE = "RELEASE"


class InventoryItem(UUIDPKMixin, TimestampMixin, Base):
    """Строка остатка по паре (product, location)."""
    __tablename__ = "inventory_item"
    __table_args__ = (
        UniqueConstraint("product_id", "location_id", name="uq_inventory_item_product_location"),
        Index("ix_inventory_item_product_location", "product_id", "location_id"),
    )

    product_id: Mapped[object] = mapped_column(
        ForeignKey("product.id", ondelete="CASCADE"), nullable=False
    )
    location_id: Mapped[object] = mapped_column(
        ForeignKey("location.id", ondelete="CASCADE"), nullable=False
    )

    on_hand: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    reserved: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # relations
    product = relationship("Product", back_populates="inventory_items", lazy="selectin")
    location = relationship("Location", back_populates="inventory_items", lazy="selectin")


class InventoryTxn(UUIDPKMixin, CreatedAtMixin, Base):
    """Журнал движения запасов (append-only)."""
    __tablename__ = "inventory_txn"

    product_id: Mapped[object] = mapped_column(
        ForeignKey("product.id", ondelete="RESTRICT"), nullable=False
    )
    from_location_id: Mapped[Optional[object]] = mapped_column(
        ForeignKey("location.id", ondelete="SET NULL"), nullable=True
    )
    to_location_id: Mapped[Optional[object]] = mapped_column(
        ForeignKey("location.id", ondelete="SET NULL"), nullable=True
    )

    qty: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    txn_type: Mapped[InventoryTxnType] = mapped_column(
        Enum(InventoryTxnType, name="inventory_txn_type"), nullable=False
    )
    reason: Mapped[str | None] = mapped_column(String(255))
    reference: Mapped[str | None] = mapped_column(String(255))
