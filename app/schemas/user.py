from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    role: str = "operator"  # admin/operator/viewer


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str | None = None
    role: str
