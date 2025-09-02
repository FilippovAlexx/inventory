from __future__ import annotations
from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal

class SupplierCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None

class SupplierOut(BaseModel):
    id: UUID
    name: str

class PurchaseOrderCreate(BaseModel):
    supplier_id: UUID

class PurchaseOrderOut(BaseModel):
    id: UUID
    supplier_id: UUID
    status: str

class PurchaseOrderLineCreate(BaseModel):
    product_id: UUID
    qty_ordered: Decimal
    unit_cost: Decimal | None = None

class PurchaseReceiveLine(BaseModel):
    line_id: UUID
    qty: Decimal
    location_id: UUID

class PurchaseReceiveRequest(BaseModel):
    lines: list[PurchaseReceiveLine]
