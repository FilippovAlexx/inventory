from __future__ import annotations

import enum
from typing import List

from sqlalchemy import Enum, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPKMixin


class POStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class PurchaseOrder(UUIDPKMixin, CreatedAtMixin, Base):
    """Заказ поставщику."""
    __tablename__ = "purchase_order"

    supplier_id: Mapped[object] = mapped_column(
        ForeignKey("supplier.id", ondelete="RESTRICT"),
        nullable=False
    )
    status: Mapped[POStatus] = mapped_column(
        Enum(POStatus, name="po_status"), nullable=False, default=POStatus.DRAFT
    )

    supplier = relationship("Supplier", back_populates="purchase_orders", lazy="selectin")
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine", back_populates="purchase_order",
        cascade="all, delete-orphan", lazy="selectin"
    )


class PurchaseOrderLine(UUIDPKMixin, Base):
    """Позиция заказа поставщику."""
    __tablename__ = "purchase_order_line"
    __table_args__ = (
        UniqueConstraint("purchase_order_id", "product_id", name="uq_pol_po_product"),
    )

    purchase_order_id: Mapped[object] = mapped_column(
        ForeignKey("purchase_order.id", ondelete="CASCADE"), nullable=False
    )
    product_id: Mapped[object] = mapped_column(
        ForeignKey("product.id", ondelete="RESTRICT"),
        nullable=False
    )

    qty_ordered: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False)
    qty_received: Mapped[float] = mapped_column(Numeric(14, 4), nullable=False, default=0)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(14, 4))

    purchase_order = relationship("PurchaseOrder", back_populates="lines", lazy="selectin")
    product = relationship("Product", back_populates="po_lines", lazy="selectin")
