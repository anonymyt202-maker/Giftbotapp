"""
Telegram WebApp initData tekshirish (HMAC-SHA256)
"""
import hashlib
import hmac
import json
import time
from urllib.parse import unquote, parse_qsl
from fastapi import HTTPException, Header
from config import settings


def verify_webapp_data(init_data: str) -> dict:
    """
    Telegram WebApp initData ni tekshiradi.
    Muvaffaqiyatli bo'lsa user dict qaytaradi.
    """
    try:
        parsed = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = parsed.pop("hash", "")
        auth_date = int(parsed.get("auth_date", 0))

        # 24 soatdan eski bo'lsa rad etish
        if time.time() - auth_date > 86400:
            raise HTTPException(status_code=401, detail="initData expired")

        # data-check-string yaratish
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(parsed.items())
        )

        # Secret key
        secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
        expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_hash, received_hash):
            raise HTTPException(status_code=401, detail="Invalid initData signature")

        user_data = json.loads(unquote(parsed.get("user", "{}")))
        return user_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"initData parse error: {e}")


def verify_admin(user_data: dict) -> bool:
    return user_data.get("id") in settings.admin_ids


async def get_webapp_user(x_init_data: str = Header(None)) -> dict:
    """FastAPI dependency — WebApp foydalanuvchisini olish."""
    if not x_init_data:
        raise HTTPException(status_code=401, detail="X-Init-Data header missing")
    return verify_webapp_data(x_init_data)


async def get_webapp_admin(x_init_data: str = Header(None)) -> dict:
    """FastAPI dependency — faqat adminlar uchun."""
    if not x_init_data:
        raise HTTPException(status_code=401, detail="X-Init-Data header missing")
    user = verify_webapp_data(x_init_data)
    if not verify_admin(user):
        raise HTTPException(status_code=403, detail="Admin only")
    return user
