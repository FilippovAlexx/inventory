from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class LocationCreate(BaseModel):
    code: str
    name: str


class LocationOut(BaseModel):
    id: UUID
    code: str
    name: str
