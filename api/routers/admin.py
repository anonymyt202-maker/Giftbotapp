from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from db import get_db
from db.models import User, Gift, Order, Referral, PromoCode
from api.auth import get_webapp_admin

router = APIRouter(prefix="/admin", tags=["admin"])

# In-memory config (persists while server runs)
_config = {}


@router.get("/dashboard")
async def dashboard(db: AsyncSession = Depends(get_db), admin=Depends(get_webapp_admin)):
    from config import settings

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar()
    total_gifts = (await db.execute(select(func.count()).select_from(Gift))).scalar()
    total_orders = (await db.execute(select(func.count()).select_from(Order))).scalar()
    success_orders = (await db.execute(
        select(func.count()).select_from(Order).where(Order.status == "success")
    )).scalar()
    pending_orders = (await db.execute(
        select(func.count()).select_from(Order).where(Order.status == "pending")
    )).scalar()
    failed_orders = (await db.execute(
        select(func.count()).select_from(Order).where(Order.status == "failed")
    )).scalar()
    total_stars = (await db.execute(select(func.sum(User.stars)).select_from(User))).scalar() or 0
    total_uzs = (await db.execute(select(func.sum(User.uzs)).select_from(User))).scalar() or 0
    revenue_stars = (await db.execute(
        select(func.sum(Order.amount_stars)).select_from(Order).where(Order.status == "success")
    )).scalar() or 0

    from db.models import TgAccount
    active_accounts = (await db.execute(
        select(func.count()).select_from(TgAccount).where(TgAccount.is_active == True)
    )).scalar()

    return {
        "total_users": total_users,
        "total_gifts": total_gifts,
        "total_orders": total_orders,
        "success_orders": success_orders,
        "pending_orders": pending_orders,
        "failed_orders": failed_orders,
        "total_stars_in_wallets": round(total_stars, 2),
        "total_uzs_in_wallets": round(total_uzs, 2),
        "revenue_stars": round(revenue_stars, 2),
        "active_accounts": active_accounts,
        "stars_to_uzs": settings.STARS_TO_UZS,
        "referral_reward": _config.get("referral_reward", settings.REFERRAL_REWARD),
    }


class PromoCreate(BaseModel):
    code: str
    discount_type: str = "percent"
    discount_value: float
    max_uses: int = 100
    expires_at: Optional[str] = None


@router.post("/promo")
async def create_promo(body: PromoCreate, db: AsyncSession = Depends(get_db), admin=Depends(get_webapp_admin)):
    expires = None
    if body.expires_at:
        try:
            expires = datetime.fromisoformat(body.expires_at)
        except Exception:
            pass
    promo = PromoCode(
        code=body.code.upper().strip(),
        discount_type=body.discount_type,
        discount_value=body.discount_value,
        max_uses=body.max_uses,
        expires_at=expires,
    )
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return _promo_dict(promo)


@router.get("/promo")
async def list_promos(db: AsyncSession = Depends(get_db), admin=Depends(get_webapp_admin)):
    res = await db.execute(select(PromoCode).order_by(PromoCode.id.desc()))
    return [_promo_dict(p) for p in res.scalars().all()]


@router.delete("/promo/{promo_id}")
async def delete_promo(promo_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_webapp_admin)):
    p = await db.get(PromoCode, promo_id)
    if not p:
        raise HTTPException(404, "Topilmadi")
    await db.delete(p)
    await db.commit()
    return {"ok": True}


class ReferralConfig(BaseModel):
    reward: int


@router.post("/config/referral")
async def set_referral_reward(body: ReferralConfig, admin=Depends(get_webapp_admin)):
    _config["referral_reward"] = body.reward
    return {"ok": True, "referral_reward": body.reward}


@router.get("/referrals")
async def referral_stats(db: AsyncSession = Depends(get_db), admin=Depends(get_webapp_admin)):
    total = (await db.execute(select(func.count()).select_from(Referral))).scalar()
    rewarded = (await db.execute(
        select(func.count()).select_from(Referral).where(Referral.rewarded == True)
    )).scalar()
    total_bonus = (await db.execute(select(func.sum(Referral.reward_stars)).select_from(Referral))).scalar() or 0

    top = await db.execute(
        select(User.username, User.telegram_id,
               func.count(Referral.id).label("cnt"))
        .join(Referral, Referral.inviter_id == User.id)
        .group_by(User.id).order_by(func.count(Referral.id).desc()).limit(10)
    )
    top_inviters = [{"username": r[0], "telegram_id": r[1], "count": r[2]} for r in top.all()]

    return {
        "total_referrals": total,
        "rewarded": rewarded,
        "total_bonus_stars": round(total_bonus, 2),
        "top_inviters": top_inviters,
    }


def _promo_dict(p: PromoCode) -> dict:
    return {
        "id": p.id, "code": p.code,
        "discount_type": p.discount_type, "discount_value": p.discount_value,
        "max_uses": p.max_uses, "used_count": p.used_count,
        "is_active": p.is_active,
        "expires_at": p.expires_at.isoformat() if p.expires_at else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }
