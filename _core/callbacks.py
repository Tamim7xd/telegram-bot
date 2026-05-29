from aiogram import Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME
from db import db

# لوحة الأدمن
async def admin_panel(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⚠️ هذا الأمر للأدمن فقط.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 الأعضاء", callback_data="users")],
        [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="economy")],
        [InlineKeyboardButton(text="📊 إحصائيات", callback_data="stats")],
        [InlineKeyboardButton(text="◀️ إغلاق", callback_data="close")]
    ])
    await message.reply("👑 *لوحة الأدمن*", reply_markup=keyboard, parse_mode="Markdown")

# معالج الضغط على الأزرار
async def process_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in ADMIN_IDS:
        await callback.answer("غير مسموح", show_alert=True)
        return
    data = callback.data
    await callback.answer("✅")

    if data == "users":
        rows = await db.fetch("SELECT full_name, username, money, level FROM users ORDER BY created_at DESC LIMIT 5")
        text = "👥 *آخر 5 أعضاء:*\n"
        for r in rows:
            text += f"• {r['full_name']} (@{r['username'] or '-'}) | 💰{r['money']} | مستوى {r['level']}\n"
        await callback.message.edit_text(text, parse_mode="Markdown")
        # إضافة زر رجوع
        back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back")]])
        await callback.message.edit_reply_markup(reply_markup=back_kb)

    elif data == "economy":
        total = await db.fetchval("SELECT SUM(money) FROM users") or 0
        count = await db.fetchval("SELECT COUNT(*) FROM users") or 0
        text = f"💰 *الاقتصاد*\nإجمالي الأموال: {total} {CURRENCY_NAME}\nعدد المستخدمين: {count}"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back")]])
        await callback.message.edit_reply_markup(reply_markup=back_kb)

    elif data == "stats":
        msgs = await db.fetchval("SELECT SUM(messages_count) FROM users") or 0
        wins = await db.fetchval("SELECT SUM(wins) FROM users") or 0
        text = f"📊 *إحصائيات*\nالرسائل: {msgs}\nالانتصارات: {wins}"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back")]])
        await callback.message.edit_reply_markup(reply_markup=back_kb)

    elif data == "back":
        # العودة للوحة الرئيسية
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 الأعضاء", callback_data="users")],
            [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="economy")],
            [InlineKeyboardButton(text="📊 إحصائيات", callback_data="stats")],
            [InlineKeyboardButton(text="◀️ إغلاق", callback_data="close")]
        ])
        await callback.message.edit_text("👑 *لوحة الأدمن*", parse_mode="Markdown", reply_markup=keyboard)

    elif data == "close":
        await callback.message.delete()

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(process_callback)
