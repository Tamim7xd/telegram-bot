from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME
from db import db

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
    await message.reply("👑 *لوحة تحكم الأدمن*", reply_markup=keyboard, parse_mode="Markdown")

async def handle_callback_query(callback: CallbackQuery):
    await callback.answer("جاري المعالجة...")
    user_id = callback.from_user.id
    if user_id not in ADMIN_IDS:
        await callback.message.edit_text("❌ غير مصرح لك")
        return
    data = callback.data
    if data == "admin_users":
        rows = await db.fetch("SELECT full_name, username, money, level FROM users ORDER BY created_at DESC LIMIT 10")
        text = "📋 *آخر 10 أعضاء:*\n\n" + "\n".join([f"👤 {r['full_name']} (@{r['username'] or '-'}) | 💰{r['money']} | مستوى {r['level']}" for r in rows])
        await callback.message.edit_text(text, parse_mode="Markdown")
    elif data == "admin_economy":
        total = await db.fetchval("SELECT SUM(money) FROM users") or 0
        users = await db.fetchval("SELECT COUNT(*) FROM users") or 0
        await callback.message.edit_text(f"💰 *إجمالي الأموال:* {total} {CURRENCY_NAME}\n👥 *عدد المستخدمين:* {users}", parse_mode="Markdown")
    elif data == "admin_stats":
        msgs = await db.fetchval("SELECT SUM(messages_count) FROM users") or 0
        wins = await db.fetchval("SELECT SUM(wins) FROM users") or 0
        await callback.message.edit_text(f"📊 *إحصائيات*\n📝 رسائل: {msgs}\n🏆 انتصارات: {wins}", parse_mode="Markdown")
    else:
        await callback.message.edit_text("🚧 قيد التطوير")
    # إضافة زر رجوع
    back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
    await callback.message.edit_reply_markup(reply_markup=back)

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(handle_callback_query)
