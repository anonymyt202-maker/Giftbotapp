from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from bot.keyboards.main import back_kb
from config import settings

router = Router()
_pending: dict[int, int] = {}   # admin_msg_id → user_id


@router.callback_query(F.data == "support")
async def cb_support(cb: CallbackQuery):
    await cb.message.edit_text(
        "📨 <b>Adminga xabar</b>\n\nXabaringizni yozing:",
        parse_mode="HTML", reply_markup=back_kb("main")
    )
    _pending[cb.from_user.id] = -1   # kutayotgan holat
    await cb.answer()


@router.message(F.text & ~F.text.startswith("/"))
async def handle_support_message(msg: Message):
    uid = msg.from_user.id
    if uid not in _pending:
        return
    if _pending[uid] != -1:
        return

    uname = f"@{msg.from_user.username}" if msg.from_user.username else str(uid)
    for admin_id in settings.admin_ids:
        try:
            sent = await msg.bot.send_message(
                admin_id,
                f"📨 <b>Foydalanuvchidan xabar</b>\n\n"
                f"👤 {uname} (<code>{uid}</code>)\n\n"
                f"💬 {msg.text}\n\n"
                f"<i>Javob berish uchun /reply_{uid} yozing</i>",
                parse_mode="HTML",
            )
            _pending[uid] = sent.message_id
        except Exception:
            pass

    del _pending[uid]
    await msg.answer(
        "✅ <b>Xabaringiz adminga yuborildi!</b>\nTez orada javob berishadi.",
        parse_mode="HTML",
        reply_markup=back_kb("main"),
    )


@router.message(F.text.startswith("/reply_"))
async def admin_reply(msg: Message):
    if msg.from_user.id not in settings.admin_ids:
        return
    parts = msg.text.split(" ", 1)
    target_id = int(parts[0].split("_")[1])
    reply_text = parts[1] if len(parts) > 1 else ""
    if not reply_text:
        return await msg.answer("❌ Javob matni kiriting: /reply_USER_ID matn")
    try:
        await msg.bot.send_message(
            target_id,
            f"📩 <b>Admin javobi:</b>\n\n{reply_text}",
            parse_mode="HTML",
        )
        await msg.answer("✅ Javob yuborildi.")
    except Exception as e:
        await msg.answer(f"❌ Xato: {e}")
