from aiogram import Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import ADMIN_IDS

async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⚠️ هذا الأمر للأدمن فقط.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 إدارة الأعضاء", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
        [InlineKeyboardButton(text="🎮 إعدادات الألعاب", callback_data="admin_games")],
        [InlineKeyboardButton(text="📣 إعلان", callback_data="admin_announce")],
        [InlineKeyboardButton(text="📊 إحصائيات", callback_data="admin_stats")]
    ])
    await message.reply("👑 *لوحة تحكم الأدمن*\nاختر أحد الخيارات:", reply_markup=keyboard, parse_mode="Markdown")

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    # يمكن إضافة معالج callback_query لاحقاً
