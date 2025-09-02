from __future__ import annotations
from pydantic import BaseModel
from uuid import UUID

class LocationCreate(BaseModel):
    code: str
    name: str

class LocationOut(BaseModel):
    id: UUID
    code: str
    name: str
