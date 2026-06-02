import asyncio
import time
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
        await show_offenders_list(update, context, query)
        return
    
    if data.startswith("admin_user_"):
        target_id = int(data.split("_")[2])
        await show_offender_details(update, context, query, target_id)
        return
    
    if data.startswith("admin_unmute_"):
        target_id = int(data.split("_")[2])
        user = await unmute_user(context, target_id, send_notification=True)
        
        name = user["first_name"] if user else str(target_id)
        
        await query.edit_message_text(f"✅ تم فك الكتم عن {name}")
        await asyncio.sleep(2)
        await show_offenders_list(update, context, query)
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
        
        name = user["first_name"] if user else str(target_id)
        
        await query.edit_message_text(f"✅ تم فك الحظر عن {name}")
        await context.bot.send_message(GROUP_ID, f"🔓 **فك حظر**\n\n👤 {name}\n\n👮 بواسطة: {update.effective_user.first_name}")
        await asyncio.sleep(2)
        await show_offenders_list(update, context, query)
        return
    
    if data.startswith("admin_clear_warns_"):
        target_id = int(data.split("_")[3])
        
        conn = get_db()
        cursor = conn.execute("SELECT first_name, username FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.execute("UPDATE users SET warnings = 0 WHERE user_id = ?", (target_id,))
        conn.commit()
        conn.close()
        
        name = user["first_name"] if user else str(target_id)
        
        await query.edit_message_text(f"✅ تم حذف جميع تحذيرات {name}")
        await asyncio.sleep(2)
        await show_offenders_list(update, context, query)
        return
    
    if data == "admin_back":
        await show_offenders_list(update, context, query)
        return

async def show_offenders_list(update, context, query):
    """عرض قائمة المخالفين (فقط من لديه عقوبات فعلية)"""
    conn = get_db()
    current_time = int(time.time())
    
    # شرط صارم: فقط من لديه كتم نشط أو حظر أو تحذيرات
    cursor = conn.execute("""
        SELECT user_id, first_name, username, is_muted, muted_until, warnings, is_banned 
        FROM users 
        WHERE (is_muted = 1 AND muted_until > ?) OR is_banned = 1 OR warnings > 0
        LIMIT 10
    """, (current_time,))
    offenders = cursor.fetchall()
    conn.close()
    
    if not offenders:
        await query.edit_message_text("✅ لا يوجد مخالفين")
        return
    
    keyboard = []
    for o in offenders:
        name = o["first_name"] or o["username"] or str(o["user_id"])
        
        if o["is_muted"] and o["muted_until"] > current_time:
            status = "مكتوم"
        elif o["is_banned"]:
            status = "محظور"
        else:
            status = f"منذر ({o['warnings']})"
        
        keyboard.append([InlineKeyboardButton(f"{name} - {status}", callback_data=f"admin_user_{o['user_id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_back")])
    
    await query.edit_message_text("📋 **قائمة المخالفين:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_offender_details(update, context, query, target_id):
    """عرض تفاصيل المخالف + أزرار الإدارة"""
    conn = get_db()
    current_time = int(time.time())
    
    cursor = conn.execute("""
        SELECT user_id, first_name, username, is_muted, muted_until, warnings, is_banned 
        FROM users WHERE user_id = ?
    """, (target_id,))
    user = cursor.fetchone()
    
    # جلب آخر عملية
    cursor = conn.execute("""
        SELECT action, reason, admin_name, timestamp 
        FROM logs 
        WHERE target_id = ? 
        ORDER BY timestamp DESC 
        LIMIT 1
    """, (target_id,))
    last_action = cursor.fetchone()
    conn.close()
    
    if not user:
        await query.edit_message_text("❌ العضو غير موجود")
        return
    
    name = user["first_name"] or "مستخدم"
    username = user["username"] or "لا يوجد"
    
    details = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    details += f"👤 **{name}**\n"
    details += f"🆔 @{username}\n"
    details += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # حالة العضو
    if user["is_muted"] and user["muted_until"] > current_time:
        remaining = user["muted_until"] - current_time
        minutes = remaining // 60
        seconds = remaining % 60
        details += f"🔇 **مكتوم** - متبقي {minutes} دقيقة و {seconds} ثانية\n"
    elif user["is_banned"]:
        details += f"🚫 **محظور**\n"
    else:
        details += f"⚠️ **منذر** - {user['warnings']} تحذيرات\n"
    
    if last_action:
        details += f"\n📋 **آخر عملية:**\n"
        details += f"   {last_action['action']}\n"
        details += f"   📝 {last_action['reason']}\n"
        details += f"   👮 {last_action['admin_name']}\n"
    
    details += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    keyboard = []
    
    if user["is_muted"] and user["muted_until"] > current_time:
        keyboard.append([InlineKeyboardButton("🔓 فك الكتم", callback_data=f"admin_unmute_{target_id}")])
    
    if user["is_banned"]:
        keyboard.append([InlineKeyboardButton("🔓 فك الحظر", callback_data=f"admin_unban_{target_id}")])
    
    if user["warnings"] > 0:
        keyboard.append([InlineKeyboardButton("🗑 حذف التحذيرات", callback_data=f"admin_clear_warns_{target_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_search")])
    
    await query.edit_message_text(
        details,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )