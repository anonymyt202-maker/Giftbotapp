from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from db import get_db
from db.models import User, Order, Referral, PromoCode
from api.auth import get_webapp_user, get_webapp_admin
from config import settings
import secrets, string

router = APIRouter(prefix="/users", tags=["users"])


def _gen_code():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


@router.get("/me")
async def get_me(db: AsyncSession = Depends(get_db), user=Depends(get_webapp_user)):
    tg_id = user.get("id")
    res = await db.execute(select(User).where(User.telegram_id == tg_id))
    db_user = res.scalar_one_or_none()
    if not db_user:
        # Yangi user yaratish
        db_user = User(
            telegram_id=tg_id,
            username=user.get("username"),
            first_name=user.get("first_name"),
            referral_code=_gen_code(),
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

    bi = await _get_bot_username()
    ref_link = f"https://t.me/{bi}?start=ref_{db_user.referral_code}"

    ref_count = await db.execute(
        select(func.count()).select_from(Referral).where(Referral.inviter_id == db_user.id)
    )

    return {
        "telegram_id": db_user.telegram_id,
        "username": db_user.username,
        "first_name": db_user.first_name,
        "stars": db_user.stars,
        "uzs": db_user.uzs,
        "referral_code": db_user.referral_code,
        "referral_link": ref_link,
        "referral_count": ref_count.scalar(),
        "purchases_count": db_user.purchases_count,
    }


@router.get("/admin/all")
async def admin_list_users(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_webapp_admin),
):
    q = select(User).order_by(User.id.desc()).limit(200)
    if search:
        q = q.where(
            (User.username.ilike(f"%{search}%")) |
            (User.telegram_id == int(search) if search.isdigit() else User.telegram_id == 0)
        )
    res = await db.execute(q)
    users = res.scalars().all()
    return [
        {"id": u.id, "telegram_id": u.telegram_id, "username": u.username,
         "first_name": u.first_name, "stars": u.stars, "uzs": u.uzs,
         "purchases_count": u.purchases_count, "is_banned": u.is_banned,
         "created_at": u.created_at.isoformat() if u.created_at else None}
        for u in users
    ]


class BalanceUpdate(BaseModel):
    telegram_id: int
    stars: Optional[float] = None
    uzs: Optional[float] = None


@router.post("/admin/balance")
async def admin_update_balance(
    body: BalanceUpdate,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_webapp_admin),
):
    res = await db.execute(select(User).where(User.telegram_id == body.telegram_id))
    u = res.scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User topilmadi")
    if body.stars is not None:
        u.stars = max(0, u.stars + body.stars)
    if body.uzs is not None:
        u.uzs = max(0, u.uzs + body.uzs)
    await db.commit()
    return {"ok": True, "stars": u.stars, "uzs": u.uzs}


async def _get_bot_username() -> str:
    try:
        from aiogram import Bot
        bot = Bot(token=settings.BOT_TOKEN)
        me = await bot.get_me()
        await bot.session.close()
        return me.username or "bot"
    except Exception:
        return "bot"
