from __future__ import annotations

import csv
import io
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import require_roles
from app.models import Product
from app.schemas.product import ProductCreate, ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "",
    response_model=ProductOut,
    dependencies=[Depends(require_roles("operator", "admin"))]
)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    exists = await db.scalar(select(Product).where(Product.sku == data.sku))
    if exists:
        raise HTTPException(status_code=409, detail="SKU already exists")
    prod = Product(sku=data.sku, name=data.name, description=data.description, unit=data.unit)
    db.add(prod)
    await db.commit()
    await db.refresh(prod)
    return ProductOut(id=prod.id, sku=prod.sku, name=prod.name, unit=prod.unit)


@router.get("", response_model=list[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Product))
    return [ProductOut(id=p.id, sku=p.sku, name=p.name, unit=p.unit) for p in res.scalars().all()]


@router.post("/import-csv", dependencies=[Depends(require_roles("operator", "admin"))])
async def import_products_csv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file")
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    rows = []
    for row in reader:
        sku = (row.get("sku") or row.get("SKU") or "").strip()
        name = (row.get("name") or row.get("Name") or "").strip()
        if not sku or not name:
            continue
        unit = (row.get("unit") or row.get("Unit") or "pcs").strip() or "pcs"
        description = (row.get("description") or row.get("Description") or None)
        rows.append(
            {"id": uuid.uuid4(), "sku": sku, "name": name, "unit": unit, "description": description}
        )
    if not rows:
        return {"status": "ok", "inserted": 0}
    stmt = insert(Product).values(rows).on_conflict_do_nothing(index_elements=[Product.sku])
    await db.execute(stmt)
    await db.commit()
    return {"status": "ok", "inserted": len(rows)}
