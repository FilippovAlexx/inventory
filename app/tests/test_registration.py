# tests/test_registration.py
from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.config import settings


def _headers() -> dict:
    return {"X-Admin-Secret": settings.APP_SECRET} if settings.APP_SECRET else {}


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient, created_emails: list[str]):
    email = "reg_ok_user@example.com"
    payload = {
        "email": email,
        "password": "Str0ngP@ss!",
        "full_name": "Tester",
        "role": "viewer",
    }

    r = await client.post("/auth/register", json=payload, headers=_headers())
    assert r.status_code in (200, 201), r.text

    body = r.json()
    assert body.get("email") == email
    assert body.get("role") == "viewer"
    assert "id" in body

    created_emails.append(email)


@pytest.mark.asyncio
async def test_register_duplicate_rejected(client: AsyncClient, created_emails: list[str]):
    email = "dup_user@example.com"
    payload = {
        "email": email,
        "password": "Str0ngP@ss!",
        "role": "viewer",
    }

    r1 = await client.post("/auth/register", json=payload, headers=_headers())
    assert r1.status_code in (200, 201), r1.text
    created_emails.append(email)

    r2 = await client.post("/auth/register", json=payload, headers=_headers())
    # Твой код на дубликат поднимает 409 (UserExistsError)
    assert r2.status_code == 409, r2.text
