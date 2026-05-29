from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME
from db import db

# لوحة الأدمن الرئيسية
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

# معالج الضغط على الأزرار (مع إصلاح المشكلة)
async def handle_callback_query(callback: CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in ADMIN_IDS:
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    data = callback.data
    await callback.answer("✅ جاري التنفيذ...")  # إشعار فوري للمستخدم
    
    if data == "admin_users":
        rows = await db.fetch("SELECT full_name, username, money, level FROM users ORDER BY created_at DESC LIMIT 10")
        if rows:
            text = "📋 *آخر 10 أعضاء:*\n\n"
            for r in rows:
                text += f"👤 {r['full_name']} (@{r['username'] or 'لا يوجد'})\n💰 {r['money']} {CURRENCY_NAME} | مستوى {r['level']}\n━━━━━━━━━━━━━━━\n"
        else:
            text = "لا يوجد أعضاء بعد."
        await callback.message.edit_text(text, parse_mode="Markdown")
        # زر رجوع
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back)
    
    elif data == "admin_economy":
        total_money = await db.fetchval("SELECT SUM(money) FROM users") or 0
        total_users = await db.fetchval("SELECT COUNT(*) FROM users") or 0
        avg_money = total_money // total_users if total_users else 0
        text = f"💰 *إحصائيات الاقتصاد*\n\nإجمالي الأموال: {total_money} {CURRENCY_NAME}\nعدد المستخدمين: {total_users}\nمتوسط الرصيد: {avg_money} {CURRENCY_NAME}"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back)
    
    elif data == "admin_games":
        text = "🎮 *إعدادات الألعاب*\n\nيمكنك لاحقاً تفعيل/تعطيل أنواع الألعاب وتعديل الجوائز."
        await callback.message.edit_text(text, parse_mode="Markdown")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back)
    
    elif data == "admin_announce":
        text = "📣 *إعلان*\nأرسل رسالتك الآن (نص عادي)، وسيتم إرسالها لجميع المستخدمين.\nلإلغاء الأمر، أرسل /cancel"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back)
    
    elif data == "admin_stats":
        total_msgs = await db.fetchval("SELECT SUM(messages_count) FROM users") or 0
        total_wins = await db.fetchval("SELECT SUM(wins) FROM users") or 0
        top_user = await db.fetchrow("SELECT full_name, money FROM users ORDER BY money DESC LIMIT 1")
        top_text = f"🏆 أغنى عضو: {top_user['full_name']} (💰 {top_user['money']} {CURRENCY_NAME})" if top_user else "لا يوجد أعضاء بعد"
        text = f"📊 *إحصائيات البوت*\n\nإجمالي الرسائل: {total_msgs}\nإجمالي الانتصارات: {total_wins}\n{top_text}"
        await callback.message.edit_text(text, parse_mode="Markdown")
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_to_main")]])
        await callback.message.edit_reply_markup(reply_markup=back)
    
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

# تسجيل المعالجات
def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(handle_callback_query)
