from __future__ import annotations
from pydantic import BaseModel
from uuid import UUID

class ProductCreate(BaseModel):
    sku: str
    name: str
    description: str | None = None
    unit: str = "pcs"

class ProductOut(BaseModel):
    id: UUID
    sku: str
    name: str
    unit: str
