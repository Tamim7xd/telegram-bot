import time
import asyncio
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_owner, is_admin, add_admin, remove_admin, get_all_admins
from system_punishments.punishments_handler import unmute_user
from config import GROUP_ID, OWNER_ID, MAX_WARNINGS

# قائمة الألقاب الافتراضية
TITLES = {
    1: {"name": "عضو جديد 🌱", "price": 1000},
    2: {"name": "مقاتل ⚔️", "price": 2500},
    3: {"name": "ملك 👑", "price": 5000},
    4: {"name": "VIP 💎", "price": 10000},
    5: {"name": "أسطوري 🔥", "price": 20000},
}

async def owner_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("❌ هذه اللوحة للمالك فقط")
        return
    
    keyboard = [
        [InlineKeyboardButton("👥 إدارة المشرفين", callback_data="owner_admins")],
        [InlineKeyboardButton("🛒 إدارة السوق", callback_data="owner_shop")],
        [InlineKeyboardButton("⚠️ إدارة التحذيرات", callback_data="owner_warnings")],
        [InlineKeyboardButton("🧹 عمليات جماعية", callback_data="owner_bulk")],
        [InlineKeyboardButton("📢 إعلان متحرك", callback_data="owner_broadcast")],
        [InlineKeyboardButton("📊 السجلات", callback_data="owner_logs")],
        [InlineKeyboardButton("👤 الأعضاء", callback_data="owner_users")],
        [InlineKeyboardButton("🔙 إغلاق", callback_data="owner_close")]
    ]
    await update.message.reply_text("👑 لوحة المالك\n\nاختر الإجراء:", reply_markup=InlineKeyboardMarkup(keyboard))

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
    
    # ========== إدارة المشرفين ==========
    if data == "owner_admins":
        await show_admins_list(update, context, query)
        return
    
    if data == "admin_add_user":
        await show_users_for_admin(update, context, query, 0)
        return
    
    if data.startswith("admin_select_"):
        target_id = int(data.split("_")[2])
        await show_admin_type_select(update, context, query, target_id)
        return
    
    if data.startswith("admin_set_"):
        parts = data.split("_")
        target_id = int(parts[2])
        is_super = parts[3] == "super"
        
        conn = get_db()
        cursor = conn.execute("SELECT username, first_name FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.close()
        
        username = user["username"] if user else str(target_id)
        name = user["first_name"] if user else str(target_id)
        add_admin(target_id, username, is_super)
        
        role = "مشرف إداري 👑" if is_super else "مشرف عادي 🛡️"
        await query.edit_message_text(f"✅ تم تعيين {name} كـ {role}")
        await asyncio.sleep(2)
        await show_admins_list(update, context, query)
        return
    
    if data.startswith("admin_remove_"):
        target_id = int(data.split("_")[2])
        conn = get_db()
        cursor = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.close()
        name = user["first_name"] if user else str(target_id)
        
        remove_admin(target_id)
        await query.edit_message_text(f"✅ تم إزالة {name} من المشرفين")
        await asyncio.sleep(2)
        await show_admins_list(update, context, query)
        return
    
    # ========== بقية الأقسام ==========
    if data == "owner_shop":
        await show_shop_panel(update, context, query)
        return
    
    if data == "owner_warnings":
        await show_warnings_panel(update, context, query)
        return
    
    if data == "owner_bulk":
        await show_bulk_panel(update, context, query)
        return
    
    if data == "owner_broadcast":
        keyboard = [
            [InlineKeyboardButton("📤 إرسال ملصق/صورة متحركة", callback_data="broadcast_media")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]
        ]
        await query.edit_message_text("🎬 إعلان متحرك", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data == "broadcast_media":
        await query.edit_message_text("📤 أرسل الملصق أو الصورة المتحركة:\n(ملصق متحرك - GIF - فيديو قصير)")
        context.user_data['waiting_broadcast_media'] = True
        return
    
    if data == "owner_logs":
        await show_logs(update, context, query)
        return
    
    if data == "owner_users":
        await show_users_list(update, context, query, 0)
        return
    
    if data.startswith("users_page_"):
        page = int(data.split("_")[2])
        await show_users_list(update, context, query, page)
        return
    
    if data == "owner_back":
        keyboard = [
            [InlineKeyboardButton("👥 إدارة المشرفين", callback_data="owner_admins")],
            [InlineKeyboardButton("🛒 إدارة السوق", callback_data="owner_shop")],
            [InlineKeyboardButton("⚠️ إدارة التحذيرات", callback_data="owner_warnings")],
            [InlineKeyboardButton("🧹 عمليات جماعية", callback_data="owner_bulk")],
            [InlineKeyboardButton("📢 إعلان متحرك", callback_data="owner_broadcast")],
            [InlineKeyboardButton("📊 السجلات", callback_data="owner_logs")],
            [InlineKeyboardButton("👤 الأعضاء", callback_data="owner_users")],
            [InlineKeyboardButton("🔙 إغلاق", callback_data="owner_close")]
        ]
        await query.edit_message_text("👑 لوحة المالك\n\nاختر الإجراء:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

# ==================== دوال إدارة المشرفين ====================

async def show_admins_list(update, context, query):
    """عرض قائمة المشرفين الحاليين"""
    admins = get_all_admins()
    
    if not admins:
        text = "📋 لا يوجد مشرفين حالياً"
    else:
        text = "📋 **قائمة المشرفين:**\n\n"
        for a in admins:
            role = "👑 مشرف إداري" if a["is_super_admin"] else "🛡️ مشرف عادي"
            name = a["username"] or str(a["user_id"])
            text += f"• {name} - {role}\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مشرف جديد", callback_data="admin_add_user")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]
    ]
    
    for a in admins:
        if a["user_id"] != OWNER_ID:
            name = a["username"] or str(a["user_id"])
            keyboard.insert(-1, [InlineKeyboardButton(f"➖ إزالة {name}", callback_data=f"admin_remove_{a['user_id']}")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_users_for_admin(update, context, query, page):
    """عرض قائمة الأعضاء لاختيار مشرف جديد"""
    users_per_page = 10
    offset = page * users_per_page
    
    conn = get_db()
    cursor = conn.execute("SELECT user_id, first_name, username FROM users LIMIT ? OFFSET ?", (users_per_page, offset))
    users = cursor.fetchall()
    
    cursor = conn.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    conn.close()
    
    if not users:
        await query.edit_message_text("❌ لا يوجد أعضاء")
        return
    
    text = f"👥 **اختر عضواً** (الصفحة {page + 1})\n\n"
    keyboard = []
    
    for u in users:
        name = u["first_name"] or u["username"] or str(u["user_id"])
        keyboard.append([InlineKeyboardButton(f"👤 {name}", callback_data=f"admin_select_{u['user_id']}")])
    
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"admin_page_{page-1}"))
    if (page + 1) * users_per_page < total:
        nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"admin_page_{page+1}"))
    if nav:
        keyboard.append(nav)
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="owner_admins")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_admin_type_select(update, context, query, target_id):
    """اختيار نوع المشرف (عادي أو إداري)"""
    conn = get_db()
    cursor = conn.execute("SELECT first_name, username FROM users WHERE user_id = ?", (target_id,))
    user = cursor.fetchone()
    conn.close()
    
    name = user["first_name"] or user["username"] or str(target_id)
    
    keyboard = [
        [InlineKeyboardButton("🛡️ مشرف عادي", callback_data=f"admin_set_{target_id}_normal")],
        [InlineKeyboardButton("👑 مشرف إداري", callback_data=f"admin_set_{target_id}_super")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_admins")]
    ]
    await query.edit_message_text(f"👤 **{name}**\n\nاختر نوع المشرف:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ==================== دوال مساعدة أخرى ====================

async def show_shop_panel(update, context, query):
    keyboard = [
        [InlineKeyboardButton("📋 عرض الألقاب", callback_data="shop_view")],
        [InlineKeyboardButton("➕ إضافة لقب جديد", callback_data="shop_add")],
        [InlineKeyboardButton("✏️ تعديل لقب", callback_data="shop_edit")],
        [InlineKeyboardButton("🗑 حذف لقب", callback_data="shop_delete")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]
    ]
    await query.edit_message_text("🛒 إدارة السوق", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_warnings_panel(update, context, query):
    keyboard = [
        [InlineKeyboardButton("📋 قائمة المنذرين", callback_data="warnings_list")],
        [InlineKeyboardButton("⚙️ إعدادات التحذيرات", callback_data="warn_settings")],
        [InlineKeyboardButton("📢 تحذير للجميع", callback_data="warn_all")],
        [InlineKeyboardButton("🗑 حذف كل التحذيرات", callback_data="bulk_clear_warns")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]
    ]
    await query.edit_message_text("⚠️ إدارة التحذيرات", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_bulk_panel(update, context, query):
    keyboard = [
        [InlineKeyboardButton("🔓 فك الكتم للجميع", callback_data="bulk_unmute")],
        [InlineKeyboardButton("🔓 فك الحظر للجميع", callback_data="bulk_unban")],
        [InlineKeyboardButton("🗑 حذف كل التحذيرات", callback_data="bulk_clear_warns")],
        [InlineKeyboardButton("💰 إعادة ضبط الاقتصاد", callback_data="bulk_reset_economy")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]
    ]
    await query.edit_message_text("🧹 العمليات الجماعية\n⚠️ لا يمكن التراجع عنها", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_logs(update, context, query):
    conn = get_db()
    cursor = conn.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 30")
    logs = cursor.fetchall()
    conn.close()
    
    if not logs:
        await query.edit_message_text("📊 السجلات\n\nلا توجد سجلات حالياً")
        return
    
    text = "📊 آخر 30 عملية:\n\n"
    for log in logs:
        text += f"• {log['action']} - {log['target_name'] or log['target_id']}\n   👮 {log['admin_name']} - 🕐 {time.strftime('%Y-%m-%d %H:%M', time.localtime(log['timestamp']))}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]]
    await query.edit_message_text(text[:4000], reply_markup=InlineKeyboardMarkup(keyboard))

async def show_users_list(update, context, query, page):
    users_per_page = 10
    offset = page * users_per_page
    
    conn = get_db()
    cursor = conn.execute("SELECT user_id, first_name, username FROM users LIMIT ? OFFSET ?", (users_per_page, offset))
    users = cursor.fetchall()
    
    cursor = conn.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    conn.close()
    
    if not users:
        await query.edit_message_text("❌ لا يوجد أعضاء")
        return
    
    text = f"👥 قائمة الأعضاء (الصفحة {page + 1})\n\n"
    keyboard = []
    
    for u in users:
        name = u["first_name"] or u["username"] or str(u["user_id"])
        keyboard.append([InlineKeyboardButton(f"👤 {name}", callback_data=f"user_actions_{u['user_id']}")])
    
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"users_page_{page-1}"))
    if (page + 1) * users_per_page < total:
        nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"users_page_{page+1}"))
    if nav:
        keyboard.append(nav)
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ==================== دوال الأزرار الإضافية للمشرفين ====================

async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار التي تظهر في ملف العضو للمشرفين"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text("❌ ليس لديك صلاحية")
        return
    
    data = query.data
    
    if data.startswith("admin_warn_"):
        target_id = int(data.split("_")[2])
        await query.edit_message_text(f"⚠️ أرسل سبب التحذير:")
        context.user_data['admin_warn_target'] = target_id
        return
    
    if data.startswith("admin_mute_"):
        target_id = int(data.split("_")[2])
        await query.edit_message_text(f"🔇 أرسل مدة الكتم (مثال: 10د):")
        context.user_data['admin_mute_target'] = target_id
        return
    
    if data.startswith("admin_deduct_"):
        target_id = int(data.split("_")[2])
        await query.edit_message_text(f"💰 أرسل المبلغ:")
        context.user_data['admin_deduct_target'] = target_id
        return
    
    if data == "close":
        await query.delete_message()
        return

async def handle_admin_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الإدخالات من أزرار المشرفين"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not is_admin(user_id):
        return
    
    # تحذير
    if context.user_data.get('admin_warn_target'):
        target_id = context.user_data['admin_warn_target']
        conn = get_db()
        conn.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (target_id,))
        cursor = conn.execute("SELECT warnings, first_name FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.commit()
        conn.close()
        await context.bot.send_message(GROUP_ID, f"⚠️ تحذير\n\n👤 {user['first_name']}\n📝 {text}\n🔢 {user['warnings']}\n\n👮 بواسطة: {update.effective_user.first_name}")
        await update.message.reply_text(f"✅ تم")
        context.user_data['admin_warn_target'] = None
        return
    
    # كتم
    if context.user_data.get('admin_mute_target'):
        target_id = context.user_data['admin_mute_target']
        duration_str = text
        from system_punishments.punishments_handler import parse_duration, format_duration
        duration_seconds = parse_duration(duration_str)
        duration_text = format_duration(duration_seconds)
        until_time = int(time.time()) + duration_seconds
        
        try:
            await context.bot.restrict_chat_member(GROUP_ID, target_id, permissions=telegram.ChatPermissions(can_send_messages=False))
        except:
            pass
        
        conn = get_db()
        conn.execute("UPDATE users SET is_muted = 1, muted_until = ? WHERE user_id = ?", (until_time, target_id))
        cursor = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.commit()
        conn.close()
        
        await context.bot.send_message(GROUP_ID, f"🔇 كتم\n\n👤 {user['first_name']}\n⏱️ {duration_text}\n📝 {text}\n\n👮 بواسطة: {update.effective_user.first_name}")
        await update.message.reply_text(f"✅ تم")
        context.user_data['admin_mute_target'] = None
        return
    
    # خصم
    if context.user_data.get('admin_deduct_target'):
        try:
            amount = int(text)
            target_id = context.user_data['admin_deduct_target']
            conn = get_db()
            conn.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, target_id))
            cursor = conn.execute("SELECT balance, first_name FROM users WHERE user_id = ?", (target_id,))
            user = cursor.fetchone()
            conn.commit()
            conn.close()
            await context.bot.send_message(GROUP_ID, f"💰 خصم\n\n👤 {user['first_name']}\n💰 -{amount}\n💵 {user['balance']}\n\n👮 بواسطة: {update.effective_user.first_name}")
            await update.message.reply_text(f"✅ تم")
        except:
            await update.message.reply_text("❌ خطأ")
        context.user_data['admin_deduct_target'] = None
        return

# ==================== معالج الإدخالات ====================

async def handle_owner_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        return
    
    text = update.message.text.strip()
    
    # إعلان متحرك - انتظار الملف
    if context.user_data.get('waiting_broadcast_media'):
        if update.message.animation or update.message.document or update.message.sticker or update.message.video:
            context.user_data['broadcast_media'] = update.message
            await update.message.reply_text("✏️ أرسل نص الإعلان:")
            context.user_data['waiting_broadcast_text'] = True
            context.user_data['waiting_broadcast_media'] = False
        else:
            await update.message.reply_text("❌ أرسل ملف متحرك (GIF، ملصق، فيديو)")
        return
    
    # إعلان متحرك - انتظار النص
    if context.user_data.get('waiting_broadcast_text'):
        media_msg = context.user_data.get('broadcast_media')
        caption = f"📢 إعــــلان\n\n{text}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👮 صادر عن: المالك\n🕐 {time.strftime('%Y-%m-%d %H:%M')}"
        
        try:
            if media_msg.animation:
                await context.bot.send_animation(GROUP_ID, media_msg.animation.file_id, caption=caption)
            elif media_msg.sticker:
                await context.bot.send_sticker(GROUP_ID, media_msg.sticker.file_id)
                await context.bot.send_message(GROUP_ID, caption)
            elif media_msg.video:
                await context.bot.send_video(GROUP_ID, media_msg.video.file_id, caption=caption)
            await update.message.reply_text("✅ تم إرسال الإعلان المتحرك")
        except Exception as e:
            await update.message.reply_text(f"❌ فشل الإرسال: {e}")
        
        context.user_data['broadcast_media'] = None
        context.user_data['waiting_broadcast_text'] = False
        return