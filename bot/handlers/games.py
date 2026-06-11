from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from db.session import AsyncSessionLocal
from db.models import User
from bot.keyboards.main import games_kb, bet_kb, back_kb
from datetime import datetime, timedelta
import asyncio, random

router = Router()

DAILY_MS   = timedelta(hours=24)
SLOT_JP    = 64
SLOT_LEM   = 1
THREE_SAME = {1, 22, 43, 64}

GAME_INFO = {
    "dice"      : {"name": "🎲 Zar",       "emoji": "🎲"},
    "football"  : {"name": "⚽ Futbol",    "emoji": "⚽"},
    "basketball": {"name": "🏀 Basketbol", "emoji": "🏀"},
    "darts"     : {"name": "🎯 Darts",     "emoji": "🎯"},
    "slots"     : {"name": "🎰 Slotlar",   "emoji": "🎰"},
    "coin"      : {"name": "🪙 Coin Flip", "emoji": "🎲"},
}


def calc_result(game: str, value: int, bet: float):
    if game == "dice":
        if value == 6: return bet * 2,   f"🎉 6 tushdi! 2×!"
        if value == 5: return bet * 1.5, f"🎊 5 tushdi! 1.5×!"
        if value == 4: return bet,       f"🙂 4 tushdi. Qaytarildi."
        if value == 3: return bet * 0.5, f"😕 3 tushdi. Yarmi."
        return 0, f"😢 {value} tushdi. Yutqazdingiz!"
    if game == "football":
        return (bet * 1.44, "⚽ GOL! 1.44×!") if value >= 3 else (0, "❌ Xato!")
    if game == "basketball":
        return (bet * 1.5, "🏀 HIT! 1.5×!") if value >= 4 else (0, "❌ Xato!")
    if game == "darts":
        if value == 6: return bet * 2,   "🎯 MARKAZ! 2×!"
        if value >= 4: return bet * 1.5, "🎯 Yaqin! 1.5×!"
        return 0, "❌ Xato!"
    if game == "slots":
        if value == SLOT_JP:        return bet * 5,  "🎰 777 JACKPOT! 5×! 🎉"
        if value == SLOT_LEM:       return bet * 2,  "🍋🍋🍋 2×!"
        if value in THREE_SAME:     return bet * 2,  "🎰 3 bir xil! 2×!"
        return 0, "❌ Yutqazdingiz."
    if game == "coin":
        won = random.random() > 0.5
        return (bet * 1.9, "🪙 Yutdingiz! 1.9×!") if won else (0, "🪙 Yutqazdingiz!")
    return 0, "?"


@router.callback_query(F.data.startswith("game_"))
async def cb_game_select(cb: CallbackQuery):
    game = cb.data.split("_", 1)[1]
    if game not in GAME_INFO:
        return await cb.answer("Noto'g'ri o'yin!")

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.telegram_id == cb.from_user.id))
        u = res.scalar_one_or_none()
        stars = u.stars if u else 0

        if game == "slots" and u and u.last_slots_at:
            if datetime.utcnow() - u.last_slots_at < DAILY_MS:
                rem = DAILY_MS - (datetime.utcnow() - u.last_slots_at)
                h, m = divmod(int(rem.total_seconds()), 3600)
                m //= 60
                await cb.message.edit_text(
                    f"⏰ <b>Slotlar kunlik!</b>\nKeyingi: <b>{h} soat {m} daqiqa</b>",
                    parse_mode="HTML", reply_markup=games_kb()
                )
                return await cb.answer()

    gi = GAME_INFO[game]
    rules = {
        "dice": "6→2× | 5→1.5× | 4→qaytarildi | 3→0.5× | 1-2→lost",
        "football": "3-5→1.44× | 1-2→lost",
        "basketball": "4-5→1.5× | 1-3→lost",
        "darts": "6→2× | 4-5→1.5× | 1-3→lost",
        "slots": "777→5× | 🍋→2× | 3bir→2× | lost (kunlik)",
        "coin": "50% → 1.9× yoki lost",
    }.get(game, "")

    await cb.message.edit_text(
        f"{gi['name']}\n\n📋 {rules}\n\n💎 Balans: {stars:.0f} ⭐\n\nTikish miqdori:",
        parse_mode="HTML", reply_markup=bet_kb(game)
    )
    await cb.answer()


@router.callback_query(F.data.startswith("bet_"))
async def cb_bet(cb: CallbackQuery):
    _, game, amt_str = cb.data.split("_", 2)
    if amt_str == "custom":
        await cb.message.edit_text(
            "✏️ Tikish miqdorini yozing (raqam):",
            reply_markup=back_kb("games")
        )
        # State management is simplified; we use a temp message
        await cb.answer()
        return

    bet = float(amt_str)
    tg_id = cb.from_user.id
    gi = GAME_INFO.get(game, {})

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.telegram_id == tg_id))
        u = res.scalar_one_or_none()
        if not u or u.stars < bet:
            await cb.answer(f"❌ Balans yetarli emas! Sizda: {u.stars if u else 0:.0f} ⭐", show_alert=True)
            return

        if game == "slots":
            u.last_slots_at = datetime.utcnow()

        u.stars -= bet
        await db.commit()

    await cb.message.edit_text(
        f"🎮 <b>{gi.get('name', game)}</b>\n💰 Tikish: {bet:.0f} ⭐\n⏳ Natijani kuting...",
        parse_mode="HTML"
    )

    if game == "coin":
        dice_msg = await cb.message.answer_dice(emoji="🎲")
        value = dice_msg.dice.value
    else:
        dice_msg = await cb.message.answer_dice(emoji=gi.get("emoji", "🎲"))
        value = dice_msg.dice.value

    await asyncio.sleep(3.5)

    win, msg_text = calc_result(game, value, bet)
    win = round(win, 1)

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.telegram_id == tg_id))
        u = res.scalar_one_or_none()
        if win > 0:
            u.stars += win
        await db.commit()
        new_bal = u.stars if u else 0

    net = win - bet
    net_str = f"+{net:.0f}" if net >= 0 else f"{net:.0f}"

    await cb.message.answer(
        f"🎮 <b>{gi.get('name', game)} natijasi</b>\n\n"
        f"🎲 Zar: <b>{value}</b>\n{msg_text}\n\n"
        f"💰 Tikish: {bet:.0f} ⭐\n"
        + (f"🏆 Yutish: +{win:.0f} ⭐\n" if win > 0 else "")
        + f"📊 O'zgarish: <b>{net_str} ⭐</b>\n"
        f"💎 Balans: <b>{new_bal:.0f} ⭐</b>",
        parse_mode="HTML", reply_markup=games_kb()
    )
    await cb.answer()


@router.callback_query(F.data == "daily")
async def cb_daily(cb: CallbackQuery):
    tg_id = cb.from_user.id
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.telegram_id == tg_id))
        u = res.scalar_one_or_none()
        if not u:
            return await cb.answer("❌ Xato!", show_alert=True)

        if u.last_daily_bonus and datetime.utcnow() - u.last_daily_bonus < DAILY_MS:
            rem = DAILY_MS - (datetime.utcnow() - u.last_daily_bonus)
            h, m = divmod(int(rem.total_seconds()), 3600)
            m //= 60
            await cb.message.edit_text(
                f"⏰ <b>Bonus olindi!</b>\nKeyingi: <b>{h} soat {m} daqiqa</b>",
                parse_mode="HTML", reply_markup=games_kb()
            )
            return await cb.answer()

        bonus = random.randint(1, 3)
        u.stars += bonus
        u.last_daily_bonus = datetime.utcnow()
        await db.commit()
        new_bal = u.stars

    await cb.message.edit_text(
        f"🎁 <b>Kunlik bonus!</b>\n\n⭐ +{bonus} Stars\n💎 Balans: <b>{new_bal:.0f} ⭐</b>\n\nErtaga qaytib keling! 🌟",
        parse_mode="HTML", reply_markup=games_kb()
    )
    await cb.answer()
