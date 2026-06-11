from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from pydantic import BaseModel
from db import get_db
from db.models import TgAccount
from api.auth import get_webapp_admin
from gift_sender.sender import login_start, login_verify_code, login_verify_2fa, get_session_info
from datetime import datetime
import telethon

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("")
async def list_accounts(db: AsyncSession = Depends(get_db), admin=Depends(get_webapp_admin)):
    res = await db.execute(select(TgAccount).order_by(TgAccount.id.desc()))
    return [_acc_dict(a) for a in res.scalars().all()]


@router.post("/login/start")
async def start_login(phone: str = Form(...), db: AsyncSession = Depends(get_db), admin=Depends(get_webapp_admin)):
    result = await login_start(phone)
    return result


@router.post("/login/code")
async def verify_code(
    phone: str = Form(...),
    code: str = Form(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_webapp_admin),
):
    result = await login_verify_code(phone, code)
    if result.get("ok"):
        await _save_account(db, phone, result)
    return result


@router.post("/login/2fa")
async def verify_2fa(
    phone: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_webapp_admin),
):
    result = await login_verify_2fa(phone, password)
    if result.get("ok"):
        await _save_account(db, phone, result)
    return result


@router.post("/upload-session")
async def upload_session(
    phone: str = Form(...),
    session_file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_webapp_admin),
):
    """Session faylni yuklash (.session fayl yoki StringSession string)."""
    content = await session_file.read()
    session_string = content.decode("utf-8").strip()

    info = await get_session_info(session_string)
    if not info.get("ok"):
        raise HTTPException(400, f"Session yaroqsiz: {info.get('error')}")

    result = {
        "session": session_string,
        "username": info["username"],
        "first_name": info["first_name"],
        "tg_id": info["tg_id"],
    }
    await _save_account(db, phone, result)
    return {"ok": True, **info}


@router.patch("/{account_id}/toggle")
async def toggle_account(account_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_webapp_admin)):
    acc = await db.get(TgAccount, account_id)
    if not acc:
        raise HTTPException(404, "Account topilmadi")
    acc.is_active = not acc.is_active
    await db.commit()
    return {"ok": True, "is_active": acc.is_active}


@router.delete("/{account_id}")
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db), admin=Depends(get_webapp_admin)):
    acc = await db.get(TgAccount, account_id)
    if not acc:
        raise HTTPException(404, "Account topilmadi")
    await db.delete(acc)
    await db.commit()
    return {"ok": True}


async def _save_account(db: AsyncSession, phone: str, data: dict):
    res = await db.execute(select(TgAccount).where(TgAccount.phone == phone))
    acc = res.scalar_one_or_none()
    if acc:
        acc.session_string = data["session"]
        acc.username = data.get("username")
        acc.first_name = data.get("first_name")
        acc.tg_id = data.get("tg_id")
        acc.is_active = True
    else:
        acc = TgAccount(
            phone=phone, session_string=data["session"],
            username=data.get("username"), first_name=data.get("first_name"),
            tg_id=data.get("tg_id"), is_active=True,
        )
        db.add(acc)
    await db.commit()


def _acc_dict(a: TgAccount) -> dict:
    return {
        "id": a.id, "phone": a.phone, "username": a.username,
        "first_name": a.first_name, "tg_id": a.tg_id,
        "is_active": a.is_active, "stars_balance": a.stars_balance,
        "gifts_sent": a.gifts_sent, "note": a.note,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "last_used": a.last_used.isoformat() if a.last_used else None,
    }
