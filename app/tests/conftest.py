# tests/conftest.py
from __future__ import annotations

import asyncio
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker, create_async_engine)
from sqlalchemy.pool import NullPool

from app.api.deps import get_db  # <- это мы будем переопределять
from app.core.config import settings
from app.main import app
from app.models.user import User

# --- критично для Windows + asyncpg ---
# if sys.platform.startswith("win"):
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# --------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    # делаем движок ТОЛЬКО для тестов, без пула (NullPool), чтобы не было «кросс-луп» коннектов
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
    # одна фабрика сессий для всех тестов
    return async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest_asyncio.fixture(autouse=True, scope="session")
async def override_db_dependency(TestSession):
    # Переопределяем get_db у FastAPI, чтобы ВСЕ запросы в тестах ходили через наш движок/сессию
    async def _get_db():
        async with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture()
async def client():
    # in-process HTTP клиент
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
def created_emails() -> list[str]:
    return []


@pytest_asyncio.fixture(autouse=True)
async def cleanup_users(TestSession, created_emails: list[str]):
    # после каждого теста удаляем созданных пользователей
    yield
    if created_emails:
        async with TestSession() as s:
            await s.execute(delete(User).where(User.email.in_(created_emails)))
            await s.commit()
