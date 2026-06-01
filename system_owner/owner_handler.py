from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_owner, add_admin, remove_admin, get_all_admins
from system_punishments.punishments_handler import unmute_user
from config import GROUP_ID

async def owner_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        await update.message.reply_text("❌ هذه اللوحة للمالك فقط")
        return
    
    keyboard = [
        [InlineKeyboardButton("👥 إدارة المشرفين", callback_data="owner_admins")],
        [InlineKeyboardButton("🛒 إدارة السوق", callback_data="owner_shop")],
        [InlineKeyboardButton("🧹 عمليات جماعية", callback_data="owner_bulk")],
        [InlineKeyboardButton("📢 تنبيه جماعي", callback_data="owner_broadcast")],
        [InlineKeyboardButton("📊 السجلات", callback_data="owner_logs")],
        [InlineKeyboardButton("🔙 إغلاق", callback_data="owner_close")]
    ]
    
    await update.message.reply_text(
        "👑 **لوحة المالك**\n\nاختر الإجراء:",
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
        await show_admins_list(update, context, query)
        return
    
    if data == "owner_shop":
        await show_shop_management(update, context, query)
        return
    
    if data == "owner_bulk":
        keyboard = [
            [InlineKeyboardButton("🔓 فك الكتم للجميع", callback_data="owner_unmute_all")],
            [InlineKeyboardButton("🗑 حذف كل التحذيرات", callback_data="owner_clear_warnings")],
            [InlineKeyboardButton("💰 إعادة ضبط الاقتصاد", callback_data="owner_reset_economy")],
            [InlineKeyboardButton("🎮 إعادة ضبط الألعاب", callback_data="owner_reset_games")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]
        ]
        await query.edit_message_text("🧹 **العمليات الجماعية**\n⚠️ هذه العمليات لا يمكن التراجع عنها", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    if data == "owner_broadcast":
        await query.edit_message_text("📢 أرسل الرسالة التي تريد إرسالها للجميع")
        context.user_data['waiting_broadcast'] = True
        return
    
    if data == "owner_logs":
        conn = get_db()
        cursor = conn.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 30")
        logs = cursor.fetchall()
        conn.close()
        
        if not logs:
            text = "📊 **السجلات**\n\nلا توجد سجلات حالياً"
        else:
            text = "📊 **آخر 30 عملية:**\n\n"
            for log in logs:
                text += f"• {log['action']} - {log['target_name'] or log['target_id']}\n"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
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
    
    if data == "owner_reset_economy":
        conn = get_db()
        conn.execute("UPDATE users SET balance = 1000, level = 1, messages = 0")
        conn.commit()
        conn.close()
        await query.edit_message_text("✅ **تم إعادة ضبط الاقتصاد**")
        return
    
    if data == "owner_reset_games":
        conn = get_db()
        conn.execute("DELETE FROM game_stats")
        conn.commit()
        conn.close()
        await query.edit_message_text("✅ **تم إعادة ضبط الألعاب**")
        return
    
    if data == "owner_back":
        keyboard = [
            [InlineKeyboardButton("👥 إدارة المشرفين", callback_data="owner_admins")],
            [InlineKeyboardButton("🛒 إدارة السوق", callback_data="owner_shop")],
            [InlineKeyboardButton("🧹 عمليات جماعية", callback_data="owner_bulk")],
            [InlineKeyboardButton("📢 تنبيه جماعي", callback_data="owner_broadcast")],
            [InlineKeyboardButton("📊 السجلات", callback_data="owner_logs")],
            [InlineKeyboardButton("🔙 إغلاق", callback_data="owner_close")]
        ]
        await query.edit_message_text("👑 **لوحة المالك**\n\nاختر الإجراء:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return
    
    # إدارة المشرفين - عرض قائمة الأعضاء
    if data.startswith("admin_list_"):
        page = int(data.split("_")[2])
        await show_users_list(update, context, query, page)
        return
    
    if data.startswith("admin_add_"):
        target_id = int(data.split("_")[2])
        await show_admin_type_selection(update, context, query, target_id)
        return
    
    if data.startswith("admin_remove_"):
        target_id = int(data.split("_")[2])
        remove_admin(target_id)
        await query.edit_message_text(f"✅ تم إزالة المستخدم من المشرفين")
        await show_admins_list(update, context, query)
        return
    
    if data.startswith("admin_type_"):
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
        await show_admins_list(update, context, query)
        return

async def show_admins_list(update, context, query):
    conn = get_db()
    cursor = conn.execute("SELECT user_id, username, first_name, is_super_admin FROM admins")
    admins = cursor.fetchall()
    conn.close()
    
    text = "📋 **قائمة المشرفين الحاليين:**\n\n"
    for a in admins:
        role = "👑 مشرف إداري" if a["is_super_admin"] else "🛡️ مشرف عادي"
        name = a["first_name"] or a["username"] or str(a["user_id"])
        text += f"• {name} - {role}\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مشرف جديد", callback_data="admin_add_new")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_users_list(update, context, query, page=0):
    conn = get_db()
    cursor = conn.execute("SELECT user_id, username, first_name FROM users LIMIT 10 OFFSET ?", (page * 10,))
    users = cursor.fetchall()
    
    cursor = conn.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    conn.close()
    
    if not users:
        await query.edit_message_text("❌ لا يوجد أعضاء")
        return
    
    text = "👥 **قائمة الأعضاء:**\n\n"
    buttons = []
    
    for u in users:
        name = u["first_name"] or u["username"] or str(u["user_id"])
        buttons.append([InlineKeyboardButton(f"👤 {name}", callback_data=f"admin_add_{u['user_id']}")])
    
    # أزرار التنقل
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"admin_list_{page-1}"))
    if (page + 1) * 10 < total:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"admin_list_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="owner_admins")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

async def show_admin_type_selection(update, context, query, target_id):
    conn = get_db()
    cursor = conn.execute("SELECT first_name, username FROM users WHERE user_id = ?", (target_id,))
    user = cursor.fetchone()
    conn.close()
    
    name = user["first_name"] or user["username"] or str(target_id) if user else str(target_id)
    
    keyboard = [
        [InlineKeyboardButton("🛡️ مشرف عادي", callback_data=f"admin_type_{target_id}_normal")],
        [InlineKeyboardButton("👑 مشرف إداري", callback_data=f"admin_type_{target_id}_super")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_admins")]
    ]
    
    await query.edit_message_text(f"👤 **{name}**\n\nاختر نوع المشرف:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_shop_management(update, context, query):
    conn = get_db()
    cursor = conn.execute("SELECT title FROM user_titles GROUP BY title")
    titles = cursor.fetchall()
    conn.close()
    
    text = "🛒 **إدارة السوق (المتجر)**\n\n"
    text += "**الألقاب المتوفرة:**\n"
    
    all_titles = {
        1: {"name": "عضو جديد 🌱", "price": 1000},
        2: {"name": "مقاتل ⚔️", "price": 2500},
        3: {"name": "ملك 👑", "price": 5000},
        4: {"name": "VIP 💎", "price": 10000},
        5: {"name": "أسطوري 🔥", "price": 20000},
    }
    
    for tid, title in all_titles.items():
        text += f"• {title['name']} - {title['price']} 🪙\n"
    
    text += "\n📌 **للشراء:** اذهب إلى المجموعة واكتب `/shop`"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_owner_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not is_owner(user_id):
        return
    
    text = update.message.text.strip()
    
    if context.user_data.get('waiting_broadcast'):
        # إرسال رسالة جماعية
        conn = get_db()
        cursor = conn.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        conn.close()
        
        sent = 0
        for u in users:
            try:
                await context.bot.send_message(u["user_id"], f"📢 **إعلان من المالك**\n\n{text}", parse_mode="Markdown")
                sent += 1
            except:
                pass
        
        await update.message.reply_text(f"✅ تم إرسال الإعلان إلى {sent} عضو")
        context.user_data['waiting_broadcast'] = False