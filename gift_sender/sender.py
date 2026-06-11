"""
gift_sender/sender.py
Telethon orqali Telegram gift yuboruvchi modul.
Bir nechta account session ni boshqaradi.
"""
import asyncio
import logging
from typing import Optional
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.payments import GetPaymentFormRequest, SendStarsFormRequest
from telethon.tl.types import InputInvoiceStarGift, TextWithEntities
from telethon.errors import (
    UserPrivacyRestrictedError, UserNotMutualContactError,
    BalanceTooLowError, FloodWaitError, RPCError
)
from config import settings

logger = logging.getLogger(__name__)


class GiftSendResult:
    def __init__(self, ok: bool, error: Optional[str] = None, error_type: Optional[str] = None):
        self.ok = ok
        self.error = error
        self.error_type = error_type  # user_not_started | balance_low | flood | unknown


async def send_gift(
    session_string: str,
    to_user_id: int,
    tg_gift_id: int,
    anonymous: bool = False,
    message: Optional[str] = None,
) -> GiftSendResult:
    """Telethon session orqali gift yuboradi."""
    client = TelegramClient(StringSession(session_string), settings.API_ID, settings.API_HASH)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return GiftSendResult(ok=False, error="Session expired", error_type="session_expired")

        # Peer olish
        try:
            peer = await client.get_input_entity(to_user_id)
        except Exception as e:
            return GiftSendResult(
                ok=False,
                error=f"Foydalanuvchi topilmadi ({to_user_id}). Bot bilan chat ochilmagan bo'lishi mumkin.",
                error_type="user_not_started",
            )

        # Izoh
        msg_obj = None
        if message and message.strip():
            msg_obj = TextWithEntities(text=message.strip()[:255], entities=[])

        invoice = InputInvoiceStarGift(
            peer=peer,
            gift_id=int(tg_gift_id),
            hide_name=anonymous,
            include_upgrade=False,
            message=msg_obj,
        )

        form = await client(GetPaymentFormRequest(invoice=invoice))
        await client(SendStarsFormRequest(form_id=form.form_id, invoice=invoice))
        logger.info(f"✅ Gift sent: giftId={tg_gift_id} → userId={to_user_id}")
        return GiftSendResult(ok=True)

    except BalanceTooLowError:
        return GiftSendResult(ok=False, error="Hisobda Stars yetarli emas", error_type="balance_low")
    except FloodWaitError as e:
        return GiftSendResult(ok=False, error=f"Flood wait: {e.seconds}s", error_type="flood")
    except (UserPrivacyRestrictedError, UserNotMutualContactError):
        return GiftSendResult(
            ok=False,
            error="Foydalanuvchi privacy sozlamalari tufayli gift qabul qila olmaydi",
            error_type="user_not_started",
        )
    except RPCError as e:
        logger.error(f"RPC error sending gift: {e}")
        return GiftSendResult(ok=False, error=str(e), error_type="rpc_error")
    except Exception as e:
        logger.exception(f"Unexpected error sending gift: {e}")
        return GiftSendResult(ok=False, error=str(e), error_type="unknown")
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def get_session_info(session_string: str) -> dict:
    """Session haqida ma'lumot olish."""
    client = TelegramClient(StringSession(session_string), settings.API_ID, settings.API_HASH)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return {"ok": False, "error": "Session expired"}
        me = await client.get_me()
        return {
            "ok": True,
            "tg_id": me.id,
            "username": me.username,
            "first_name": me.first_name,
            "phone": me.phone,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


# Login flow (phone → code → password)
_login_clients: dict[str, TelegramClient] = {}
_login_data: dict[str, dict] = {}


async def login_start(phone: str) -> dict:
    """Login boshlash: telefon raqam yuborish."""
    client = TelegramClient(StringSession(), settings.API_ID, settings.API_HASH)
    await client.connect()
    try:
        result = await client.send_code_request(phone)
        _login_clients[phone] = client
        _login_data[phone] = {"phone_code_hash": result.phone_code_hash}
        return {"ok": True, "phone_code_hash": result.phone_code_hash}
    except Exception as e:
        await client.disconnect()
        return {"ok": False, "error": str(e)}


async def login_verify_code(phone: str, code: str) -> dict:
    """Kodni tekshirish."""
    client = _login_clients.get(phone)
    data = _login_data.get(phone, {})
    if not client:
        return {"ok": False, "error": "Login sessiyasi topilmadi"}
    try:
        await client.sign_in(phone=phone, code=code, phone_code_hash=data["phone_code_hash"])
        session_string = client.session.save()
        me = await client.get_me()
        await client.disconnect()
        _login_clients.pop(phone, None)
        _login_data.pop(phone, None)
        return {"ok": True, "session": session_string, "username": me.username,
                "first_name": me.first_name, "tg_id": me.id}
    except Exception as e:
        if "PASSWORD_NEEDED" in str(e):
            return {"ok": False, "need_2fa": True}
        await client.disconnect()
        _login_clients.pop(phone, None)
        return {"ok": False, "error": str(e)}


async def login_verify_2fa(phone: str, password: str) -> dict:
    """2FA parolini tekshirish."""
    client = _login_clients.get(phone)
    if not client:
        return {"ok": False, "error": "Login sessiyasi topilmadi"}
    try:
        await client.sign_in(password=password)
        session_string = client.session.save()
        me = await client.get_me()
        await client.disconnect()
        _login_clients.pop(phone, None)
        _login_data.pop(phone, None)
        return {"ok": True, "session": session_string, "username": me.username,
                "first_name": me.first_name, "tg_id": me.id}
    except Exception as e:
        await client.disconnect()
        _login_clients.pop(phone, None)
        return {"ok": False, "error": str(e)}
