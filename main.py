import logging
import threading
import time
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN
from shared.database import init_db

from system_profile.profile_handler import profile_command
from system_games.games_handler import game_command, game_callback, handle_game_answer
from system_shop.shop_handler import shop_command, shop_callback
from system_warnings.warnings_handler import warning_command
from system_punishments.punishments_handler import mute_command, ban_command, kick_command, unmute_command, check_expired_mutes
from system_economy.economy_handler import add_balance_command, remove_balance_command, daily_reward_command
from system_admin.admin_handler import admin_panel_command, admin_callback
from system_owner.owner_handler import owner_panel_command, owner_callback, handle_owner_input, handle_admin_buttons, handle_admin_inputs
from system_backup.backup_handler import create_backup

logging.basicConfig(level=logging.INFO)

async def register_user(update: Update):
    """تسجيل المستخدم في قاعدة البيانات إذا لم يكن موجوداً"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "لا يوجد"
    first_name = update.effective_user.first_name or "مستخدم"
    
    from shared.database import get_db
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)", 
                 (user_id, username, first_name))
    conn.commit()
    conn.close()
    print(f"📝 Registered user: {first_name} (@{username}) - ID: {user_id}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await register_user(update)
    
    await update.message.reply_text(
        "✅ البوت يعمل!\n\n"
        "📋 الأوامر المتاحة:\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 أوامر عامة:\n"
        "#ملف - عرض ملفك الشخصي\n"
        "#لعبة - فتح الألعاب\n"
        "#سوق - فتح المتجر\n"
        "#يومي - مكافأة يومية\n\n"
        "🛡️ أوامر المشرفين:\n"
        "#تحذير سبب - تحذير عضو\n"
        "#كتم مدة سبب - كتم عضو\n"
        "#فك_كتم - فك الكتم عن عضو\n"
        "#خصم مبلغ سبب - خصم رصيد\n"
        "#مكافأة مبلغ سبب - إضافة رصيد\n"
        "#مشرف - لوحة المشرفين\n\n"
        "👑 أوامر المشرف الإداري:\n"
        "#حظر سبب - حظر عضو\n"
        "#طرد سبب - طرد عضو\n\n"
        "⭐ أوامر المالك:\n"
        "#مالك - لوحة المالك\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )

async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج جميع الرسائل النصية - يسجل المستخدم ثم يعالج الأوامر"""
    await register_user(update)
    
    text = update.message.text.strip()
    
    print(f"📩 Received from {update.effective_user.first_name}: {text}")
    
    # أوامر عامة
    if text in ["#ملف", "#ملفي", "#الملف", "#معلومات", "#معلوماتي", "#المعلومات"]:
        await profile_command(update, context)
        return
    
    if text in ["#لعبة", "#العاب", "#لعب", "#العب"]:
        await game_command(update, context)
        return
    
    if text in ["#سوق", "#محل", "#شراء", "#اشتري", "#اسواق", "#المتجر"]:
        await shop_command(update, context)
        return
    
    if text in ["#يومي", "#مكافأةيومية", "#يومية"]:
        await daily_reward_command(update, context)
        return
    
    if text in ["#مشرف", "#ادمن", "#الادمن"]:
        await admin_panel_command(update, context)
        return
    
    if text in ["#مالك", "#المالك"]:
        await owner_panel_command(update, context)
        return
    
    # أوامر تتطلب الرد
    if text.startswith("#تحذير"):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ يرجى الرد على رسالة العضو المستهدف")
            return
        parts = text.split(maxsplit=1)
        reason = parts[1] if len(parts) > 1 else "لا يوجد سبب"
        context.user_data['temp_reason'] = reason
        await warning_command(update, context)
        return
    
    if text.startswith("#كتم"):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ يرجى الرد على رسالة العضو المستهدف")
            return
        parts = text.split(maxsplit=2)
        import re
        time_patterns = [r'^\d+ث$', r'^\d+ثانية$', r'^\d+د$', r'^\d+دقيقة$', r'^\d+س$', r'^\d+ساعة$', r'^يوم$']
        is_time = False
        if len(parts) >= 2:
            for pattern in time_patterns:
                if re.match(pattern, parts[1]):
                    is_time = True
                    break
        
        if is_time:
            context.user_data['temp_duration'] = parts[1]
            context.user_data['temp_reason'] = parts[2] if len(parts) > 2 else "لا يوجد سبب"
        else:
            context.user_data['temp_reason'] = parts[1] if len(parts) > 1 else "لا يوجد سبب"
        await mute_command(update, context)
        return
    
    if text.startswith("#فك_كتم"):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ يرجى الرد على رسالة العضو المستهدف")
            return
        await unmute_command(update, context)
        return
    
    if text.startswith("#حظر"):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ يرجى الرد على رسالة العضو المستهدف")
            return
        parts = text.split(maxsplit=1)
        context.user_data['temp_reason'] = parts[1] if len(parts) > 1 else "لا يوجد سبب"
        await ban_command(update, context)
        return
    
    if text.startswith("#طرد"):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ يرجى الرد على رسالة العضو المستهدف")
            return
        parts = text.split(maxsplit=1)
        context.user_data['temp_reason'] = parts[1] if len(parts) > 1 else "لا يوجد سبب"
        await kick_command(update, context)
        return
    
    if text.startswith("#خصم"):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ يرجى الرد على رسالة العضو المستهدف")
            return
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            await update.message.reply_text("❌ يرجى تحديد المبلغ")
            return
        try:
            context.user_data['temp_amount'] = int(parts[1])
        except:
            await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً")
            return
        context.user_data['temp_reason'] = parts[2] if len(parts) > 2 else "لا يوجد سبب"
        await remove_balance_command(update, context)
        return
    
    if text.startswith("#مكافأة"):
        if not update.message.reply_to_message:
            await update.message.reply_text("❌ يرجى الرد على رسالة العضو المستهدف")
            return
        parts = text.split(maxsplit=2)
        if len(parts) < 2:
            await update.message.reply_text("❌ يرجى تحديد المبلغ")
            return
        try:
            context.user_data['temp_amount'] = int(parts[1])
        except:
            await update.message.reply_text("❌ المبلغ يجب أن يكون رقماً")
            return
        context.user_data['temp_reason'] = parts[2] if len(parts) > 2 else "لا يوجد سبب"
        await add_balance_command(update, context)
        return
    
    # معالجة إجابات الألعاب
    if context.user_data.get('waiting_guess') or context.user_data.get('waiting_question') or context.user_data.get('waiting_reverse') or context.user_data.get('waiting_lucky'):
        await handle_game_answer(update, context)
        return
    
    # معالجة إدخالات المالك
    if context.user_data.get('waiting_shop_name') or context.user_data.get('waiting_shop_price') or context.user_data.get('waiting_edit_name') or context.user_data.get('waiting_edit_price') or context.user_data.get('waiting_warn_all') or context.user_data.get('waiting_warn_reason') or context.user_data.get('waiting_deduct_amount') or context.user_data.get('waiting_reward_amount') or context.user_data.get('waiting_broadcast_media') or context.user_data.get('waiting_broadcast_text') or context.user_data.get('waiting_mute_duration') or context.user_data.get('waiting_ban_reason') or context.user_data.get('waiting_admin_reward_amount') or context.user_data.get('waiting_admin_reward_reason'):
        await handle_owner_input(update, context)
        return
    
    # معالجة إدخالات المشرفين
    if context.user_data.get('admin_warn_target') or context.user_data.get('admin_mute_target') or context.user_data.get('admin_deduct_target'):
        await handle_admin_inputs(update, context)
        return

def check_mutes_thread(bot):
    while True:
        time.sleep(30)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(check_expired_mutes(bot))
            loop.close()
        except Exception as e:
            print(f"Check mutes error: {e}")

def backup_thread(bot):
    while True:
        time.sleep(3600)
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(create_backup(bot))
            loop.close()
        except Exception as e:
            print(f"Backup error: {e}")

async def post_init(app):
    await app.bot.delete_webhook()
    print("✅ Webhook deleted")

def main():
    init_db()
    
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # أوامر إنجليزية
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("game", game_command))
    app.add_handler(CommandHandler("shop", shop_command))
    app.add_handler(CommandHandler("daily", daily_reward_command))
    app.add_handler(CommandHandler("warn", warning_command))
    app.add_handler(CommandHandler("mute", mute_command))
    app.add_handler(CommandHandler("unmute", unmute_command))
    app.add_handler(CommandHandler("deduct", remove_balance_command))
    app.add_handler(CommandHandler("reward", add_balance_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("kick", kick_command))
    app.add_handler(CommandHandler("admin", admin_panel_command))
    app.add_handler(CommandHandler("owner", owner_panel_command))
    
    # ========== معالجات الأزرار ==========
    app.add_handler(CallbackQueryHandler(game_callback, pattern="^(game_|rps_)"))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern="^shop_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(owner_callback, pattern="^(owner_|admin_|shop_|warn_|bulk_|user_|broadcast_|close)"))
    app.add_handler(CallbackQueryHandler(handle_admin_buttons, pattern="^(admin_warn_|admin_mute_|admin_deduct_|close)"))
    
    # ========== معالجات الرسائل ==========
    # معالج الرسائل النصية (الأوامر العربية)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))
    
    # معالج الملفات (لإعلان متحرك - GIF, ملصق, فيديو)
    app.add_handler(MessageHandler(filters.ANIMATION | filters.STICKER | filters.VIDEO | filters.DOCUMENT, handle_owner_input))
    
    # تشغيل مهمة فحص الكتم
    check_mutes = threading.Thread(target=check_mutes_thread, args=(app.bot,), daemon=True)
    check_mutes.start()
    print("✅ Mute checker started (every 30 seconds)")
    
    # النسخ الاحتياطي
    backup = threading.Thread(target=backup_thread, args=(app.bot,), daemon=True)
    backup.start()
    
    print("✅ البوت شغال...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
