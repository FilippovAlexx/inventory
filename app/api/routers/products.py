from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import Product
from app.schemas.product import ProductCreate, ProductOut

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductOut)
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
