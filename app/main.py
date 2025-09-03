from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Здесь мы импортируем СРАЗУ объекты APIRouter из пакета routers.__init__
from app.api.routers import auth, products, locations, inventory, purchase_orders

app = FastAPI(title="Inventory API", version="0.2.0")


@app.get("/healthz")
async def healthz():
    return JSONResponse({"status": "ok"})


# Подключаем роутеры напрямую, БЕЗ .router
app.include_router(auth)
app.include_router(products)
app.include_router(locations)
app.include_router(inventory)
app.include_router(purchase_orders)
