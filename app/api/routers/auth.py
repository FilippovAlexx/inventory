from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import (
    create_access_token,
    get_current_user,
    get_password_hash,
    verify_password
)
from app.models.user import Role, User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    x_admin_secret: str | None = Header(default=None, alias="X-Admin-Secret")
):
    print("DEBUG register:", x_admin_secret, settings.APP_SECRET, flush=True)
    if x_admin_secret != settings.APP_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    exists = await db.scalar(select(User).where(User.email == data.email))
    if exists:
        raise HTTPException(status_code=409, detail="User already exists")
    user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=get_password_hash(data.password),
        role=Role(data.role)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut(id=user.id, email=user.email, full_name=user.full_name, role=user.role.value)


@router.post("/token", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(User).where(User.email == form.username))
    user = q.scalars().first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    token = create_access_token(sub=str(user.id), role=user.role.value)
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current: User = Depends(get_current_user)):
    return UserOut(
        id=current.id,
        email=current.email,
        full_name=current.full_name,
        role=current.role.value
    )
