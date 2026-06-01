import logging
import threading
import time
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from shared.database import init_db

# استيراد جميع الأنظمة
from system_profile.profile_handler import profile_command
from system_games.games_handler import game_command, game_callback, handle_game_answer
from system_shop.shop_handler import shop_command, shop_callback
from system_warnings.warnings_handler import warning_command
from system_punishments.punishments_handler import mute_command, ban_command, kick_command
from system_economy.economy_handler import add_balance_command, remove_balance_command, daily_reward_command
from system_admin.admin_handler import admin_panel_command, admin_callback
from system_owner.owner_handler import owner_panel_command, owner_callback, handle_owner_input
from system_backup.backup_handler import create_backup

logging.basicConfig(level=logging.INFO)

async def start(update, context):
    user_id = update.effective_user.id
    username = update.effective_user.username or "لا يوجد"
    first_name = update.effective_user.first_name or "مستخدم"
    
    from shared.database import get_db
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)", 
                 (user_id, username, first_name))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        "✅ **البوت يعمل!**\n\n"
        "📋 **الأوامر المتاحة:**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👤 **أوامر عامة:**\n"
        "/profile - عرض ملفك الشخصي\n"
        "/game - فتح الألعاب\n"
        "/shop - فتح المتجر\n"
        "/daily - مكافأة يومية\n\n"
        "🛡️ **أوامر المشرفين:**\n"
        "/warn سبب - تحذير عضو\n"
        "/mute مدة سبب - كتم عضو\n"
        "/deduct مبلغ سبب - خصم رصيد\n"
        "/reward مبلغ سبب - إضافة رصيد\n"
        "/admin - لوحة المشرفين\n\n"
        "👑 **أوامر المشرف الإداري:**\n"
        "/ban سبب - حظر عضو\n"
        "/kick سبب - طرد عضو\n\n"
        "⭐ **أوامر المالك:**\n"
        "/owner - لوحة المالك\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

async def handle_message(update, context):
    # معالجة الألعاب
    if context.user_data.get('waiting_guess') or \
       context.user_data.get('waiting_question') or \
       context.user_data.get('waiting_reverse') or \
       context.user_data.get('waiting_lucky'):
        await handle_game_answer(update, context)
        return
    
    # معالجة إدخالات المالك
    if context.user_data.get('waiting_add_admin') or \
       context.user_data.get('waiting_add_super') or \
       context.user_data.get('waiting_remove_admin'):
        await handle_owner_input(update, context)
        return

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
    
    # الأوامر العامة
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("game", game_command))
    app.add_handler(CommandHandler("shop", shop_command))
    app.add_handler(CommandHandler("daily", daily_reward_command))
    
    # أوامر المشرفين
    app.add_handler(CommandHandler("warn", warning_command))
    app.add_handler(CommandHandler("mute", mute_command))
    app.add_handler(CommandHandler("deduct", add_balance_command))
    app.add_handler(CommandHandler("reward", remove_balance_command))
    
    # أوامر المشرف الإداري
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("kick", kick_command))
    
    # لوحات التحكم
    app.add_handler(CommandHandler("admin", admin_panel_command))
    app.add_handler(CommandHandler("owner", owner_panel_command))
    
    # معالجات الأزرار
    app.add_handler(CallbackQueryHandler(game_callback, pattern="^(game_|rps_)"))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern="^shop_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(owner_callback, pattern="^owner_"))
    
    # معالج الرسائل
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # النسخ الاحتياطي
    backup = threading.Thread(target=backup_thread, args=(app.bot,), daemon=True)
    backup.start()
    
    print("✅ البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()