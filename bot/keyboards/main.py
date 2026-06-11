from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import settings


def main_menu_kb(webapp_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🎁 Gift Sotib Olish",
        web_app=WebAppInfo(url=f"{webapp_url}/webapp/user"),
    ))
    builder.row(
        InlineKeyboardButton(text="👤 Hisobim",     callback_data="balance"),
        InlineKeyboardButton(text="👥 Referal",     callback_data="referral"),
    )
    builder.row(
        InlineKeyboardButton(text="🎮 O'yinlar",    callback_data="games"),
        InlineKeyboardButton(text="📨 Adminga xabar", callback_data="support"),
    )
    return builder.as_markup()


def admin_panel_kb(webapp_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🔧 Admin Panelni Ochish",
            web_app=WebAppInfo(url=f"{webapp_url}/webapp/admin"),
        )
    ]])


def games_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🎲 Zar",        callback_data="game_dice"),
        InlineKeyboardButton(text="⚽ Futbol",     callback_data="game_football"),
        InlineKeyboardButton(text="🏀 Basketbol",  callback_data="game_basketball"),
    )
    builder.row(
        InlineKeyboardButton(text="🎯 Darts",      callback_data="game_darts"),
        InlineKeyboardButton(text="🎰 Slotlar",    callback_data="game_slots"),
        InlineKeyboardButton(text="🪙 Coin Flip",  callback_data="game_coin"),
    )
    builder.row(
        InlineKeyboardButton(text="🎁 Kunlik bonus", callback_data="daily"),
        InlineKeyboardButton(text="⬅️ Orqaga",       callback_data="main"),
    )
    return builder.as_markup()


def bet_kb(game: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for amt in [1, 5, 10, 25, 50, 100]:
        builder.button(text=f"{amt} ⭐", callback_data=f"bet_{game}_{amt}")
    builder.button(text="✏️ Boshqa", callback_data=f"bet_{game}_custom")
    builder.button(text="⬅️ Orqaga", callback_data="games")
    builder.adjust(3, 3, 2)
    return builder.as_markup()


def back_kb(callback: str = "main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="⬅️ Bosh menyu", callback_data=callback)
    ]])
