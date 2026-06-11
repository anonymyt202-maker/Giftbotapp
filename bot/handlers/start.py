from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import User
from db.session import AsyncSessionLocal
from bot.keyboards.main import main_menu_kb, back_kb, games_kb
from config import settings
import secrets, string

router = Router()


def _gen_code():
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


async def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None) -> User:
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user = res.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=telegram_id, username=username,
                first_name=first_name, referral_code=_gen_code(),
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            return user, True
        user.username = username or user.username
        user.first_name = first_name or user.first_name
        await db.commit()
        return user, False


@router.message(CommandStart())
async def cmd_start(msg: Message):
    payload = msg.text.split(" ", 1)[1] if " " in msg.text else ""
    user, is_new = await get_or_create_user(
        msg.from_user.id, msg.from_user.username, msg.from_user.first_name
    )

    # Referral
    if payload.startswith("ref_") and is_new:
        ref_code = payload[4:]
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(User).where(User.referral_code == ref_code))
            inviter = res.scalar_one_or_none()
            if inviter and inviter.telegram_id != msg.from_user.id:
                res2 = await db.execute(select(User).where(User.telegram_id == msg.from_user.id))
                new_user = res2.scalar_one_or_none()
                if new_user and not new_user.referred_by:
                    new_user.referred_by = inviter.telegram_id
                    # Mukofot berish
                    reward = settings.REFERRAL_REWARD
                    inviter.stars += reward
                    inviter.referral_rewarded = True
                    await db.commit()
                    try:
                        await msg.bot.send_message(
                            inviter.telegram_id,
                            f"🎉 Yangi referal! <b>+{reward} ⭐</b> ishladingiz!",
                            parse_mode="HTML",
                        )
                    except Exception:
                        pass

    if is_new:
        try:
            for admin_id in settings.admin_ids:
                await msg.bot.send_message(
                    admin_id,
                    f"👤 <b>Yangi foydalanuvchi!</b>\n\n"
                    f"🆔 <code>{msg.from_user.id}</code>\n"
                    f"📛 @{msg.from_user.username or '—'}\n"
                    f"Ism: {msg.from_user.first_name or '—'}",
                    parse_mode="HTML",
                )
        except Exception:
            pass

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.telegram_id == msg.from_user.id))
        u = res.scalar_one_or_none()
        stars = u.stars if u else 0
        uzs = u.uzs if u else 0

    await msg.answer(
        f"🎁 <b>GiftBot</b> ga xush kelibsiz!\n\n"
        f"💼 <b>Hisobingiz:</b>\n"
        f"   ⭐ Stars: <b>{stars:.0f}</b>\n"
        f"   💵 UZS: <b>{uzs:,.0f} UZS</b>",
        parse_mode="HTML",
        reply_markup=main_menu_kb(settings.API_BASE_URL),
    )


@router.message(Command("admin"))
async def cmd_admin(msg: Message):
    if msg.from_user.id not in settings.admin_ids:
        return
    from bot.keyboards.main import admin_panel_kb
    await msg.answer(
        "🔧 <b>Admin Panel</b>\n\nQuyidagi tugmani bosing:",
        parse_mode="HTML",
        reply_markup=admin_panel_kb(settings.API_BASE_URL),
    )


@router.callback_query(F.data == "main")
async def cb_main(cb: CallbackQuery):
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.telegram_id == cb.from_user.id))
        u = res.scalar_one_or_none()
        stars = u.stars if u else 0
        uzs = u.uzs if u else 0
    await cb.message.edit_text(
        f"🎁 <b>GiftBot</b>\n\n"
        f"⭐ Stars: <b>{stars:.0f}</b>\n"
        f"💵 UZS: <b>{uzs:,.0f} UZS</b>",
        parse_mode="HTML",
        reply_markup=main_menu_kb(settings.API_BASE_URL),
    )
    await cb.answer()


@router.callback_query(F.data == "balance")
async def cb_balance(cb: CallbackQuery):
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.telegram_id == cb.from_user.id))
        u = res.scalar_one_or_none()
        stars = u.stars if u else 0
        uzs = u.uzs if u else 0
        purchases = u.purchases_count if u else 0
        ref_code = u.referral_code if u else "—"

    bot_info = await cb.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{ref_code}"

    await cb.message.edit_text(
        f"👤 <b>Hisobim</b>\n\n"
        f"🆔 ID: <code>{cb.from_user.id}</code>\n"
        f"⭐ Stars: <b>{stars:.0f}</b>\n"
        f"💵 UZS: <b>{uzs:,.0f} UZS</b>\n"
        f"🛍 Xaridlar: <b>{purchases}</b>\n\n"
        f"🔗 Referal link:\n{ref_link}",
        parse_mode="HTML",
        reply_markup=back_kb("main"),
    )
    await cb.answer()


@router.callback_query(F.data == "referral")
async def cb_referral(cb: CallbackQuery):
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.telegram_id == cb.from_user.id))
        u = res.scalar_one_or_none()
        stars = u.stars if u else 0
        ref_code = u.referral_code if u else "—"

    bot_info = await cb.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{ref_code}"

    await cb.message.edit_text(
        f"👥 <b>Referal tizim</b>\n\n"
        f"⭐ Stars: {stars:.0f}\n"
        f"🎁 Har do'st uchun: {settings.REFERRAL_REWARD} ⭐\n\n"
        f"🔗 Sizning havola:\n{ref_link}",
        parse_mode="HTML",
        reply_markup=back_kb("main"),
    )
    await cb.answer()


@router.callback_query(F.data == "games")
async def cb_games(cb: CallbackQuery):
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.telegram_id == cb.from_user.id))
        u = res.scalar_one_or_none()
        stars = u.stars if u else 0
    await cb.message.edit_text(
        f"🎮 <b>O'yinlar</b>\n\n💎 Balans: <b>{stars:.0f} ⭐</b>\n\nO'yin tanlang:",
        parse_mode="HTML",
        reply_markup=games_kb(),
    )
    await cb.answer()
