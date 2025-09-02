from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class AdjustRequest(BaseModel):
    product_id: UUID
    location_id: UUID
    delta: Decimal = Field(description="Positive or negative change; e.g., 5 or -2.5")
    reason: str | None = None


class MoveRequest(BaseModel):
    product_id: UUID
    from_location_id: UUID
    to_location_id: UUID
    qty: Decimal
    reason: str | None = None


class ReserveRequest(BaseModel):
    product_id: UUID
    location_id: UUID
    qty: Decimal
    reference: str | None = None


class ReleaseRequest(BaseModel):
    product_id: UUID
    location_id: UUID
    qty: Decimal
    reference: str | None = None


class InventorySnapshot(BaseModel):
    product_id: UUID
    location_id: UUID
    on_hand: Decimal
    reserved: Decimal
    available: Decimal
