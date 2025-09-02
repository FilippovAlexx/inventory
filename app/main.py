from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.routers import inventory, locations, products, purchase

app = FastAPI(title="Inventory API", version="0.1.0")


@app.get("/healthz")
async def healthz():
    return JSONResponse({"status": "ok"})


app.include_router(products)
app.include_router(locations)
app.include_router(inventory)
app.include_router(purchase)
