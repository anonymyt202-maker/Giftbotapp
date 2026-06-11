from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from db import get_db
from db.models import Order, Gift, User, TgAccount, PromoCode
from api.auth import get_webapp_user, get_webapp_admin
from gift_sender.sender import send_gift
from datetime import datetime

router = APIRouter(prefix="/orders", tags=["orders"])


class OrderCreate(BaseModel):
    gift_id: int
    target_telegram_id: Optional[int] = None
    target_username: Optional[str] = None
    pay_with: str = "stars"          # stars | uzs
    anonymous: bool = False
    comment: Optional[str] = None
    promo_code: Optional[str] = None


@router.post("")
async def create_order(body: OrderCreate, db: AsyncSession = Depends(get_db), user=Depends(get_webapp_user)):
    tg_id = user.get("id")

    # User topish
    res = await db.execute(select(User).where(User.telegram_id == tg_id))
    db_user = res.scalar_one_or_none()
    if not db_user:
        raise HTTPException(404, "User topilmadi")

    # Gift topish
    gift = await db.get(Gift, body.gift_id)
    if not gift or not gift.is_active:
        raise HTTPException(404, "Gift topilmadi yoki faol emas")

    from config import settings
    price = float(gift.price_stars)

    # Promo kod
    discount = 0.0
    if body.promo_code:
        res2 = await db.execute(select(PromoCode).where(
            PromoCode.code == body.promo_code.upper(),
            PromoCode.is_active == True,
        ))
        promo = res2.scalar_one_or_none()
        if promo and (not promo.expires_at or promo.expires_at > datetime.utcnow()) and promo.used_count < promo.max_uses:
            if promo.discount_type == "percent":
                discount = price * promo.discount_value / 100
            else:
                discount = promo.discount_value
            promo.used_count += 1
    price = max(1, price - discount)

    # Balans tekshirish
    if body.pay_with == "stars":
        if db_user.stars < price:
            raise HTTPException(400, f"Stars yetarli emas. Sizda: {db_user.stars}, kerak: {price}")
        db_user.stars -= price
    else:
        uzs_price = price * settings.STARS_TO_UZS
        if db_user.uzs < uzs_price:
            raise HTTPException(400, f"UZS yetarli emas. Sizda: {db_user.uzs}, kerak: {uzs_price}")
        db_user.uzs -= uzs_price

    order = Order(
        user_id=db_user.id, gift_id=gift.id,
        target_telegram_id=body.target_telegram_id,
        target_username=body.target_username,
        amount_stars=price, amount_uzs=price * settings.STARS_TO_UZS if body.pay_with == "uzs" else 0,
        pay_with=body.pay_with, anonymous=body.anonymous,
        comment=body.comment, promo_code=body.promo_code, status="pending",
    )
    db.add(order)
    await db.flush()

    # Gift yuborish
    res3 = await db.execute(select(TgAccount).where(TgAccount.is_active == True))
    accounts = res3.scalars().all()
    if not accounts:
        order.status = "failed"
        order.error_msg = "Faol Telegram account topilmadi"
        await db.commit()
        raise HTTPException(503, "Faol Telegram account topilmadi. Admin bilan bog'laning.")

    account = accounts[0]
    target_id = body.target_telegram_id or tg_id
    result = await send_gift(
        session_string=account.session_string,
        to_user_id=target_id,
        tg_gift_id=int(gift.tg_gift_id),
        anonymous=body.anonymous,
        message=body.comment,
    )

    if result.ok:
        order.status = "success"
        account.gifts_sent += 1
        account.last_used = datetime.utcnow()
        if gift.stock > 0:
            gift.stock -= 1
        db_user.purchases_count += 1
        await db.commit()
        return {"ok": True, "order_id": order.id, "status": "success"}
    else:
        order.status = "failed"
        order.error_msg = result.error
        # Pulni qaytarish
        if body.pay_with == "stars":
            db_user.stars += price
        else:
            db_user.uzs += price * settings.STARS_TO_UZS
        await db.commit()
        error_msg = {
            "user_not_started": "Foydalanuvchi bot bilan chat ochmagan. Avval /start bosishlarini so'rang.",
            "balance_low": "Ulangan hisobda Stars yetarli emas. Admin bilan bog'laning.",
            "flood": "Flood wait. Bir oz kuting.",
        }.get(result.error_type, result.error)
        raise HTTPException(400, error_msg)


@router.get("/my")
async def my_orders(db: AsyncSession = Depends(get_db), user=Depends(get_webapp_user)):
    tg_id = user.get("id")
    res = await db.execute(select(User).where(User.telegram_id == tg_id))
    db_user = res.scalar_one_or_none()
    if not db_user:
        return []
    res2 = await db.execute(
        select(Order).where(Order.user_id == db_user.id).order_by(Order.id.desc()).limit(50)
    )
    orders = res2.scalars().all()
    result = []
    for o in orders:
        gift = await db.get(Gift, o.gift_id)
        result.append({
            "id": o.id, "gift_name": gift.name if gift else "?",
            "amount_stars": o.amount_stars, "status": o.status,
            "anonymous": o.anonymous, "created_at": o.created_at.isoformat(),
        })
    return result


# ── Admin ────────────────────────────────────────────────────────

@router.get("/admin/all")
async def admin_orders(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_webapp_admin),
):
    q = select(Order).order_by(Order.id.desc()).limit(200)
    if status:
        q = q.where(Order.status == status)
    res = await db.execute(q)
    orders = res.scalars().all()
    result = []
    for o in orders:
        u = await db.get(User, o.user_id)
        g = await db.get(Gift, o.gift_id)
        result.append({
            "id": o.id,
            "user": u.username or str(u.telegram_id) if u else "?",
            "gift": g.name if g else "?",
            "target": o.target_username or str(o.target_telegram_id),
            "amount_stars": o.amount_stars,
            "pay_with": o.pay_with,
            "status": o.status,
            "error": o.error_msg,
            "anonymous": o.anonymous,
            "created_at": o.created_at.isoformat(),
        })
    return result
