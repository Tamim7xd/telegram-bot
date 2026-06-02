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
        cursor = conn.execute("""
            SELECT user_id, first_name, username, is_muted, muted_until, warnings, is_banned 
            FROM users 
            WHERE is_muted = 1 OR warnings > 0 OR is_banned = 1 
            LIMIT 10
        """)
        offenders = cursor.fetchall()
        conn.close()
        
        if not offenders:
            await query.edit_message_text("✅ لا يوجد مخالفين")
            return
        
        keyboard = []
        for o in offenders:
            name = o["first_name"] or o["username"] or str(o["user_id"])
            
            if o["is_muted"]:
                remaining = o["muted_until"] - int(__import__('time').time())
                if remaining > 0:
                    status = f"مكتوم - متبقي {remaining//60} دقيقة"
                else:
                    status = "مكتوم (منتهي)"
            elif o["is_banned"]:
                status = "محظور"
            else:
                status = f"منذر ({o['warnings']})"
            
            keyboard.append([InlineKeyboardButton(f"{name} - {status}", callback_data=f"admin_user_{o['user_id']}")])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")])
        
        await query.edit_message_text("📋 **قائمة المخالفين:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    if data.startswith("admin_user_"):
        target_id = int(data.split("_")[2])
        
        conn = get_db()
        cursor = conn.execute("""
            SELECT user_id, first_name, username, is_muted, muted_until, warnings, is_banned 
            FROM users WHERE user_id = ?
        """, (target_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            await query.edit_message_text("❌ العضو غير موجود")
            return
        
        name = user["first_name"] or user["username"] or str(user["user_id"])
        username = user["username"] or "لا يوجد"
        
        # بناء نص الحالة
        status_text = ""
        if user["is_muted"]:
            remaining = user["muted_until"] - int(__import__('time').time())
            if remaining > 0:
                status_text = f"🔇 مكتوم - متبقي {remaining//60} دقيقة و {remaining%60} ثانية"
            else:
                status_text = "🔇 مكتوم (منتهي)"
        elif user["is_banned"]:
            status_text = "🚫 محظور"
        else:
            status_text = f"⚠️ منذر - {user['warnings']} تحذيرات"
        
        # بناء الأزرار حسب نوع المخالفة
        keyboard = []
        
        if user["is_muted"]:
            keyboard.append([InlineKeyboardButton("🔓 فك الكتم", callback_data=f"admin_unmute_{target_id}")])
        
        if user["is_banned"]:
            keyboard.append([InlineKeyboardButton("🔓 فك الحظر", callback_data=f"admin_unban_{target_id}")])
        
        if user["warnings"] > 0:
            keyboard.append([InlineKeyboardButton("🗑 حذف التحذيرات", callback_data=f"admin_clear_warns_{target_id}")])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_search")])
        
        await query.edit_message_text(
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 **{name}**\n"
            f"🆔 @{username}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{status_text}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    if data.startswith("admin_unmute_"):
        target_id = int(data.split("_")[2])
        await unmute_user(context, target_id)
        
        conn = get_db()
        cursor = conn.execute("SELECT first_name, username FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.close()
        
        name = user["first_name"] or user["username"] or str(target_id)
        
        await query.edit_message_text(f"✅ تم فك الكتم عن {name}")
        await context.bot.send_message(GROUP_ID, f"🔓 **فك كتم**\n\n👤 {name}\n\n👮 بواسطة: {update.effective_user.first_name}")
        await asyncio.sleep(2)
        
        # العودة لقائمة المخالفين
        await admin_search_again(update, context, query)
        return
    
    if data.startswith("admin_unban_"):
        target_id = int(data.split("_")[2])
        
        try:
            await context.bot.unban_chat_member(GROUP_ID, target_id)
        except:
            pass
        
        conn = get_db()
        conn.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
        cursor = conn.execute("SELECT first_name, username FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.commit()
        conn.close()
        
        name = user["first_name"] or user["username"] or str(target_id)
        
        await query.edit_message_text(f"✅ تم فك الحظر عن {name}")
        await context.bot.send_message(GROUP_ID, f"🔓 **فك حظر**\n\n👤 {name}\n\n👮 بواسطة: {update.effective_user.first_name}")
        await asyncio.sleep(2)
        await admin_search_again(update, context, query)
        return
    
    if data.startswith("admin_clear_warns_"):
        target_id = int(data.split("_")[3])
        
        conn = get_db()
        cursor = conn.execute("SELECT first_name, username FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.execute("UPDATE users SET warnings = 0 WHERE user_id = ?", (target_id,))
        conn.commit()
        conn.close()
        
        name = user["first_name"] or user["username"] or str(target_id)
        
        await query.edit_message_text(f"✅ تم حذف جميع تحذيرات {name}")
        await asyncio.sleep(2)
        await admin_search_again(update, context, query)
        return
    
    if data == "admin_back":
        await admin_search_again(update, context, query)
        return

async def admin_search_again(update, context, query):
    """إعادة عرض قائمة المخالفين"""
    conn = get_db()
    cursor = conn.execute("""
        SELECT user_id, first_name, username, is_muted, muted_until, warnings, is_banned 
        FROM users 
        WHERE is_muted = 1 OR warnings > 0 OR is_banned = 1 
        LIMIT 10
    """)
    offenders = cursor.fetchall()
    conn.close()
    
    if not offenders:
        await query.edit_message_text("✅ لا يوجد مخالفين")
        return
    
    keyboard = []
    for o in offenders:
        name = o["first_name"] or o["username"] or str(o["user_id"])
        
        if o["is_muted"]:
            remaining = o["muted_until"] - int(__import__('time').time())
            if remaining > 0:
                status = f"مكتوم - متبقي {remaining//60} دقيقة"
            else:
                status = "مكتوم (منتهي)"
        elif o["is_banned"]:
            status = "محظور"
        else:
            status = f"منذر ({o['warnings']})"
        
        keyboard.append([InlineKeyboardButton(f"{name} - {status}", callback_data=f"admin_user_{o['user_id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")])
    
    await query.edit_message_text("📋 **قائمة المخالفين:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")