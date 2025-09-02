from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class IDModel(BaseModel):
    id: UUID


class Qty(BaseModel):
    qty: Decimal = Field(gt=0)
