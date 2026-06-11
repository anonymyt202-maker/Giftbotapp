from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from db import get_db
from db.models import Gift
from api.auth import get_webapp_user, get_webapp_admin
import aiofiles
import os
import uuid

router = APIRouter(prefix="/gifts", tags=["gifts"])
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("")
async def list_gifts(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_webapp_user),
):
    q = select(Gift).where(Gift.is_active == True)
    if category:
        q = q.where(Gift.category == category)
    if search:
        q = q.where(Gift.name.ilike(f"%{search}%"))
    result = await db.execute(q.order_by(Gift.id.desc()))
    gifts = result.scalars().all()
    return [_gift_dict(g) for g in gifts]


@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db), user=Depends(get_webapp_user)):
    result = await db.execute(select(Gift.category).distinct())
    return [r[0] for r in result.all() if r[0]]


@router.get("/{gift_id}")
async def get_gift(gift_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_webapp_user)):
    g = await db.get(Gift, gift_id)
    if not g:
        raise HTTPException(404, "Gift topilmadi")
    return _gift_dict(g)


# ── Admin endpoints ──────────────────────────────────────────────

@router.get("/admin/all")
async def admin_list_gifts(db: AsyncSession = Depends(get_db), admin=Depends(get_webapp_admin)):
    result = await db.execute(select(Gift).order_by(Gift.id.desc()))
    return [_gift_dict(g) for g in result.scalars().all()]


@router.post("/admin")
async def admin_create_gift(
    name: str = Form(...),
    price_stars: int = Form(...),
    tg_gift_id: str = Form(...),
    description: Optional[str] = Form(None),
    sticker_url: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    category: str = Form("Umumiy"),
    stock: int = Form(-1),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_webapp_admin),
):
    file_path = None
    if file and file.filename:
        ext = os.path.splitext(file.filename)[1]
        fname = f"{uuid.uuid4()}{ext}"
        fpath = os.path.join(UPLOAD_DIR, fname)
        async with aiofiles.open(fpath, "wb") as f:
            await f.write(await file.read())
        file_path = f"/uploads/{fname}"

    gift = Gift(
        name=name, price_stars=price_stars, tg_gift_id=tg_gift_id,
        description=description, sticker_url=sticker_url, image_url=image_url,
        file_path=file_path, category=category, stock=stock,
    )
    db.add(gift)
    await db.commit()
    await db.refresh(gift)
    return _gift_dict(gift)


@router.put("/admin/{gift_id}")
async def admin_update_gift(
    gift_id: int,
    name: Optional[str] = Form(None),
    price_stars: Optional[int] = Form(None),
    tg_gift_id: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    sticker_url: Optional[str] = Form(None),
    image_url: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    stock: Optional[int] = Form(None),
    is_active: Optional[bool] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_webapp_admin),
):
    g = await db.get(Gift, gift_id)
    if not g:
        raise HTTPException(404, "Gift topilmadi")

    if name is not None:       g.name = name
    if price_stars is not None: g.price_stars = price_stars
    if tg_gift_id is not None: g.tg_gift_id = tg_gift_id
    if description is not None: g.description = description
    if sticker_url is not None: g.sticker_url = sticker_url
    if image_url is not None:   g.image_url = image_url
    if category is not None:    g.category = category
    if stock is not None:       g.stock = stock
    if is_active is not None:   g.is_active = is_active

    if file and file.filename:
        ext = os.path.splitext(file.filename)[1]
        fname = f"{uuid.uuid4()}{ext}"
        fpath = os.path.join(UPLOAD_DIR, fname)
        async with aiofiles.open(fpath, "wb") as f:
            await f.write(await file.read())
        g.file_path = f"/uploads/{fname}"

    await db.commit()
    await db.refresh(g)
    return _gift_dict(g)


@router.delete("/admin/{gift_id}")
async def admin_delete_gift(gift_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_webapp_admin)):
    g = await db.get(Gift, gift_id)
    if not g:
        raise HTTPException(404, "Gift topilmadi")
    await db.delete(g)
    await db.commit()
    return {"ok": True}


def _gift_dict(g: Gift) -> dict:
    from config import settings
    return {
        "id": g.id, "name": g.name, "description": g.description,
        "price_stars": g.price_stars,
        "price_uzs": g.price_stars * settings.STARS_TO_UZS,
        "tg_gift_id": g.tg_gift_id, "sticker_url": g.sticker_url,
        "image_url": g.image_url, "file_path": g.file_path,
        "category": g.category, "stock": g.stock, "is_active": g.is_active,
        "created_at": g.created_at.isoformat() if g.created_at else None,
    }
