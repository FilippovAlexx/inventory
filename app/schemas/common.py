from __future__ import annotations
from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal

class IDModel(BaseModel):
    id: UUID

class Qty(BaseModel):
    qty: Decimal = Field(gt=0)

