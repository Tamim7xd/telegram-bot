from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_admin
from system_punishments.punishments_handler import unmute_user
from config import GROUP_ID

async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ هذا الأمر للمشرفين فقط")
        return
    
    conn = get_db()
    cursor = conn.execute("SELECT COUNT(*) FROM users WHERE is_muted = 1 OR warnings > 0 OR is_banned = 1")
    count = cursor.fetchone()[0]
    conn.close()
    
    keyboard = [
        [InlineKeyboardButton(f"👥 عدد المخالفين: {count}", callback_data="admin_none")],
        [InlineKeyboardButton("🔍 ابحث", callback_data="admin_search")],
        [InlineKeyboardButton("🔙 إغلاق", callback_data="admin_close")]
    ]
    await update.message.reply_text("👑 لوحة التحكم الإدارية", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text("❌ ليس لديك صلاحية")
        return
    
    data = query.data
    
    if data == "admin_close":
        await query.edit_message_text("🔚 تم الإغلاق")
        return
    
    if data == "admin_search":
        conn = get_db()
        cursor = conn.execute("SELECT user_id, first_name, username, is_muted, warnings, is_banned FROM users WHERE is_muted = 1 OR warnings > 0 OR is_banned = 1 LIMIT 10")
        offenders = cursor.fetchall()
        conn.close()
        
        if not offenders:
            await query.edit_message_text("✅ لا يوجد مخالفين")
            return
        
        keyboard = []
        for o in offenders:
            name = o["first_name"] or o["username"] or str(o["user_id"])
            status = "مكتوم" if o["is_muted"] else ("محظور" if o["is_banned"] else f"منذر ({o['warnings']})")
            keyboard.append([InlineKeyboardButton(f"{name} - {status}", callback_data=f"admin_user_{o['user_id']}")])
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")])
        await query.edit_message_text("📋 المخالفين:", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data.startswith("admin_user_"):
        target_id = int(data.split("_")[2])
        keyboard = [[InlineKeyboardButton("🔓 فك العقوبة", callback_data=f"admin_unpunish_{target_id}")], [InlineKeyboardButton("🔙 رجوع", callback_data="admin_search")]]
        await query.edit_message_text("👤 المستخدم\n\nهل تريد فك العقوبة؟", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data.startswith("admin_unpunish_"):
        target_id = int(data.split("_")[2])
        await unmute_user(context, target_id)
        
        conn = get_db()
        conn.execute("UPDATE users SET warnings = 0, is_banned = 0 WHERE user_id = ?", (target_id,))
        try:
            await context.bot.unban_chat_member(GROUP_ID, target_id)
        except:
            pass
        conn.commit()
        conn.close()
        
        await query.edit_message_text("✅ تم فك العقوبة")
        return
    
    if data == "admin_back":
        conn = get_db()
        cursor = conn.execute("SELECT COUNT(*) FROM users WHERE is_muted = 1 OR warnings > 0 OR is_banned = 1")
        count = cursor.fetchone()[0]
        conn.close()
        keyboard = [[InlineKeyboardButton(f"👥 عدد المخالفين: {count}", callback_data="admin_none")], [InlineKeyboardButton("🔍 ابحث", callback_data="admin_search")], [InlineKeyboardButton("🔙 إغلاق", callback_data="admin_close")]]
        await query.edit_message_text("👑 لوحة التحكم الإدارية", reply_markup=InlineKeyboardMarkup(keyboard))