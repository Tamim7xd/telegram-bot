from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_owner, add_admin, remove_admin, get_all_admins
from config import GROUP_ID
from system_punishments.punishments_handler import unmute_user

async def owner_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("❌ هذه اللوحة للمالك فقط")
        return
    
    keyboard = [
        [InlineKeyboardButton("👥 إدارة المشرفين", callback_data="owner_admins")],
        [InlineKeyboardButton("🛒 إدارة السوق", callback_data="owner_shop")],
        [InlineKeyboardButton("🧹 عمليات جماعية", callback_data="owner_bulk")],
        [InlineKeyboardButton("📊 السجلات", callback_data="owner_logs")],
        [InlineKeyboardButton("🔙 إغلاق", callback_data="owner_close")]
    ]
    
    await update.message.reply_text(
        "👑 **لوحة المالك**\n\nاختر الإجراء المناسب:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def owner_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_owner(user_id):
        await query.edit_message_text("❌ ليس لديك صلاحية")
        return
    
    data = query.data
    
    if data == "owner_close":
        await query.edit_message_text("🔚 تم إغلاق لوحة المالك")
        return
    
    if data == "owner_admins":
        admins = get_all_admins()
        text = "📋 **قائمة المشرفين:**\n\n"
        for a in admins:
            role = "👑 مشرف إداري" if a["is_super_admin"] else "🛡️ مشرف عادي"
            text += f"• {a['username'] or a['user_id']} - {role}\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ تعيين مشرف عادي", callback_data="owner_add_admin")],
            [InlineKeyboardButton("👑 تعيين مشرف إداري", callback_data="owner_add_super")],
            [InlineKeyboardButton("➖ إزالة مشرف", callback_data="owner_remove_admin")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]
        ]
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    if data == "owner_bulk":
        keyboard = [
            [InlineKeyboardButton("🔓 فك الكتم للجميع", callback_data="owner_unmute_all")],
            [InlineKeyboardButton("🗑 حذف كل التحذيرات", callback_data="owner_clear_warnings")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]
        ]
        
        await query.edit_message_text("🧹 **العمليات الجماعية**\n⚠️ تحذير: هذه العمليات لا يمكن التراجع عنها", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    if data == "owner_unmute_all":
        conn = get_db()
        cursor = conn.execute("SELECT user_id FROM users WHERE is_muted = 1")
        muted_users = cursor.fetchall()
        
        for u in muted_users:
            await unmute_user(context, u["user_id"])
        
        conn.close()
        await query.edit_message_text("✅ **تم فك الكتم عن جميع الأعضاء**")
        return
    
    if data == "owner_clear_warnings":
        conn = get_db()
        conn.execute("UPDATE users SET warnings = 0")
        conn.commit()
        conn.close()
        await query.edit_message_text("✅ **تم حذف جميع التحذيرات**")
        return
    
    if data == "owner_back":
        keyboard = [
            [InlineKeyboardButton("👥 إدارة المشرفين", callback_data="owner_admins")],
            [InlineKeyboardButton("🛒 إدارة السوق", callback_data="owner_shop")],
            [InlineKeyboardButton("🧹 عمليات جماعية", callback_data="owner_bulk")],
            [InlineKeyboardButton("📊 السجلات", callback_data="owner_logs")],
            [InlineKeyboardButton("🔙 إغلاق", callback_data="owner_close")]
        ]
        
        await query.edit_message_text("👑 **لوحة المالك**\n\nاختر الإجراء المناسب:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")