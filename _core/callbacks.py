from aiogram import Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME
from db import db
from _core.users import get_user

# لوحة الأدمن الرئيسية (أزرار)
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

# معالج الضغط على الأزرار
async def handle_callback_query(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in ADMIN_IDS:
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    data = callback.data
    if data == "admin_users":
        # عرض قائمة بالأعضاء (آخر 5)
        rows = await db.fetch("SELECT telegram_id, full_name, username, money FROM users ORDER BY created_at DESC LIMIT 5")
        if rows:
            text = "📋 *آخر 5 أعضاء:*\n"
            for row in rows:
                text += f"• {row['full_name']} (@{row['username'] or 'لا يوجد'}) - 💰 {row['money']} {CURRENCY_NAME}\n"
            await callback.message.edit_text(text, parse_mode="Markdown")
        else:
            await callback.message.edit_text("لا يوجد أعضاء بعد.")
        # إضافة زر رجوع
        back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back_btn)
    elif data == "admin_economy":
        total_money = await db.fetchval("SELECT SUM(money) FROM users")
        total_users = await db.fetchval("SELECT COUNT(*) FROM users")
        text = f"💰 *إحصائيات الاقتصاد*\nإجمالي الأموال: {total_money or 0} {CURRENCY_NAME}\nعدد المستخدمين: {total_users or 0}"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back_btn)
    elif data == "admin_games":
        await callback.message.edit_text("🎮 إعدادات الألعاب قيد التطوير...")
        back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back_btn)
    elif data == "admin_announce":
        await callback.message.edit_text("📣 أرسل الإعلان كرسالة جديدة (غير مضمنة) وسيتم إرساله لجميع المستخدمين.\nلإلغاء الأمر، أرسل /cancel")
        # هنا يمكن تفعيل حالة FSM لاستقبال الإعلان، لكن للتبسيط نكتفي برسالة
        back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back_btn)
    elif data == "admin_stats":
        total_msgs = await db.fetchval("SELECT SUM(messages_count) FROM users")
        total_wins = await db.fetchval("SELECT SUM(wins) FROM users")
        text = f"📊 *إحصائيات البوت*\nإجمالي الرسائل: {total_msgs or 0}\nإجمالي الانتصارات في الألعاب: {total_wins or 0}"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back_btn)
    elif data == "back_to_main":
        # العودة للوحة الرئيسية
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👤 إدارة الأعضاء", callback_data="admin_users")],
            [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
            [InlineKeyboardButton(text="🎮 إعدادات الألعاب", callback_data="admin_games")],
            [InlineKeyboardButton(text="📣 إعلان", callback_data="admin_announce")],
            [InlineKeyboardButton(text="📊 إحصائيات", callback_data="admin_stats")]
        ])
        await callback.message.edit_text("👑 *لوحة تحكم الأدمن*\nاختر أحد الخيارات:", parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(handle_callback_query)
