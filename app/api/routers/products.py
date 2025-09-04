from __future__ import annotations

import csv
import io
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
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


# ── CSV IMPORT ───────────────────────────────────────────────────────────────
@router.post("/import-csv", dependencies=[Depends(require_roles("operator", "admin"))])
async def import_products_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    encoding: str | None = Query(
        None,
        description="Принудительная кодировка: utf-8, utf-8-sig, cp1251, utf-16 и т.п."
    ),
):
    """Импорт товаров из CSV. Поддерживаются кодировки UTF-8/UTF-16/CP1251 и др.,
    а также разделители ',', ';', '	', '|'. Заголовки: sku/name/unit/description
    (или русские аналоги: Артикул/Наименование/Ед/Описание).
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Upload a .csv file")

    content = await file.read()

    def _decode_csv_bytes(b: bytes) -> str:
        # Если пользователь явно указал encoding — используем его
        if encoding:
            try:
                return b.decode(encoding)
            except UnicodeDecodeError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Не удалось декодировать файл как {encoding}"
                )
        # Автоматические попытки — популярные кодировки Windows/Excel
        for enc in (
        "utf-8-sig", "utf-8", "utf-16", "utf-16le", "utf-16be", "cp1251", "windows-1251",
        "latin-1"):
            try:
                return b.decode(enc)
            except UnicodeDecodeError:
                continue
        # Опционально: если установлен charset-normalizer — попробуем им
        try:
            from charset_normalizer import from_bytes  # type: ignore
            res = from_bytes(b).best()
            if res:
                return str(res)
        except Exception:
            pass
        raise HTTPException(
            status_code=400,
            detail="Не удалось распознать кодировку. Сохраните файл как 'CSV UTF-8' и повторите."
        )

    text = _decode_csv_bytes(content)

    # Определяем разделитель (запятая/точка с запятой/таб/|)
    try:
        dialect = csv.Sniffer().sniff(text[:10000], delimiters=",;|\t")
    except Exception:
        dialect = csv.excel

    reader = csv.DictReader(io.StringIO(text), dialect=dialect)

    def pick(row: dict, *keys: str) -> str:
        for k in keys:
            v = row.get(k)
            if v is not None and str(v).strip():
                return str(v).strip()
        return ""

    rows: list[dict] = []
    for row in reader:
        # Поддерживаем и англ., и русские заголовки
        sku = pick(row, "sku", "SKU", "артикул", "Артикул", "код", "Код", "Код товара")
        name = pick(row, "name", "Name", "наименование", "Наименование", "Название", "Товар")
        if not sku or not name:
            continue
        unit = pick(row, "unit", "Unit", "ед", "Ед", "единица", "ед. изм.", "шт") or "pcs"
        description = pick(row, "description", "Description", "описание", "Описание") or None
        rows.append(
            {"id": uuid.uuid4(), "sku": sku, "name": name, "unit": unit, "description": description}
        )

    if not rows:
        return {"status": "ok", "inserted": 0}

    stmt = insert(Product).values(rows).on_conflict_do_nothing(index_elements=[Product.sku])
    await db.execute(stmt)
    await db.commit()
    return {"status": "ok", "inserted": len(rows)}


# ── CSV EXPORT ───────────────────────────────────────────────────────────────
@router.get("/export-csv", dependencies=[Depends(require_roles("viewer", "operator", "admin"))])
async def export_products_csv(
    db: AsyncSession = Depends(get_db),
    delimiter: str = Query(
        ",",
        min_length=1,
        max_length=1,
        description="Разделитель: ',' по умолчанию; для Excel на RU часто ';'",
    ),
    encoding: str = Query(
        "utf-8-sig",
        description="Кодировка вывода: 'utf-8-sig' дружелюбна к Excel на Windows; можно 'utf-8' или 'cp1251'",
    ),
    filename: str = Query("products.csv", description="Имя файла для скачивания"),
):
    res = await db.execute(select(Product).order_by(Product.sku))
    products = list(res.scalars().all())

    sio = io.StringIO()
    writer = csv.writer(sio, delimiter=delimiter)
    writer.writerow(["sku", "name", "unit", "description"])  # шапка
    for p in products:
        # Убираем переводы строк из description, чтобы не ломать CSV
        cleaned_desc = (p.description or "").replace("\r", " ").replace("\n", " ")
        writer.writerow([p.sku or "", p.name or "", p.unit or "", cleaned_desc])

    data_bytes = sio.getvalue().encode(encoding, errors="strict")
    headers = {
        "Content-Disposition": f"attachment; filename=\"{filename}\"",
        "Cache-Control": "no-store",
    }
    return Response(content=data_bytes, media_type=f"text/csv; charset={encoding}", headers=headers)
