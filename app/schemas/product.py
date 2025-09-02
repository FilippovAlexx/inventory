from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


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
