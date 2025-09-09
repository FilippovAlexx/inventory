from __future__ import annotations

from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, IsActiveMixin, UUIDPKMixin


class Supplier(UUIDPKMixin, CreatedAtMixin, IsActiveMixin, Base):
    """Поставщик."""
    __tablename__ = "supplier"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(64))

    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder", back_populates="supplier", lazy="selectin"
    )
