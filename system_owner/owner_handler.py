# ==================== معالج الأزرار الإضافية لإدارة المشرفين ====================

async def handle_admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأزرار الإضافية التي تظهر في ملف العضو للمشرفين"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text("❌ ليس لديك صلاحية")
        return
    
    data = query.data
    
    if data.startswith("admin_warn_"):
        target_id = int(data.split("_")[2])
        await query.edit_message_text(f"⚠️ أرسل سبب التحذير للعضو:")
        context.user_data['admin_warn_target'] = target_id
        return
    
    if data.startswith("admin_mute_"):
        target_id = int(data.split("_")[2])
        await query.edit_message_text(f"🔇 أرسل مدة الكتم (مثال: 10د):")
        context.user_data['admin_mute_target'] = target_id
        return
    
    if data.startswith("admin_deduct_"):
        target_id = int(data.split("_")[2])
        await query.edit_message_text(f"💰 أرسل المبلغ المراد خصمه:")
        context.user_data['admin_deduct_target'] = target_id
        return
    
    if data == "close":
        await query.delete_message()
        return

async def handle_admin_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الإدخالات من الأزرار الإضافية"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if not is_admin(user_id):
        return
    
    # معالج التحذير
    if context.user_data.get('admin_warn_target'):
        target_id = context.user_data['admin_warn_target']
        conn = get_db()
        conn.execute("UPDATE users SET warnings = warnings + 1 WHERE user_id = ?", (target_id,))
        cursor = conn.execute("SELECT warnings, first_name FROM users WHERE user_id = ?", (target_id,))
        user = cursor.fetchone()
        conn.commit()
        conn.close()
        
        await context.bot.send_message(GROUP_ID, f"⚠️ **تحذير**\n\n👤 {user['first_name']}\n📝 {text}\n🔢 {user['warnings']}\n\n👮 بواسطة: {update.effective_user.first_name}", parse_mode="Markdown")
        await update.message.reply_text(f"✅ تم إضافة تحذير\n⚠️ العدد: {user['warnings']}")
        context.user_data['admin_warn_target'] = None
        return
    
    # معالج الكتم
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
        
        await context.bot.send_message(GROUP_ID, f"🔇 **كتم**\n\n👤 {user['first_name']}\n⏱️ {duration_str}\n\n👮 بواسطة: {update.effective_user.first_name}", parse_mode="Markdown")
        await update.message.reply_text(f"✅ تم كتم {user['first_name']} لمدة {duration_str}")
        context.user_data['admin_mute_target'] = None
        return
    
    # معالج الخصم
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
            
            await context.bot.send_message(GROUP_ID, f"💰 **خصم**\n\n👤 {user['first_name']}\n💰 -{amount} عملة\n💵 الرصيد الجديد: {user['balance']}\n\n👮 بواسطة: {update.effective_user.first_name}", parse_mode="Markdown")
            await update.message.reply_text(f"✅ تم خصم {amount} عملة")
        except:
            await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً")
        context.user_data['admin_deduct_target'] = None
        return