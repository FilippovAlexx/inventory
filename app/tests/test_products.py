# app/tests/test_products.py
from __future__ import annotations

import pytest
from httpx import AsyncClient


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_product_as_admin_ok(
    client: AsyncClient, admin_token: str, created_skus: list[str]
):
    sku = "SKU-ADM-OK-001"
    payload = {
        "sku": sku,
        "name": "Admin Created Product",
        "unit": "pcs",
        "description": "created by admin in tests",
    }

    r = await client.post("/products", json=payload, headers=_bearer(admin_token))
    assert r.status_code in (200, 201), r.text

    body = r.json()
    assert body["sku"] == sku
    assert body["name"] == payload["name"]
    assert body["unit"] == payload["unit"]
    assert "id" in body

    created_skus.append(sku)


@pytest.mark.asyncio
async def test_create_product_duplicate(
    client: AsyncClient, admin_token: str, created_skus: list[str]
):
    sku = "SKU-DUP-001"
    payload = {"sku": sku, "name": "Dup", "unit": "pcs"}

    r1 = await client.post("/products", json=payload, headers=_bearer(admin_token))
    assert r1.status_code in (200, 201), r1.text
    created_skus.append(sku)

    r2 = await client.post("/products", json=payload, headers=_bearer(admin_token))
    assert r2.status_code == 409, r2.text
    assert r2.json().get("detail") == "SKU already exists"


@pytest.mark.asyncio
async def test_create_product_forbidden_for_viewer(
    client: AsyncClient, viewer_token: str
):
    sku = "SKU-VIEWER-FORBID-001"
    payload = {"sku": sku, "name": "Nope", "unit": "pcs"}

    r = await client.post("/products", json=payload, headers=_bearer(viewer_token))
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_create_product_unauthorized(client: AsyncClient):
    sku = "SKU-UNAUTH-001"
    payload = {"sku": sku, "name": "No token", "unit": "pcs"}

    r = await client.post("/products", json=payload)  # без токена
    # get_current_user в итоге вернёт 401
    assert r.status_code == 401, r.text
