from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import InventoryItem, InventoryTxn, InventoryTxnType


async def _ensure_and_lock_item(session: AsyncSession, product_id, location_id) -> InventoryItem:
    # Create row if missing (idempotent), then select FOR UPDATE to avoid races
    stmt = insert(InventoryItem).values(
        product_id=product_id, location_id=location_id, on_hand=0, reserved=0
    ).on_conflict_do_nothing(index_elements=[InventoryItem.product_id, InventoryItem.location_id])
    await session.execute(stmt)

    q = (
        select(InventoryItem)
        .where(
            InventoryItem.product_id == product_id,
            InventoryItem.location_id == location_id,
        )
        .with_for_update()
    )
    res = await session.execute(q)
    item = res.scalars().first()
    if not item:
        raise RuntimeError("Failed to fetch inventory item after upsert")
    return item


async def adjust_stock(
    session: AsyncSession,
    *,
    product_id,
    location_id,
    delta: Decimal,
    reason: str | None
) -> InventoryItem:
    async with session.begin():
        item = await _ensure_and_lock_item(session, product_id, location_id)
        new_on_hand = Decimal(item.on_hand) + Decimal(delta)
        if new_on_hand < Decimal("0"):
            raise ValueError("Adjustment would result in negative on-hand")
        item.on_hand = new_on_hand
        item.version += 1
        txn = InventoryTxn(
            product_id=product_id,
            from_location_id=None,
            to_location_id=location_id if delta > 0 else None,
            qty=abs(delta),
            txn_type=InventoryTxnType.ADJUSTMENT,
            reason=reason,
        )
        session.add(txn)
        await session.flush()
        return item


async def move_stock(
    session: AsyncSession,
    *,
    product_id,
    from_location_id,
    to_location_id,
    qty: Decimal,
    reason: str | None
) -> None:
    if from_location_id == to_location_id:
        raise ValueError("from and to locations must be different")
    async with session.begin():
        src = await _ensure_and_lock_item(session, product_id, from_location_id)
        dst = await _ensure_and_lock_item(session, product_id, to_location_id)
        available = Decimal(src.on_hand) - Decimal(src.reserved)
        if qty > available:
            raise ValueError("Not enough available stock to move")
        src.on_hand = Decimal(src.on_hand) - qty
        dst.on_hand = Decimal(dst.on_hand) + qty
        src.version += 1
        dst.version += 1
        session.add(
            InventoryTxn(
                product_id=product_id,
                from_location_id=from_location_id,
                to_location_id=to_location_id,
                qty=qty,
                txn_type=InventoryTxnType.TRANSFER,
                reason=reason,
            )
        )


async def reserve_stock(
    session: AsyncSession,
    *,
    product_id,
    location_id,
    qty: Decimal,
    reference: str | None
) -> InventoryItem:
    async with session.begin():
        item = await _ensure_and_lock_item(session, product_id, location_id)
        available = Decimal(item.on_hand) - Decimal(item.reserved)
        if qty > available:
            raise ValueError("Not enough available to reserve")
        item.reserved = Decimal(item.reserved) + qty
        item.version += 1
        session.add(
            InventoryTxn(
                product_id=product_id,
                from_location_id=location_id,
                to_location_id=None,
                qty=qty,
                txn_type=InventoryTxnType.RESERVE,
                reference=reference,
            )
        )
        return item


async def release_reservation(
    session: AsyncSession,
    *,
    product_id,
    location_id,
    qty: Decimal,
    reference: str | None
) -> InventoryItem:
    async with session.begin():
        item = await _ensure_and_lock_item(session, product_id, location_id)
        if qty > Decimal(item.reserved):
            raise ValueError("Cannot release more than reserved")
        item.reserved = Decimal(item.reserved) - qty
        item.version += 1
        session.add(
            InventoryTxn(
                product_id=product_id,
                from_location_id=None,
                to_location_id=location_id,
                qty=qty,
                txn_type=InventoryTxnType.RELEASE,
                reference=reference,
            )
        )
        return item


async def ship_reserved(
    session: AsyncSession,
    *,
    product_id,
    location_id,
    qty: Decimal,
    reference: str | None
) -> InventoryItem:
    # Decrease both reserved and on_hand
    async with session.begin():
        item = await _ensure_and_lock_item(session, product_id, location_id)
        if qty > Decimal(item.reserved):
            raise ValueError("Not enough reserved to ship")
        item.reserved = Decimal(item.reserved) - qty
        if qty > Decimal(item.on_hand):
            raise ValueError("Inconsistent state: reserved exceeds on_hand")
        item.on_hand = Decimal(item.on_hand) - qty
        item.version += 1
        session.add(
            InventoryTxn(
                product_id=product_id,
                from_location_id=location_id,
                to_location_id=None,
                qty=qty,
                txn_type=InventoryTxnType.OUT,
                reference=reference,
            )
        )
        return item
