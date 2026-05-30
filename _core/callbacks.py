from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS

async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("للأدمن فقط")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="اختبار", callback_data="test")]
    ])
    await message.reply("لوحة اختبار", reply_markup=kb)

async def process_callback(callback: CallbackQuery):
    await callback.answer()
    if callback.data == "test":
        await callback.message.edit_text("✅ الزر يعمل")

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(process_callback)
