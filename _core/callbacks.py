from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS

async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⚠️ للأدمن فقط")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 الأعضاء", callback_data="admin_users")],
        [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
    ])
    await message.reply("👑 لوحة الأدمن", reply_markup=kb)

async def process_callback(callback: CallbackQuery):
    await callback.answer()
    data = callback.data
    if data == "admin_users":
        await callback.message.edit_text("👥 قائمة الأعضاء (سيتم تطويرها لاحقاً)")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="admin_back")]])
        await callback.message.edit_reply_markup(reply_markup=back)
    elif data == "admin_back":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 الأعضاء", callback_data="admin_users")],
            [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
        ])
        await callback.message.edit_text("👑 لوحة الأدمن", reply_markup=kb)
    elif data == "admin_close":
        await callback.message.delete()

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(process_callback)
