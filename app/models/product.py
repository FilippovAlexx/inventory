from __future__ import annotations

from typing import List

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IsActiveMixin, TimestampMixin, UUIDPKMixin


class Product(UUIDPKMixin, TimestampMixin, IsActiveMixin, Base):
    """Товар (SKU, имя, описание, единица измерения)."""
    __tablename__ = "product"

    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text())
    unit: Mapped[str] = mapped_column(String(16), nullable=False, default="pcs")

    # relations
    inventory_items: Mapped[List["InventoryItem"]] = relationship(
        "InventoryItem", back_populates="product", cascade="all, delete-orphan", lazy="selectin"
    )
    po_lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine", back_populates="product", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Product {self.sku} {self.name}>"
