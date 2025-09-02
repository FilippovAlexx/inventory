from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.models import Location
from app.schemas.location import LocationCreate, LocationOut

router = APIRouter(prefix="/locations", tags=["locations"])

@router.post("", response_model=LocationOut)
async def create_location(data: LocationCreate, db: AsyncSession = Depends(get_db)):
    exists = await db.scalar(select(Location).where(Location.code == data.code))
    if exists:
        raise HTTPException(status_code=409, detail="Code already exists")
    loc = Location(code=data.code, name=data.name)
    db.add(loc)
    await db.commit()
    await db.refresh(loc)
    return LocationOut(id=loc.id, code=loc.code, name=loc.name)

@router.get("", response_model=list[LocationOut])
async def list_locations(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Location))
    return [LocationOut(id=l.id, code=l.code, name=l.name) for l in res.scalars().all()]
