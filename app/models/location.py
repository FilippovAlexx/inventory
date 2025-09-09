from __future__ import annotations

from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import IsActiveMixin, TimestampMixin, UUIDPKMixin


class Location(UUIDPKMixin, TimestampMixin, IsActiveMixin, Base):
    """Локация/склад/ячейка. Пара (product, location) формирует остаток."""
    __tablename__ = "location"

    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    inventory_items: Mapped[List["InventoryItem"]] = relationship(
        "InventoryItem", back_populates="location", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Location {self.code} {self.name}>"
