import time
import asyncio
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_owner, is_admin, add_admin, remove_admin, get_all_admins
from system_punishments.punishments_handler import unmute_user
from config import GROUP_ID, MAX_WARNINGS

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
        await show_admins_panel(update, context, query)
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
        cursor = conn.execute("SELECT username FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.close()
        
        username = user["username"] if user else str(target_id)
        add_admin(target_id, username, is_super)
        
        role = "مشرف إداري" if is_super else "مشرف عادي"
        await query.edit_message_text(f"✅ تم تعيين المستخدم كـ {role}")
        await asyncio.sleep(2)
        await show_admins_panel(update, context, query)
        return
    
    if data.startswith("admin_remove_"):
        target_id = int(data.split("_")[2])
        remove_admin(target_id)
        await query.edit_message_text("✅ تم إزالة المستخدم من المشرفين")
        await asyncio.sleep(2)
        await show_admins_panel(update, context, query)
        return
    
    # ========== إدارة السوق ==========
    if data == "owner_shop":
        await show_shop_panel(update, context, query)
        return
    
    if data == "shop_view":
        await show_shop_items(update, context, query)
        return
    
    if data == "shop_add":
        await query.edit_message_text("✏️ أرسل اسم اللقب الجديد:\n(مثال: محارب 🛡️)")
        context.user_data['waiting_shop_name'] = True
        return
    
    if data == "shop_edit":
        await show_shop_edit_list(update, context, query)
        return
    
    if data.startswith("shop_edit_title_"):
        title_id = int(data.split("_")[3])
        context.user_data['editing_title_id'] = title_id
        await query.edit_message_text("✏️ أرسل الاسم الجديد (اتركه فارغاً لعدم التغيير):")
        context.user_data['waiting_edit_name'] = True
        return
    
    if data == "shop_delete":
        await show_shop_delete_list(update, context, query)
        return
    
    if data.startswith("shop_delete_title_"):
        title_id = int(data.split("_")[3])
        title_name = TITLES[title_id]["name"]
        keyboard = [
            [InlineKeyboardButton("✅ نعم، احذف", callback_data=f"shop_confirm_delete_{title_id}")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="owner_shop")]
        ]
        await query.edit_message_text(f"⚠️ تأكيد حذف اللقب: {title_name}\n\nهل أنت متأكد؟", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    if data.startswith("shop_confirm_delete_"):
        title_id = int(data.split("_")[3])
        del TITLES[title_id]
        new_titles = {}
        for i, (tid, title) in enumerate(TITLES.items(), 1):
            new_titles[i] = title
        TITLES.clear()
        TITLES.update(new_titles)
        await query.edit_message_text("✅ تم حذف اللقب بنجاح")
        await asyncio.sleep(2)
        await show_shop_panel(update, context, query)
        return
    
    # ========== إدارة التحذيرات ==========
    if data == "owner_warnings":
        await show_warnings_panel(update, context, query)
        return
    
    if data == "warnings_list":
        await show_warnings_list(update, context, query)
        return
    
    if data.startswith("warn_user_"):
        target_id = int(data.split("_")[2])
        await show_user_warnings(update, context, query, target_id)
        return
    
    if data.startswith("warn_add_"):
        target_id = int(data.split("_")[2])
        conn = get_db()
        conn.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (target_id,))
        cursor = conn.execute("SELECT warnings, first_name FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.commit()
        conn.close()
        await query.edit_message_text(f"✅ تم إضافة تحذير\n👤 {user['first_name']}\n⚠️ العدد: {user['warnings']}")
        await context.bot.send_message(GROUP_ID, f"⚠️ تحذير\n\n👤 {user['first_name']}\n🔢 {user['warnings']}\n\n👮 بواسطة: المالك")
        await asyncio.sleep(2)
        await show_warnings_panel(update, context, query)
        return
    
    if data.startswith("warn_remove_"):
        target_id = int(data.split("_")[2])
        conn = get_db()
        conn.execute("UPDATE users SET warnings = warnings - 1 WHERE user_id = ? AND warnings > 0", (target_id,))
        cursor = conn.execute("SELECT warnings, first_name FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.commit()
        conn.close()
        await query.edit_message_text(f"✅ تم حذف تحذير\n👤 {user['first_name']}\n⚠️ العدد: {user['warnings']}")
        await asyncio.sleep(2)
        await show_warnings_panel(update, context, query)
        return
    
    if data.startswith("warn_clear_"):
        target_id = int(data.split("_")[2])
        conn = get_db()
        cursor = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.execute("UPDATE users SET warnings = 0 WHERE user_id = ?", (target_id,))
        conn.commit()
        conn.close()
        await query.edit_message_text(f"✅ تم حذف جميع تحذيرات {user['first_name']}")
        await asyncio.sleep(2)
        await show_warnings_panel(update, context, query)
        return
    
    if data == "warn_all":
        await query.edit_message_text("📢 أرسل سبب التحذير العام:")
        context.user_data['waiting_warn_all'] = True
        return
    
    if data == "warn_settings":
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]]
        await query.edit_message_text(f"⚙️ إعدادات التحذيرات\n\nالحد الأقصى: {MAX_WARNINGS}", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    
    # ========== عمليات جماعية ==========
    if data == "owner_bulk":
        await show_bulk_panel(update, context, query)
        return
    
    if data == "bulk_unmute":
        conn = get_db()
        cursor = conn.execute("SELECT user_id FROM users WHERE is_muted = 1")
        muted = cursor.fetchall()
        for u in muted:
            await unmute_user(context, u["user_id"])
        conn.close()
        await query.edit_message_text("✅ تم فك الكتم عن جميع الأعضاء")
        await context.bot.send_message(GROUP_ID, "🔓 تم فك الكتم عن جميع الأعضاء\n👮 بواسطة: المالك")
        await asyncio.sleep(2)
        await show_bulk_panel(update, context, query)
        return
    
    if data == "bulk_unban":
        conn = get_db()
        cursor = conn.execute("SELECT user_id FROM users WHERE is_banned = 1")
        banned = cursor.fetchall()
        for u in banned:
            try:
                await context.bot.unban_chat_member(GROUP_ID, u["user_id"])
            except:
                pass
        conn.execute("UPDATE users SET is_banned = 0")
        conn.commit()
        conn.close()
        await query.edit_message_text("✅ تم فك الحظر عن جميع الأعضاء")
        await context.bot.send_message(GROUP_ID, "🔓 تم فك الحظر عن جميع الأعضاء\n👮 بواسطة: المالك")
        await asyncio.sleep(2)
        await show_bulk_panel(update, context, query)
        return
    
    if data == "bulk_clear_warns":
        conn = get_db()
        conn.execute("UPDATE users SET warnings = 0")
        conn.commit()
        conn.close()
        await query.edit_message_text("✅ تم حذف جميع التحذيرات")
        await context.bot.send_message(GROUP_ID, "🗑 تم حذف جميع التحذيرات\n👮 بواسطة: المالك")
        await asyncio.sleep(2)
        await show_bulk_panel(update, context, query)
        return
    
    if data == "bulk_reset_economy":
        conn = get_db()
        conn.execute("UPDATE users SET balance = 1000, level = 1, messages = 0")
        conn.commit()
        conn.close()
        await query.edit_message_text("✅ تم إعادة ضبط الاقتصاد")
        await context.bot.send_message(GROUP_ID, "💰 تم إعادة ضبط الاقتصاد (الرصيد 1000، المستوى 1)\n👮 بواسطة: المالك")
        await asyncio.sleep(2)
        await show_bulk_panel(update, context, query)
        return
    
    # ========== إعلان متحرك ==========
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
    
    # ========== السجلات ==========
    if data == "owner_logs":
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
        return
    
    # ========== الأعضاء ==========
    if data == "owner_users":
        await show_users_list(update, context, query, 0)
        return
    
    if data.startswith("users_page_"):
        page = int(data.split("_")[2])
        await show_users_list(update, context, query, page)
        return
    
    if data.startswith("user_actions_"):
        target_id = int(data.split("_")[2])
        await show_user_details(update, context, query, target_id)
        return
    
    if data.startswith("user_action_"):
        parts = data.split("_")
        action = parts[2]
        target_id = int(parts[3])
        await execute_user_action(update, context, query, target_id, action)
        return
    
    if data.startswith("user_logs_"):
        target_id = int(data.split("_")[2])
        await show_user_logs(update, context, query, target_id, 0)
        return
    
    if data.startswith("user_logs_page_"):
        parts = data.split("_")
        target_id = int(parts[3])
        page = int(parts[4])
        await show_user_logs(update, context, query, target_id, page)
        return
    
    # ========== رجوع ==========
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

# ==================== دوال المساعدة ====================

async def show_admins_panel(update, context, query):
    admins = get_all_admins()
    
    text = "📋 قائمة المشرفين:\n\n"
    for a in admins:
        role = "👑 مشرف إداري" if a["is_super_admin"] else "🛡️ مشرف عادي"
        text += f"• {a['username'] or a['user_id']} - {role}\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مشرف جديد", callback_data="admin_add_user")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]
    ]
    
    for a in admins:
        name = a["username"] or str(a["user_id"])
        keyboard.insert(-1, [InlineKeyboardButton(f"➖ إزالة {name}", callback_data=f"admin_remove_{a['user_id']}")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_users_for_admin(update, context, query, page):
    users_per_page = 10
    offset = page * users_per_page
    
    conn = get_db()
    cursor = conn.execute("SELECT user_id, first_name, username FROM users LIMIT ? OFFSET ?", (users_per_page, offset))
    users = cursor.fetchall()
    
    cursor = conn.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    conn.close()
    
    text = f"👥 اختر عضواً (الصفحة {page + 1})\n\n"
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
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_admin_type_select(update, context, query, target_id):
    conn = get_db()
    cursor = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,))
    user = cursor.fetchone()
    conn.close()
    
    name = user["first_name"] if user else str(target_id)
    
    keyboard = [
        [InlineKeyboardButton("🛡️ مشرف عادي", callback_data=f"admin_set_{target_id}_normal")],
        [InlineKeyboardButton("👑 مشرف إداري", callback_data=f"admin_set_{target_id}_super")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_admins")]
    ]
    await query.edit_message_text(f"👤 {name}\n\nاختر نوع المشرف:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_shop_panel(update, context, query):
    keyboard = [
        [InlineKeyboardButton("📋 عرض الألقاب", callback_data="shop_view")],
        [InlineKeyboardButton("➕ إضافة لقب جديد", callback_data="shop_add")],
        [InlineKeyboardButton("✏️ تعديل لقب", callback_data="shop_edit")],
        [InlineKeyboardButton("🗑 حذف لقب", callback_data="shop_delete")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]
    ]
    await query.edit_message_text("🛒 إدارة السوق", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_shop_items(update, context, query):
    text = "🏷️ الألقاب الحالية:\n\n"
    for tid, title in TITLES.items():
        text += f"{tid}. {title['name']} - {title['price']} 🪙\n"
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="owner_shop")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_shop_edit_list(update, context, query):
    keyboard = []
    for tid, title in TITLES.items():
        keyboard.append([InlineKeyboardButton(title['name'], callback_data=f"shop_edit_title_{tid}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="owner_shop")])
    await query.edit_message_text("✏️ اختر اللقب لتعديله:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_shop_delete_list(update, context, query):
    keyboard = []
    for tid, title in TITLES.items():
        keyboard.append([InlineKeyboardButton(title['name'], callback_data=f"shop_delete_title_{tid}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="owner_shop")])
    await query.edit_message_text("🗑 اختر اللقب للحذف:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_warnings_panel(update, context, query):
    keyboard = [
        [InlineKeyboardButton("📋 قائمة المنذرين", callback_data="warnings_list")],
        [InlineKeyboardButton("⚙️ إعدادات التحذيرات", callback_data="warn_settings")],
        [InlineKeyboardButton("📢 تحذير للجميع", callback_data="warn_all")],
        [InlineKeyboardButton("🗑 حذف كل التحذيرات", callback_data="bulk_clear_warns")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]
    ]
    await query.edit_message_text("⚠️ إدارة التحذيرات", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_warnings_list(update, context, query):
    conn = get_db()
    cursor = conn.execute("SELECT user_id, first_name, username, warnings FROM users WHERE warnings > 0 ORDER BY warnings DESC")
    warned = cursor.fetchall()
    conn.close()
    
    if not warned:
        await query.edit_message_text("✅ لا يوجد أعضاء لديهم تحذيرات")
        return
    
    keyboard = []
    for w in warned:
        name = w["first_name"] or w["username"] or str(w["user_id"])
        keyboard.append([InlineKeyboardButton(f"{name} - {w['warnings']}", callback_data=f"warn_user_{w['user_id']}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="owner_warnings")])
    await query.edit_message_text("⚠️ قائمة المنذرين:", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_user_warnings(update, context, query, target_id):
    conn = get_db()
    cursor = conn.execute("SELECT first_name, warnings FROM users WHERE user_id = ?", (target_id,))
    user = cursor.fetchone()
    conn.close()
    
    name = user["first_name"] if user else str(target_id)
    warnings = user["warnings"] if user else 0
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة تحذير", callback_data=f"warn_add_{target_id}")],
        [InlineKeyboardButton("➖ حذف تحذير", callback_data=f"warn_remove_{target_id}")],
        [InlineKeyboardButton("🗑 حذف الكل", callback_data=f"warn_clear_{target_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="warnings_list")]
    ]
    await query.edit_message_text(f"👤 {name}\n⚠️ التحذيرات: {warnings}", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_bulk_panel(update, context, query):
    keyboard = [
        [InlineKeyboardButton("🔓 فك الكتم للجميع", callback_data="bulk_unmute")],
        [InlineKeyboardButton("🔓 فك الحظر للجميع", callback_data="bulk_unban")],
        [InlineKeyboardButton("🗑 حذف كل التحذيرات", callback_data="bulk_clear_warns")],
        [InlineKeyboardButton("💰 إعادة ضبط الاقتصاد", callback_data="bulk_reset_economy")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]
    ]
    await query.edit_message_text("🧹 العمليات الجماعية\n⚠️ لا يمكن التراجع عنها", reply_markup=InlineKeyboardMarkup(keyboard))

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

async def show_user_details(update, context, query, target_id):
    conn = get_db()
    cursor = conn.execute("SELECT balance, warnings, messages, level, title, first_name, username FROM users WHERE user_id = ?", (target_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        await query.edit_message_text("❌ العضو غير موجود")
        return
    
    name = user["first_name"] or user["username"] or str(target_id)
    title_text = f"🏆 {user['title']}" if user['title'] else ""
    
    text = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"👤 {name}\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += f"💰 الرصيد: {user['balance']} 🪙\n"
    text += f"⚠️ التحذيرات: {user['warnings']}\n"
    text += f"📨 الرسائل: {user['messages']}\n"
    text += f"🎖️ المستوى: {user['level']}\n"
    text += f"{title_text}\n\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"🔧 الإجراءات:\n"
    
    keyboard = [
        [InlineKeyboardButton("🔇 كتم", callback_data=f"user_action_mute_{target_id}"), InlineKeyboardButton("🔓 فك كتم", callback_data=f"user_action_unmute_{target_id}")],
        [InlineKeyboardButton("🚫 حظر", callback_data=f"user_action_ban_{target_id}"), InlineKeyboardButton("🔓 فك حظر", callback_data=f"user_action_unban_{target_id}")],
        [InlineKeyboardButton("⚠️ تحذير", callback_data=f"user_action_warn_{target_id}"), InlineKeyboardButton("🗑 حذف تحذير", callback_data=f"user_action_unwarn_{target_id}")],
        [InlineKeyboardButton("💰 خصم", callback_data=f"user_action_deduct_{target_id}"), InlineKeyboardButton("🎁 مكافأة", callback_data=f"user_action_reward_{target_id}")],
        [InlineKeyboardButton("📜 سجل العمليات", callback_data=f"user_logs_{target_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_users")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def execute_user_action(update, context, query, target_id, action):
    admin_name = update.effective_user.first_name
    
    conn = get_db()
    cursor = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,))
    target = cursor.fetchone()
    conn.close()
    
    target_name = target["first_name"] if target else str(target_id)
    
    if action == "mute":
        await query.edit_message_text(f"🔇 أرسل مدة الكتم لـ {target_name} (مثال: 10د):")
        context.user_data['waiting_mute_duration'] = target_id
        return
    
    elif action == "unmute":
        await unmute_user(context, target_id)
        await query.edit_message_text(f"✅ تم فك الكتم عن {target_name}")
        await context.bot.send_message(GROUP_ID, f"🔓 فك كتم\n\n👤 {target_name}\n\n👮 بواسطة: {admin_name}")
    
    elif action == "ban":
        await query.edit_message_text(f"🚫 أرسل سبب حظر {target_name}:")
        context.user_data['waiting_ban_reason'] = target_id
        return
    
    elif action == "unban":
        try:
            await context.bot.unban_chat_member(GROUP_ID, target_id)
        except:
            pass
        conn = get_db()
        conn.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
        conn.commit()
        conn.close()
        await query.edit_message_text(f"✅ تم فك الحظر عن {target_name}")
        await context.bot.send_message(GROUP_ID, f"🔓 فك حظر\n\n👤 {target_name}\n\n👮 بواسطة: {admin_name}")
    
    elif action == "warn":
        await query.edit_message_text(f"⚠️ أرسل سبب تحذير {target_name}:")
        context.user_data['waiting_warn_reason'] = target_id
        return
    
    elif action == "unwarn":
        conn = get_db()
        conn.execute("UPDATE users SET warnings = warnings - 1 WHERE user_id = ? AND warnings > 0", (target_id,))
        cursor = conn.execute("SELECT warnings FROM users WHERE user_id = ?", (target_id,))
        warnings = cursor.fetchone()["warnings"]
        conn.commit()
        conn.close()
        await query.edit_message_text(f"✅ تم حذف تحذير من {target_name}\n⚠️ العدد: {warnings}")
    
    elif action == "deduct":
        await query.edit_message_text(f"💰 أرسل المبلغ المراد خصمه من {target_name}:")
        context.user_data['waiting_deduct_amount'] = target_id
        return
    
    elif action == "reward":
        await query.edit_message_text(f"🎁 أرسل المبلغ المراد إضافته لـ {target_name}:")
        context.user_data['waiting_reward_amount'] = target_id
        return
    
    await asyncio.sleep(2)
    await show_user_details(update, context, query, target_id)

async def show_user_logs(update, context, query, target_id, page):
    logs_per_page = 5
    offset = page * logs_per_page
    
    conn = get_db()
    cursor = conn.execute("SELECT * FROM logs WHERE target_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?", (target_id, logs_per_page, offset))
    logs = cursor.fetchall()
    
    cursor = conn.execute("SELECT COUNT(*) FROM logs WHERE target_id = ?", (target_id,))
    total = cursor.fetchone()[0]
    conn.close()
    
    if not logs:
        await query.edit_message_text("📜 لا توجد سجلات لهذا العضو")
        return
    
    text = f"📜 سجل العمليات (الصفحة {page + 1})\n\n"
    for log in logs:
        text += f"• {log['action']} - {log['reason']}\n"
        text += f"  👮 {log['admin_name']} - 🕐 {time.strftime('%Y-%m-%d %H:%M', time.localtime(log['timestamp']))}\n\n"
    
    keyboard = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"user_logs_page_{target_id}_{page-1}"))
    if (page + 1) * logs_per_page < total:
        nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"user_logs_page_{target_id}_{page+1}"))
    if nav:
        keyboard.append(nav)
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"user_actions_{target_id}")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ==================== معالج الإدخالات ====================

async def handle_owner_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        return
    
    text = update.message.text.strip()
    
    # إضافة لقب - انتظار الاسم
    if context.user_data.get('waiting_shop_name'):
        context.user_data['new_shop_name'] = text
        await update.message.reply_text("💰 أرسل سعر اللقب:")
        context.user_data['waiting_shop_price'] = True
        context.user_data['waiting_shop_name'] = False
        return
    
    # إضافة لقب - انتظار السعر
    if context.user_data.get('waiting_shop_price'):
        try:
            price = int(text)
            name = context.user_data.get('new_shop_name')
            new_id = max(TITLES.keys()) + 1 if TITLES else 1
            TITLES[new_id] = {"name": name, "price": price}
            await update.message.reply_text(f"✅ تم إضافة: {name} - {price} 🪙")
        except:
            await update.message.reply_text("❌ السعر يجب أن يكون رقماً")
        context.user_data['waiting_shop_price'] = False
        context.user_data['new_shop_name'] = None
        return
    
    # تعديل لقب - انتظار الاسم
    if context.user_data.get('waiting_edit_name'):
        if text:
            context.user_data['new_edit_name'] = text
        await update.message.reply_text("💰 أرسل السعر الجديد:")
        context.user_data['waiting_edit_price'] = True
        context.user_data['waiting_edit_name'] = False
        return
    
    # تعديل لقب - انتظار السعر
    if context.user_data.get('waiting_edit_price'):
        title_id = context.user_data.get('editing_title_id')
        if title_id and title_id in TITLES:
            if text:
                try:
                    TITLES[title_id]["price"] = int(text)
                except:
                    pass
            if context.user_data.get('new_edit_name'):
                TITLES[title_id]["name"] = context.user_data.get('new_edit_name')
            await update.message.reply_text("✅ تم تعديل اللقب")
        context.user_data['waiting_edit_price'] = False
        context.user_data['editing_title_id'] = None
        context.user_data['new_edit_name'] = None
        return
    
    # تحذير للجميع
    if context.user_data.get('waiting_warn_all'):
        await context.bot.send_message(GROUP_ID, f"⚠️ تحذير عام\n\n📝 {text}\n\n👮 صادر عن: المالك")
        await update.message.reply_text("✅ تم الإرسال")
        context.user_data['waiting_warn_all'] = False
        return
    
    # تحذير فردي
    if context.user_data.get('waiting_warn_reason'):
        target_id = context.user_data['waiting_warn_reason']
        conn = get_db()
        conn.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (target_id,))
        cursor = conn.execute("SELECT warnings, first_name FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.commit()
        conn.close()
        await context.bot.send_message(GROUP_ID, f"⚠️ تحذير\n\n👤 {user['first_name']}\n📝 {text}\n🔢 {user['warnings']}\n\n👮 بواسطة: المالك")
        await update.message.reply_text(f"✅ تم الإضافة\n⚠️ العدد: {user['warnings']}")
        context.user_data['waiting_warn_reason'] = None
        return
    
    # خصم
    if context.user_data.get('waiting_deduct_amount'):
        try:
            amount = int(text)
            target_id = context.user_data['waiting_deduct_amount']
            conn = get_db()
            conn.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, target_id))
            cursor = conn.execute("SELECT balance, first_name FROM users WHERE user_id = ?", (target_id,))
            user = cursor.fetchone()
            conn.commit()
            conn.close()
            await context.bot.send_message(GROUP_ID, f"💰 خصم\n\n👤 {user['first_name']}\n💰 -{amount} عملة\n💵 الرصيد الجديد: {user['balance']}\n\n👮 بواسطة: المالك")
            await update.message.reply_text(f"✅ تم خصم {amount}")
        except:
            await update.message.reply_text("❌ خطأ")
        context.user_data['waiting_deduct_amount'] = None
        return
    
    # مكافأة
    if context.user_data.get('waiting_reward_amount'):
        try:
            amount = int(text)
            target_id = context.user_data['waiting_reward_amount']
            conn = get_db()
            conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
            cursor = conn.execute("SELECT balance, first_name FROM users WHERE user_id = ?", (target_id,))
            user = cursor.fetchone()
            conn.commit()
            conn.close()
            await context.bot.send_message(GROUP_ID, f"🎁 مكافأة\n\n👤 {user['first_name']}\n💰 +{amount} عملة\n💵 الرصيد الجديد: {user['balance']}\n\n👮 بواسطة: المالك")
            await update.message.reply_text(f"✅ تم إضافة {amount}")
        except:
            await update.message.reply_text("❌ خطأ")
        context.user_data['waiting_reward_amount'] = None
        return
    
    # إعلان متحرك - ملف
    if context.user_data.get('waiting_broadcast_media'):
        if update.message.animation or update.message.document or update.message.sticker or update.message.video:
            context.user_data['broadcast_media'] = update.message
            await update.message.reply_text("✏️ أرسل نص الإعلان:")
            context.user_data['waiting_broadcast_text'] = True
            context.user_data['waiting_broadcast_media'] = False
        else:
            await update.message.reply_text("❌ أرسل ملف متحرك")
        return
    
    # إعلان متحرك - نص
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
            await update.message.reply_text("✅ تم الإرسال")
        except Exception as e:
            await update.message.reply_text(f"❌ فشل: {e}")
        
        context.user_data['broadcast_media'] = None
        context.user_data['waiting_broadcast_text'] = False
        return
    
    # كتم - مدة
    if context.user_data.get('waiting_mute_duration'):
        target_id = context.user_data['waiting_mute_duration']
        duration_str = text
        mute_durations = {"1د": 60, "5د": 300, "10د": 600, "30د": 1800, "1س": 3600, "يوم": 86400}
        duration = mute_durations.get(duration_str, 300)
        
        try:
            await context.bot.restrict_chat_member(GROUP_ID, target_id, permissions=telegram.ChatPermissions(can_send_messages=False))
        except:
            pass
        
        conn = get_db()
        conn.execute("UPDATE users SET is_muted = 1, muted_until = ? WHERE user_id = ?", (int(time.time()) + duration, target_id))
        cursor = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.commit()
        conn.close()
        
        await context.bot.send_message(GROUP_ID, f"🔇 كتم\n\n👤 {user['first_name']}\n⏱️ {duration_str}\n\n👮 بواسطة: المالك")
        await update.message.reply_text(f"✅ تم كتم {user['first_name']}")
        context.user_data['waiting_mute_duration'] = None
        return
    
    # حظر - سبب
    if context.user_data.get('waiting_ban_reason'):
        target_id = context.user_data['waiting_ban_reason']
        reason = text
        
        try:
            await context.bot.ban_chat_member(GROUP_ID, target_id)
        except:
            pass
        
        conn = get_db()
        conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,))
        cursor = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.commit()
        conn.close()
        
        await context.bot.send_message(GROUP_ID, f"🚫 حظر\n\n👤 {user['first_name']}\n📝 {reason}\n\n👮 بواسطة: المالك")
        await update.message.reply_text(f"✅ تم حظر {user['first_name']}")
        context.user_data['waiting_ban_reason'] = None
        return

# ==================== معالج الأزرار الإضافية للمشرفين ====================

async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        mute_durations = {"1د": 60, "5د": 300, "10د": 600, "30د": 1800, "1س": 3600, "يوم": 86400}
        duration = mute_durations.get(duration_str, 300)
        
        try:
            await context.bot.restrict_chat_member(GROUP_ID, target_id, permissions=telegram.ChatPermissions(can_send_messages=False))
        except:
            pass
        
        conn = get_db()
        conn.execute("UPDATE users SET is_muted = 1, muted_until = ? WHERE user_id = ?", (int(time.time()) + duration, target_id))
        cursor = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.commit()
        conn.close()
        await context.bot.send_message(GROUP_ID, f"🔇 كتم\n\n👤 {user['first_name']}\n⏱️ {duration_str}\n\n👮 بواسطة: {update.effective_user.first_name}")
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