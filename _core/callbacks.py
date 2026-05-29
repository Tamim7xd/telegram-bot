from aiogram import Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME
from db import db
from _core.users import get_user, update_user_money

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

async def handle_callback_query(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in ADMIN_IDS:
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    data = callback.data
    if data == "admin_users":
        rows = await db.fetch("SELECT telegram_id, full_name, username, money, level FROM users ORDER BY created_at DESC LIMIT 10")
        if rows:
            text = "📋 *آخر 10 أعضاء:*\n\n"
            for row in rows:
                text += f"👤 {row['full_name']} (@{row['username'] or 'لا يوجد'})\n💰 {row['money']} {CURRENCY_NAME} | مستوى {row['level']}\n━━━━━━━━━━━━━━━\n"
            await callback.message.edit_text(text, parse_mode="Markdown")
        else:
            await callback.message.edit_text("لا يوجد أعضاء بعد.")
        back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back_btn)
    
    elif data == "admin_economy":
        total_money = await db.fetchval("SELECT SUM(money) FROM users")
        total_users = await db.fetchval("SELECT COUNT(*) FROM users")
        avg_money = total_money // total_users if total_users else 0
        text = f"💰 *إحصائيات الاقتصاد*\n\nإجمالي الأموال المتداولة: {total_money or 0} {CURRENCY_NAME}\nعدد المستخدمين: {total_users or 0}\nمتوسط الرصيد لكل مستخدم: {avg_money} {CURRENCY_NAME}"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back_btn)
    
    elif data == "admin_games":
        # يمكنك هنا إضافة إعدادات الألعاب لاحقاً
        await callback.message.edit_text("🎮 إعدادات الألعاب قيد التطوير...")
        back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back_btn)
    
    elif data == "admin_announce":
        await callback.message.edit_text("📣 أرسل الإعلان كرسالة جديدة (غير مضمنة) وسيتم إرساله لجميع المستخدمين.\nلإلغاء الأمر، أرسل /cancel")
        back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back_btn)
        # يمكن تفعيل FSM هنا، لكن سنكتفي بهذا
    
    elif data == "admin_stats":
        total_msgs = await db.fetchval("SELECT SUM(messages_count) FROM users")
        total_wins = await db.fetchval("SELECT SUM(wins) FROM users")
        top_user = await db.fetchrow("SELECT full_name, money FROM users ORDER BY money DESC LIMIT 1")
        top_text = f"🏆 أغنى عضو: {top_user['full_name']} (💰 {top_user['money']} {CURRENCY_NAME})" if top_user else "لا يوجد أعضاء بعد"
        text = f"📊 *إحصائيات البوت*\n\nإجمالي الرسائل: {total_msgs or 0}\nإجمالي الانتصارات في الألعاب: {total_wins or 0}\n{top_text}"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back_btn)
    
    elif data == "back_to_main":
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
