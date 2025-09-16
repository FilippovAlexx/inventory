# app/tests/conftest.py
from __future__ import annotations

import asyncio
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.deps import get_db
from app.core.config import settings
from app.db.session import get_session  # <-- ВАЖНО: тоже переопределим!
from app.main import app
from app.models import Product
from app.models.user import User

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ---- единый движок/фабрика сессий для всех зависимостей ----
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    url = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    engine = create_async_engine(url, future=True, poolclass=NullPool)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def TestSession(test_engine):
    return async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


# ---- переопределяем и get_db, и get_session ----
@pytest_asyncio.fixture(autouse=True, scope="session")
async def override_db_dependencies(TestSession):
    async def _dep():
        async with TestSession() as session:
            yield session

    # обе зависимости на один и тот же провайдер
    app.dependency_overrides[get_db] = _dep
    app.dependency_overrides[get_session] = _dep
    yield
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_session, None)


# ---- http клиент ----
@pytest_asyncio.fixture()
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---- трекинг и зачистка ----
@pytest.fixture()
def created_emails() -> list[str]:
    return []


@pytest_asyncio.fixture(autouse=True)
async def cleanup_users(TestSession, created_emails: list[str]):
    yield
    if created_emails:
        async with TestSession() as s:
            await s.execute(delete(User).where(User.email.in_(created_emails)))
            await s.commit()


@pytest.fixture()
def created_skus() -> list[str]:
    return []


@pytest_asyncio.fixture(autouse=True)
async def cleanup_products(TestSession, created_skus: list[str]):
    yield
    if created_skus:
        async with TestSession() as s:
            await s.execute(delete(Product).where(Product.sku.in_(created_skus)))
            await s.commit()


# ---- хелперы токенов/регистрации как у тебя было ----
def _admin_header() -> dict:
    return {"X-Admin-Secret": settings.APP_SECRET} if settings.APP_SECRET else {}


async def _register(client: AsyncClient, email: str, password: str, role: str = "viewer"):
    payload = {"email": email, "password": password, "role": role}
    return await client.post("/auth/register", json=payload, headers=_admin_header())


async def _token(client: AsyncClient, email: str, password: str) -> str:
    resp = await client.post("/auth/token", data={"username": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture()
async def admin_token(client: AsyncClient, created_emails: list[str]) -> str:
    email, pwd = "admin_test@example.com", "Str0ngP@ss!"
    r = await _register(client, email, pwd, role="admin")
    assert r.status_code in (200, 201, 409), r.text
    if r.status_code in (200, 201):
        created_emails.append(email)
    return await _token(client, email, pwd)


@pytest_asyncio.fixture()
async def viewer_token(client: AsyncClient, created_emails: list[str]) -> str:
    email, pwd = "viewer_test@example.com", "Str0ngP@ss!"
    r = await _register(client, email, pwd, role="viewer")
    assert r.status_code in (200, 201, 409), r.text
    if r.status_code in (200, 201):
        created_emails.append(email)
    return await _token(client, email, pwd)
