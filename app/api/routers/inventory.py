from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.models import InventoryItem
from app.schemas.inventory import (
    AdjustRequest,
    MoveRequest,
    ReserveRequest,
    ReleaseRequest,
    InventorySnapshot,
)
from app.services.inventory import adjust_stock, move_stock, reserve_stock, release_reservation, ship_reserved

router = APIRouter(prefix="/inventory", tags=["inventory"])

@router.get("/snapshot", response_model=list[InventorySnapshot])
async def snapshot(product_id: str | None = None, location_id: str | None = None, db: AsyncSession = Depends(get_db)):
    q = select(InventoryItem)
    if product_id:
        q = q.where(InventoryItem.product_id == product_id)
    if location_id:
        q = q.where(InventoryItem.location_id == location_id)
    res = await db.execute(q)
    items = res.scalars().all()
    out: list[InventorySnapshot] = []
    for it in items:
        on_hand = it.on_hand or 0
        reserved = it.reserved or 0
        out.append(
            InventorySnapshot(
                product_id=it.product_id,
                location_id=it.location_id,
                on_hand=on_hand,
                reserved=reserved,
                available=(on_hand - reserved),
            )
        )
    return out

@router.post("/adjust")
async def adjust(data: AdjustRequest, db: AsyncSession = Depends(get_db)):
    try:
        item = await adjust_stock(db, product_id=data.product_id, location_id=data.location_id, delta=data.delta, reason=data.reason)
        return {"status": "ok", "product_id": str(item.product_id), "location_id": str(item.location_id), "on_hand": str(item.on_hand), "reserved": str(item.reserved)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/move")
async def move(data: MoveRequest, db: AsyncSession = Depends(get_db)):
    try:
        await move_stock(db, product_id=data.product_id, from_location_id=data.from_location_id, to_location_id=data.to_location_id, qty=data.qty, reason=data.reason)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reserve")
async def reserve(data: ReserveRequest, db: AsyncSession = Depends(get_db)):
    try:
        item = await reserve_stock(db, product_id=data.product_id, location_id=data.location_id, qty=data.qty, reference=data.reference)
        return {"status": "ok", "reserved": str(item.reserved)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/release")
async def release(data: ReleaseRequest, db: AsyncSession = Depends(get_db)):
    try:
        item = await release_reservation(db, product_id=data.product_id, location_id=data.location_id, qty=data.qty, reference=data.reference)
        return {"status": "ok", "reserved": str(item.reserved)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ship")
async def ship(data: ReserveRequest, db: AsyncSession = Depends(get_db)):
    try:
        item = await ship_reserved(db, product_id=data.product_id, location_id=data.location_id, qty=data.qty, reference=data.reference)
        return {"status": "ok", "on_hand": str(item.on_hand), "reserved": str(item.reserved)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
