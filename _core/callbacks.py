from aiogram import Dispatcher, types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_IDS, CURRENCY_NAME
from db import db
from _core.users import get_user, update_user_money, set_user_status

# ---------- لوحة الأدمن الرئيسية ----------
async def admin_panel(message: Message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.reply("⚠️ هذا الأمر للأدمن فقط.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 الأعضاء", callback_data="admin_users")],
        [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
        [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
    ])
    await message.reply("👑 لوحة التحكم", reply_markup=keyboard)

# ---------- عرض قائمة الأعضاء (أسماء قابلة للنقر) ----------
async def show_users(callback: CallbackQuery):
    rows = await db.fetch("SELECT telegram_id, full_name FROM users ORDER BY created_at DESC LIMIT 20")
    if not rows:
        await callback.message.edit_text("لا يوجد أعضاء بعد.")
        return
    buttons = []
    for r in rows:
        buttons.append([InlineKeyboardButton(text=r['full_name'], callback_data=f"user_{r['telegram_id']}")])
    buttons.append([InlineKeyboardButton(text="◀️ رجوع", callback_data="back_main")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("اختر عضواً:", reply_markup=keyboard)

# ---------- عرض تفاصيل العضو وأزرار التحكم ----------
async def show_user_controls(callback: CallbackQuery, user_id: int):
    user = await get_user(user_id)
    if not user:
        await callback.answer("المستخدم غير موجود")
        return
    text = f"👤 {user['full_name']}\n💰 الرصيد: {user['money']}\n⭐ XP: {user['xp']}\n📊 المستوى: {user['level']}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ +100", callback_data=f"add_{user_id}_100"),
         InlineKeyboardButton(text="➖ -50", callback_data=f"sub_{user_id}_50")],
        [InlineKeyboardButton(text="🔇 كتم", callback_data=f"mute_{user_id}"),
         InlineKeyboardButton(text="🔈 فك كتم", callback_data=f"unmute_{user_id}")],
        [InlineKeyboardButton(text="🚫 حظر", callback_data=f"ban_{user_id}"),
         InlineKeyboardButton(text="✅ فك حظر", callback_data=f"unban_{user_id}")],
        [InlineKeyboardButton(text="◀️ رجوع", callback_data="users_list")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)

# ---------- المعالج الرئيسي لجميع الأزرار ----------
async def process_callback(callback: CallbackQuery):
    # طباعة للفحص (تظهر في سجل Railway)
    print(f"[DEBUG] Received callback: {callback.data}")
    await callback.answer()  # يزيل "الانتظار"

    data = callback.data
    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    # التأكد من الصلاحيات (لأزرار الإدارة فقط)
    if user_id not in ADMIN_IDS and not data.startswith(("user_", "back_main", "users_list")):
        await callback.message.answer("❌ غير مصرح.")
        return

    # قائمة الأعضاء
    if data == "admin_users":
        await show_users(callback)
        return
    # الاقتصاد
    if data == "admin_economy":
        total = await db.fetchval("SELECT SUM(money) FROM users") or 0
        count = await db.fetchval("SELECT COUNT(*) FROM users") or 0
        text = f"💰 إجمالي الأموال: {total}\n👥 عدد المستخدمين: {count}"
        await callback.message.edit_text(text)
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_main")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    # الإحصائيات
    if data == "admin_stats":
        msgs = await db.fetchval("SELECT SUM(messages_count) FROM users") or 0
        wins = await db.fetchval("SELECT SUM(wins) FROM users") or 0
        text = f"📊 الرسائل: {msgs}\n🏆 الانتصارات: {wins}"
        await callback.message.edit_text(text)
        back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="◀️ رجوع", callback_data="back_main")]])
        await callback.message.edit_reply_markup(reply_markup=back)
        return
    # إغلاق اللوحة
    if data == "admin_close":
        await callback.message.delete()
        return
    # رجوع للوحة الرئيسية
    if data == "back_main":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 الأعضاء", callback_data="admin_users")],
            [InlineKeyboardButton(text="💰 الاقتصاد", callback_data="admin_economy")],
            [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton(text="❌ إغلاق", callback_data="admin_close")]
        ])
        await callback.message.edit_text("👑 لوحة التحكم", reply_markup=keyboard)
        return
    # اختيار مستخدم
    if data.startswith("user_"):
        target_id = int(data.split("_")[1])
        await show_user_controls(callback, target_id)
        return
    # رجوع لقائمة المستخدمين
    if data == "users_list":
        await show_users(callback)
        return
    # إضافة رصيد
    if data.startswith("add_"):
        parts = data.split("_")
        target_id = int(parts[1])
        amount = int(parts[2])
        await update_user_money(target_id, amount, "إضافة من اللوحة", user_id)
        await callback.message.answer(f"✅ تم إضافة {amount}")
        await show_user_controls(callback, target_id)
        return
    # خصم
    if data.startswith("sub_"):
        parts = data.split("_")
        target_id = int(parts[1])
        amount = int(parts[2])
        await update_user_money(target_id, -amount, "خصم من اللوحة", user_id)
        await callback.message.answer(f"✅ تم خصم {amount}")
        await show_user_controls(callback, target_id)
        return
    # كتم
    if data.startswith("mute_"):
        target_id = int(data.split("_")[1])
        await set_user_status(target_id, "muted")
        await callback.message.answer("🔇 تم الكتم")
        await show_user_controls(callback, target_id)
        return
    # فك كتم
    if data.startswith("unmute_"):
        target_id = int(data.split("_")[1])
        await set_user_status(target_id, "active")
        await callback.message.answer("🔈 تم فك الكتم")
        await show_user_controls(callback, target_id)
        return
    # حظر
    if data.startswith("ban_"):
        target_id = int(data.split("_")[1])
        await set_user_status(target_id, "banned")
        await callback.message.answer("🚫 تم الحظر")
        await show_user_controls(callback, target_id)
        return
    # فك حظر
    if data.startswith("unban_"):
        target_id = int(data.split("_")[1])
        await set_user_status(target_id, "active")
        await callback.message.answer("✅ تم فك الحظر")
        await show_user_controls(callback, target_id)
        return

def register_callback_handlers(dp: Dispatcher):
    dp.message.register(admin_panel, Command("adminiq"))
    dp.callback_query.register(process_callback)
