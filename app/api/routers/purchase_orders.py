from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.models import Supplier, Product, PurchaseOrder, PurchaseOrderLine, POStatus
from app.schemas.purchase import (
    SupplierCreate,
    SupplierOut,
    PurchaseOrderCreate,
    PurchaseOrderOut,
    PurchaseOrderLineCreate,
    PurchaseReceiveRequest,
)
from app.services.inventory import adjust_stock

router = APIRouter(prefix="/purchase", tags=["purchase"])

@router.post("/suppliers", response_model=SupplierOut)
async def create_supplier(data: SupplierCreate, db: AsyncSession = Depends(get_db)):
    sup = Supplier(name=data.name, email=data.email, phone=data.phone)
    db.add(sup)
    await db.commit()
    await db.refresh(sup)
    return SupplierOut(id=sup.id, name=sup.name)

@router.post("/orders", response_model=PurchaseOrderOut)
async def create_po(data: PurchaseOrderCreate, db: AsyncSession = Depends(get_db)):
    supplier = await db.get(Supplier, data.supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    po = PurchaseOrder(supplier_id=data.supplier_id, status=POStatus.OPEN)
    db.add(po)
    await db.commit()
    await db.refresh(po)
    return PurchaseOrderOut(id=po.id, supplier_id=po.supplier_id, status=po.status.value)

@router.post("/orders/{po_id}/lines")
async def add_po_line(po_id: str, data: PurchaseOrderLineCreate, db: AsyncSession = Depends(get_db)):
    po = await db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    if po.status not in (POStatus.DRAFT, POStatus.OPEN):
        raise HTTPException(status_code=400, detail="PO not editable")
    prod = await db.get(Product, data.product_id)
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")
    line = PurchaseOrderLine(purchase_order_id=po.id, product_id=prod.id, qty_ordered=data.qty_ordered, unit_cost=data.unit_cost)
    db.add(line)
    await db.commit()
    return {"status": "ok"}

@router.post("/orders/{po_id}/receive")
async def receive_po(po_id: str, data: PurchaseReceiveRequest, db: AsyncSession = Depends(get_db)):
    po = await db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="PO not found")
    if po.status in (POStatus.CANCELLED, POStatus.RECEIVED):
        raise HTTPException(status_code=400, detail="PO closed")

    # Receive each line into specified locations
    for line_in in data.lines:
        line = await db.get(PurchaseOrderLine, line_in.line_id)
        if not line or line.purchase_order_id != po.id:
            raise HTTPException(status_code=400, detail=f"Line {line_in.line_id} invalid")
        remaining = line.qty_ordered - line.qty_received
        if line_in.qty > remaining:
            raise HTTPException(status_code=400, detail="Receive qty exceeds remaining")
        line.qty_received += line_in.qty
        # Adjust stock IN at the target location
        await adjust_stock(db, product_id=line.product_id, location_id=line_in.location_id, delta=line_in.qty, reason=f"PO {po.id}")

    # If all lines fully received -> mark PO RECEIVED
    res = await db.execute(select(PurchaseOrderLine).where(PurchaseOrderLine.purchase_order_id == po.id))
    lines = res.scalars().all()
    if all(l.qty_received >= l.qty_ordered for l in lines):
        po.status = POStatus.RECEIVED
        await db.commit()
    return {"status": "ok"}
