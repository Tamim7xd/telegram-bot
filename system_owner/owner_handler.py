import time
import asyncio
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.permissions import is_owner, is_admin, add_admin, remove_admin, get_all_admins
from system_punishments.punishments_handler import unmute_user
from config import GROUP_ID, OWNER_ID, MAX_WARNINGS

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
        await show_user_details_for_admin(update, context, query, target_id)
        return
    if data.startswith("admin_promote_"):
        target_id = int(data.split("_")[2])
        await promote_to_super_admin(update, context, query, target_id)
        return
    if data.startswith("admin_demote_"):
        target_id = int(data.split("_")[2])
        await demote_from_super_admin(update, context, query, target_id)
        return
    if data.startswith("admin_remove_"):
        target_id = int(data.split("_")[2])
        conn = get_db()
        user = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
        conn.close()
        name = user["first_name"] if user else str(target_id)
        remove_admin(target_id)
        await query.edit_message_text(f"✅ تم إزالة {name} من المشرفين")
        await asyncio.sleep(2)
        await show_admins_list(update, context, query)
        return
    if data.startswith("admin_page_"):
        page = int(data.split("_")[2])
        await show_users_for_admin(update, context, query, page)
        return
    if data.startswith("admin_set_"):
        parts = data.split("_")
        target_id = int(parts[2])
        is_super = parts[3] == "super"
        conn = get_db()
        user = conn.execute("SELECT username, first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
        conn.close()
        username = user["username"] if user else str(target_id)
        name = user["first_name"] if user else str(target_id)
        add_admin(target_id, username, is_super)
        role = "مشرف إداري 👑" if is_super else "مشرف عادي 🛡️"
        await query.edit_message_text(f"✅ تم تعيين {name} كـ {role}")
        await asyncio.sleep(2)
        await show_admins_list(update, context, query)
        return
    
    # ========== إدارة السوق ==========
    if data == "owner_shop":
        await show_shop_panel(update, context, query)
        return
    if data == "shop_view":
        await show_shop_items(update, context, query)
        return
    if data == "shop_add":
        await query.edit_message_text("✏️ أرسل اسم اللقب الجديد:")
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
        keyboard = [[InlineKeyboardButton("✅ نعم، احذف", callback_data=f"shop_confirm_delete_{title_id}")], [InlineKeyboardButton("🔙 رجوع", callback_data="owner_shop")]]
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
        user = conn.execute("SELECT warnings, first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
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
        user = conn.execute("SELECT warnings, first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
        conn.commit()
        conn.close()
        await query.edit_message_text(f"✅ تم حذف تحذير\n👤 {user['first_name']}\n⚠️ العدد: {user['warnings']}")
        await asyncio.sleep(2)
        await show_warnings_panel(update, context, query)
        return
    if data.startswith("warn_clear_"):
        target_id = int(data.split("_")[2])
        conn = get_db()
        user = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
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
        muted = conn.execute("SELECT user_id FROM users WHERE is_muted = 1").fetchall()
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
        banned = conn.execute("SELECT user_id FROM users WHERE is_banned = 1").fetchall()
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
        keyboard = [[InlineKeyboardButton("📤 إرسال ملصق/صورة متحركة", callback_data="broadcast_media")], [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]]
        await query.edit_message_text("🎬 إعلان متحرك", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if data == "broadcast_media":
        await query.edit_message_text("📤 أرسل الملصق أو الصورة المتحركة:\n(ملصق متحرك - GIF - فيديو قصير)")
        context.user_data['waiting_broadcast_media'] = True
        return
    
    # ========== السجلات ==========
    if data == "owner_logs":
        conn = get_db()
        logs = conn.execute("SELECT * FROM logs ORDER BY timestamp DESC LIMIT 30").fetchall()
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
    if data.startswith("user_details_"):
        target_id = int(data.split("_")[2])
        await show_user_full_details(update, context, query, target_id)
        return
    
    # ========== أزرار إجراءات الأعضاء ==========
    if data.startswith("user_action_mute_"):
        target_id = int(data.split("_")[3])
        await query.edit_message_text(f"🔇 أرسل مدة الكتم (مثال: 10د):")
        context.user_data['mute_target'] = target_id
        return
    if data.startswith("user_action_unmute_"):
        target_id = int(data.split("_")[3])
        await unmute_user(context, target_id)
        await query.edit_message_text("✅ تم فك الكتم")
        await asyncio.sleep(2)
        await show_user_full_details(update, context, query, target_id)
        return
    if data.startswith("user_action_ban_"):
        target_id = int(data.split("_")[3])
        await query.edit_message_text(f"🚫 أرسل سبب الحظر:")
        context.user_data['ban_target'] = target_id
        return
    if data.startswith("user_action_unban_"):
        target_id = int(data.split("_")[3])
        try:
            await context.bot.unban_chat_member(GROUP_ID, target_id)
        except:
            pass
        conn = get_db()
        conn.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (target_id,))
        conn.commit()
        conn.close()
        await query.edit_message_text("✅ تم فك الحظر")
        await asyncio.sleep(2)
        await show_user_full_details(update, context, query, target_id)
        return
    if data.startswith("user_action_warn_"):
        target_id = int(data.split("_")[3])
        await query.edit_message_text(f"⚠️ أرسل سبب التحذير:")
        context.user_data['warn_target'] = target_id
        return
    if data.startswith("user_action_unwarn_"):
        target_id = int(data.split("_")[3])
        conn = get_db()
        conn.execute("UPDATE users SET warnings = warnings - 1 WHERE user_id = ? AND warnings > 0", (target_id,))
        conn.commit()
        conn.close()
        await query.edit_message_text("✅ تم حذف آخر تحذير")
        await asyncio.sleep(2)
        await show_user_full_details(update, context, query, target_id)
        return
    if data.startswith("user_action_deduct_"):
        target_id = int(data.split("_")[3])
        await query.edit_message_text(f"💰 أرسل المبلغ المراد خصمه:")
        context.user_data['deduct_target'] = target_id
        return
    if data.startswith("user_action_reward_"):
        target_id = int(data.split("_")[3])
        await query.edit_message_text(f"🎁 أرسل المبلغ المراد إضافته:")
        context.user_data['reward_target'] = target_id
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
        return

# ==================== دوال مساعدة ====================

async def show_admins_list(update, context, query):
    admins = get_all_admins()
    if not admins:
        text = "📋 لا يوجد مشرفين حالياً"
    else:
        text = "📋 **قائمة المشرفين:**\n\n"
        for a in admins:
            role = "👑 مشرف إداري" if a["is_super_admin"] else "🛡️ مشرف عادي"
            conn = get_db()
            user = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (a["user_id"],)).fetchone()
            conn.close()
            name = user["first_name"] if user else a["username"] or str(a["user_id"])
            text += f"• {name} - {role}\n"
    keyboard = [[InlineKeyboardButton("➕ إضافة مشرف جديد", callback_data="admin_add_user")], [InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")]]
    for a in admins:
        if a["user_id"] != OWNER_ID:
            conn = get_db()
            user = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (a["user_id"],)).fetchone()
            conn.close()
            name = user["first_name"] if user else a["username"] or str(a["user_id"])
            keyboard.insert(-1, [InlineKeyboardButton(f"➖ إزالة {name}", callback_data=f"admin_remove_{a['user_id']}")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_users_for_admin(update, context, query, page):
    users_per_page = 10
    offset = page * users_per_page
    conn = get_db()
    users = conn.execute("SELECT user_id, first_name, username FROM users LIMIT ? OFFSET ?", (users_per_page, offset)).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    if not users:
        await query.edit_message_text("❌ لا يوجد أعضاء في قاعدة البيانات")
        return
    text = f"👥 **اختر عضواً** (الصفحة {page + 1} من {((total - 1) // users_per_page) + 1})\n\n"
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

async def show_user_details_for_admin(update, context, query, target_id):
    conn = get_db()
    user = conn.execute("SELECT user_id, first_name, username FROM users WHERE user_id = ?", (target_id,)).fetchone()
    admin_info = conn.execute("SELECT is_super_admin FROM admins WHERE user_id = ?", (target_id,)).fetchone()
    conn.close()
    if not user:
        await query.edit_message_text("❌ العضو غير موجود")
        return
    name = user["first_name"] or "مستخدم"
    username = user["username"] or "لا يوجد"
    is_super = admin_info["is_super_admin"] if admin_info else False
    text = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👤 **{name}**\n🆔 @{username}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    if admin_info:
        role = "👑 مشرف إداري" if is_super else "🛡️ مشرف عادي"
        text += f"📋 **حالة المشرف:** {role}\n\n"
    else:
        text += f"📋 **حالة المشرف:** ❌ ليس مشرفاً\n\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    keyboard = []
    if not admin_info:
        keyboard.append([InlineKeyboardButton("➕ تعيين مشرف عادي", callback_data=f"admin_set_{target_id}_normal")])
        keyboard.append([InlineKeyboardButton("👑 تعيين مشرف إداري", callback_data=f"admin_set_{target_id}_super")])
    else:
        if is_super:
            keyboard.append([InlineKeyboardButton("⬇️ خفض إلى مشرف عادي", callback_data=f"admin_demote_{target_id}")])
        else:
            keyboard.append([InlineKeyboardButton("⬆️ ترقية إلى مشرف إداري", callback_data=f"admin_promote_{target_id}")])
        keyboard.append([InlineKeyboardButton("🗑 إزالة من المشرفين", callback_data=f"admin_remove_{target_id}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_add_user")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def promote_to_super_admin(update, context, query, target_id):
    conn = get_db()
    user = conn.execute("SELECT username, first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
    conn.close()
    if user:
        add_admin(target_id, user["username"] or str(target_id), is_super=True)
        await query.edit_message_text(f"✅ تم ترقية {user['first_name']} إلى مشرف إداري 👑")
    else:
        await query.edit_message_text("❌ العضو غير موجود")
    await asyncio.sleep(2)
    await show_admins_list(update, context, query)

async def demote_from_super_admin(update, context, query, target_id):
    conn = get_db()
    user = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
    conn.close()
    if user:
        add_admin(target_id, str(target_id), is_super=False)
        await query.edit_message_text(f"✅ تم خفض {user['first_name']} إلى مشرف عادي 🛡️")
    else:
        await query.edit_message_text("❌ العضو غير موجود")
    await asyncio.sleep(2)
    await show_admins_list(update, context, query)

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
    text = "🏷️ **الألقاب الحالية:**\n\n"
    for tid, title in TITLES.items():
        text += f"{tid}. {title['name']} - {title['price']} 🪙\n"
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="owner_shop")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_shop_edit_list(update, context, query):
    keyboard = []
    for tid, title in TITLES.items():
        keyboard.append([InlineKeyboardButton(title['name'], callback_data=f"shop_edit_title_{tid}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="owner_shop")])
    await query.edit_message_text("✏️ **اختر اللقب لتعديله:**", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_shop_delete_list(update, context, query):
    keyboard = []
    for tid, title in TITLES.items():
        keyboard.append([InlineKeyboardButton(title['name'], callback_data=f"shop_delete_title_{tid}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="owner_shop")])
    await query.edit_message_text("🗑 **اختر اللقب للحذف:**", reply_markup=InlineKeyboardMarkup(keyboard))

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
    warned = conn.execute("SELECT user_id, first_name, username, warnings FROM users WHERE warnings > 0 ORDER BY warnings DESC").fetchall()
    conn.close()
    if not warned:
        await query.edit_message_text("✅ لا يوجد أعضاء لديهم تحذيرات")
        return
    keyboard = []
    for w in warned:
        name = w["first_name"] or w["username"] or str(w["user_id"])
        keyboard.append([InlineKeyboardButton(f"{name} - {w['warnings']}", callback_data=f"warn_user_{w['user_id']}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="owner_warnings")])
    await query.edit_message_text("⚠️ **قائمة المنذرين:**", reply_markup=InlineKeyboardMarkup(keyboard))

async def show_user_warnings(update, context, query, target_id):
    conn = get_db()
    user = conn.execute("SELECT first_name, warnings FROM users WHERE user_id = ?", (target_id,)).fetchone()
    conn.close()
    name = user["first_name"] if user else str(target_id)
    warnings = user["warnings"] if user else 0
    keyboard = [
        [InlineKeyboardButton("➕ إضافة تحذير", callback_data=f"warn_add_{target_id}")],
        [InlineKeyboardButton("➖ حذف تحذير", callback_data=f"warn_remove_{target_id}")],
        [InlineKeyboardButton("🗑 حذف الكل", callback_data=f"warn_clear_{target_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="warnings_list")]
    ]
    await query.edit_message_text(f"👤 **{name}**\n⚠️ التحذيرات: {warnings}", reply_markup=InlineKeyboardMarkup(keyboard))

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
    users = conn.execute("SELECT user_id, first_name, username FROM users LIMIT ? OFFSET ?", (users_per_page, offset)).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    if not users:
        await query.edit_message_text("❌ لا يوجد أعضاء في قاعدة البيانات")
        return
    text = f"👥 **قائمة الأعضاء** (الصفحة {page + 1} من {((total - 1) // users_per_page) + 1})\n\n"
    keyboard = []
    for u in users:
        name = u["first_name"] or u["username"] or str(u["user_id"])
        keyboard.append([InlineKeyboardButton(f"👤 {name}", callback_data=f"user_details_{u['user_id']}")])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"users_page_{page-1}"))
    if (page + 1) * users_per_page < total:
        nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"users_page_{page+1}"))
    if nav:
        keyboard.append(nav)
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="owner_back")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_user_full_details(update, context, query, target_id):
    conn = get_db()
    user = conn.execute("SELECT user_id, first_name, username, balance, warnings, messages, level, title FROM users WHERE user_id = ?", (target_id,)).fetchone()
    admin_info = conn.execute("SELECT is_super_admin FROM admins WHERE user_id = ?", (target_id,)).fetchone()
    conn.close()
    if not user:
        await query.edit_message_text("❌ العضو غير موجود")
        return
    name = user["first_name"] or "مستخدم"
    username = user["username"] or "لا يوجد"
    balance = user["balance"] or 1000
    warnings = user["warnings"] or 0
    messages = user["messages"] or 0
    level = user["level"] or 1
    title = user["title"] or "لا يوجد"
    is_super = admin_info["is_super_admin"] if admin_info else False
    admin_status = "👑 مشرف إداري" if is_super else ("🛡️ مشرف عادي" if admin_info else "❌ ليس مشرفاً")
    text = f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👤 **{name}**\n🆔 @{username}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n💰 الرصيد: {balance} 🪙\n⚠️ التحذيرات: {warnings}/{MAX_WARNINGS}\n📨 الرسائل: {messages}\n🎖️ المستوى: {level}\n🏆 اللقب: {title}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📋 **حالة المشرف:** {admin_status}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    keyboard = [
        [InlineKeyboardButton("🔇 كتم", callback_data=f"user_action_mute_{target_id}"), InlineKeyboardButton("🔓 فك كتم", callback_data=f"user_action_unmute_{target_id}")],
        [InlineKeyboardButton("🚫 حظر", callback_data=f"user_action_ban_{target_id}"), InlineKeyboardButton("🔓 فك حظر", callback_data=f"user_action_unban_{target_id}")],
        [InlineKeyboardButton("⚠️ تحذير", callback_data=f"user_action_warn_{target_id}"), InlineKeyboardButton("🗑 حذف تحذير", callback_data=f"user_action_unwarn_{target_id}")],
        [InlineKeyboardButton("💰 خصم", callback_data=f"user_action_deduct_{target_id}"), InlineKeyboardButton("🎁 مكافأة", callback_data=f"user_action_reward_{target_id}")],
        [InlineKeyboardButton("📜 سجل العمليات", callback_data=f"user_logs_{target_id}")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="owner_users")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_user_logs(update, context, query, target_id, page):
    logs_per_page = 5
    offset = page * logs_per_page
    conn = get_db()
    logs = conn.execute("SELECT * FROM logs WHERE target_id = ? ORDER BY timestamp DESC LIMIT ? OFFSET ?", (target_id, logs_per_page, offset)).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM logs WHERE target_id = ?", (target_id,)).fetchone()[0]
    user = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
    conn.close()
    name = user["first_name"] if user else str(target_id)
    if not logs:
        await query.edit_message_text(f"📜 لا توجد سجلات للعضو {name}")
        return
    text = f"📜 **سجل عمليات العضو {name}** (الصفحة {page + 1} من {((total - 1) // logs_per_page) + 1})\n\n"
    for log in logs:
        text += f"• **{log['action']}**\n  📝 {log['reason']}\n  👮 {log['admin_name']}\n  🕐 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(log['timestamp']))}\n\n"
    keyboard = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"user_logs_page_{target_id}_{page-1}"))
    if (page + 1) * logs_per_page < total:
        nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"user_logs_page_{target_id}_{page+1}"))
    if nav:
        keyboard.append(nav)
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"user_details_{target_id}")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# ==================== معالج الإدخالات ====================

async def handle_owner_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_owner(user_id):
        return
    text = update.message.text.strip()
    
    if context.user_data.get('waiting_shop_name'):
        context.user_data['new_shop_name'] = text
        await update.message.reply_text("💰 أرسل سعر اللقب:")
        context.user_data['waiting_shop_price'] = True
        context.user_data['waiting_shop_name'] = False
        return
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
    if context.user_data.get('waiting_edit_name'):
        if text:
            context.user_data['new_edit_name'] = text
        await update.message.reply_text("💰 أرسل السعر الجديد:")
        context.user_data['waiting_edit_price'] = True
        context.user_data['waiting_edit_name'] = False
        return
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
    if context.user_data.get('waiting_warn_all'):
        await context.bot.send_message(GROUP_ID, f"⚠️ تحذير عام\n\n📝 {text}\n\n👮 صادر عن: المالك")
        await update.message.reply_text("✅ تم الإرسال")
        context.user_data['waiting_warn_all'] = False
        return
    if context.user_data.get('mute_target'):
        target_id = context.user_data['mute_target']
        from system_punishments.punishments_handler import parse_duration, format_duration
        duration_seconds = parse_duration(text)
        duration_text = format_duration(duration_seconds)
        until_time = int(time.time()) + duration_seconds
        try:
            await context.bot.restrict_chat_member(GROUP_ID, target_id, permissions=telegram.ChatPermissions(can_send_messages=False))
        except:
            pass
        conn = get_db()
        conn.execute("UPDATE users SET is_muted = 1, muted_until = ? WHERE user_id = ?", (until_time, target_id))
        user = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
        conn.commit()
        conn.close()
        await context.bot.send_message(GROUP_ID, f"🔇 **كتم من المالك**\n\n👤 {user['first_name']}\n⏱️ {duration_text}\n📝 بقرار من المالك")
        await update.message.reply_text(f"✅ تم كتم العضو لمدة {duration_text}")
        context.user_data['mute_target'] = None
        return
    if context.user_data.get('ban_target'):
        target_id = context.user_data['ban_target']
        reason = text
        try:
            await context.bot.ban_chat_member(GROUP_ID, target_id)
        except:
            pass
        conn = get_db()
        conn.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (target_id,))
        user = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
        conn.commit()
        conn.close()
        await context.bot.send_message(GROUP_ID, f"🚫 **حظر من المالك**\n\n👤 {user['first_name']}\n📝 السبب: {reason}")
        await update.message.reply_text(f"✅ تم حظر {user['first_name']}")
        context.user_data['ban_target'] = None
        return
    if context.user_data.get('warn_target'):
        target_id = context.user_data['warn_target']
        reason = text
        conn = get_db()
        conn.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (target_id,))
        user = conn.execute("SELECT warnings, first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
        conn.commit()
        conn.close()
        await context.bot.send_message(GROUP_ID, f"⚠️ **تحذير من المالك**\n\n👤 {user['first_name']}\n📝 {reason}\n🔢 {user['warnings']}")
        await update.message.reply_text(f"✅ تم إضافة تحذير\n⚠️ العدد: {user['warnings']}")
        context.user_data['warn_target'] = None
        return
    if context.user_data.get('deduct_target'):
        try:
            amount = int(text)
            target_id = context.user_data['deduct_target']
            conn = get_db()
            conn.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, target_id))
            user = conn.execute("SELECT balance, first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
            conn.commit()
            conn.close()
            await context.bot.send_message(GROUP_ID, f"💰 **خصم من المالك**\n\n👤 {user['first_name']}\n💰 -{amount} عملة\n💵 الرصيد الجديد: {user['balance']}")
            await update.message.reply_text(f"✅ تم خصم {amount} عملة")
        except:
            await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً")
        context.user_data['deduct_target'] = None
        return
    if context.user_data.get('reward_target'):
        try:
            amount = int(text)
            target_id = context.user_data['reward_target']
            conn = get_db()
            conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
            user = conn.execute("SELECT balance, first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
            conn.commit()
            conn.close()
            await context.bot.send_message(GROUP_ID, f"🎁 **مكافأة من المالك**\n\n👤 {user['first_name']}\n💰 +{amount} عملة\n💵 الرصيد الجديد: {user['balance']}")
            await update.message.reply_text(f"✅ تم إضافة {amount} عملة")
        except:
            await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً")
        context.user_data['reward_target'] = None
        return
    if context.user_data.get('waiting_broadcast_media'):
        if update.message.animation or update.message.document or update.message.sticker or update.message.video:
            context.user_data['broadcast_media'] = update.message
            await update.message.reply_text("✏️ أرسل نص الإعلان:")
            context.user_data['waiting_broadcast_text'] = True
            context.user_data['waiting_broadcast_media'] = False
        else:
            await update.message.reply_text("❌ أرسل ملف متحرك (GIF، ملصق، فيديو)")
        return
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

# ==================== دوال الأزرار الإضافية للمشرفين ====================

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
    if context.user_data.get('admin_warn_target'):
        target_id = context.user_data['admin_warn_target']
        conn = get_db()
        conn.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (target_id,))
        user = conn.execute("SELECT warnings, first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
        conn.commit()
        conn.close()
        await context.bot.send_message(GROUP_ID, f"⚠️ تحذير\n\n👤 {user['first_name']}\n📝 {text}\n🔢 {user['warnings']}\n\n👮 بواسطة: {update.effective_user.first_name}")
        await update.message.reply_text(f"✅ تم")
        context.user_data['admin_warn_target'] = None
        return
    if context.user_data.get('admin_mute_target'):
        target_id = context.user_data['admin_mute_target']
        from system_punishments.punishments_handler import parse_duration, format_duration
        duration_seconds = parse_duration(text)
        duration_text = format_duration(duration_seconds)
        until_time = int(time.time()) + duration_seconds
        try:
            await context.bot.restrict_chat_member(GROUP_ID, target_id, permissions=telegram.ChatPermissions(can_send_messages=False))
        except:
            pass
        conn = get_db()
        conn.execute("UPDATE users SET is_muted = 1, muted_until = ? WHERE user_id = ?", (until_time, target_id))
        user = conn.execute("SELECT first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
        conn.commit()
        conn.close()
        await context.bot.send_message(GROUP_ID, f"🔇 كتم\n\n👤 {user['first_name']}\n⏱️ {duration_text}\n📝 {text}\n\n👮 بواسطة: {update.effective_user.first_name}")
        await update.message.reply_text(f"✅ تم")
        context.user_data['admin_mute_target'] = None
        return
    if context.user_data.get('admin_deduct_target'):
        try:
            amount = int(text)
            target_id = context.user_data['admin_deduct_target']
            conn = get_db()
            conn.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, target_id))
            user = conn.execute("SELECT balance, first_name FROM users WHERE user_id = ?", (target_id,)).fetchone()
            conn.commit()
            conn.close()
            await context.bot.send_message(GROUP_ID, f"💰 خصم\n\n👤 {user['first_name']}\n💰 -{amount}\n💵 {user['balance']}\n\n👮 بواسطة: {update.effective_user.first_name}")
            await update.message.reply_text(f"✅ تم")
        except:
            await update.message.reply_text("❌ خطأ")
        context.user_data['admin_deduct_target'] = None
        return
