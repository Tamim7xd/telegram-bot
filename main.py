import logging
import threading
import time
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from shared.database import init_db

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
        "#ملف - عرض ملفك الشخصي\n"
        "#لعبة - فتح الألعاب\n"
        "#سوق - فتح المتجر\n"
        "#يومي - مكافأة يومية\n\n"
        "🛡️ **أوامر المشرفين:**\n"
        "#تحذير سبب - تحذير عضو\n"
        "#كتم مدة سبب - كتم عضو\n"
        "#خصم مبلغ سبب - خصم رصيد\n"
        "#مكافأة مبلغ سبب - إضافة رصيد\n"
        "#مشرف - لوحة المشرفين\n\n"
        "👑 **أوامر المشرف الإداري:**\n"
        "#حظر سبب - حظر عضو\n"
        "#طرد سبب - طرد عضو\n\n"
        "⭐ **أوامر المالك:**\n"
        "#مالك - لوحة المالك\n"
        "━━━━━━━━━━━━━━━━━━━━━━",
        parse_mode="Markdown"
    )

async def handle_arabic_commands(update, context):
    text = update.message.text.strip()
    
    if text in ["#ملف", "#ملفي", "#الملف", "#معلومات", "#معلوماتي"]:
        await profile_command(update, context)
        return
    if text in ["#لعبة", "#العاب", "#لعب", "#العب"]:
        await game_command(update, context)
        return
    if text in ["#سوق", "#محل", "#شراء", "#اشتري", "#اسواق"]:
        await shop_command(update, context)
        return
    if text in ["#يومي", "#مكافأةيومية"]:
        await daily_reward_command(update, context)
        return
    if text.startswith("#تحذير"):
        parts = text.split(maxsplit=1)
        reason = parts[1] if len(parts) > 1 else "لا يوجد سبب"
        update.message.text = f"/warn {reason}"
        await warning_command(update, context)
        return
    if text.startswith("#كتم"):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2:
            duration = parts[1]
            reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
            update.message.text = f"/mute {duration} {reason}"
        else:
            update.message.text = "/mute"
        await mute_command(update, context)
        return
    if text.startswith("#حظر"):
        parts = text.split(maxsplit=1)
        reason = parts[1] if len(parts) > 1 else "لا يوجد سبب"
        update.message.text = f"/ban {reason}"
        await ban_command(update, context)
        return
    if text.startswith("#طرد"):
        parts = text.split(maxsplit=1)
        reason = parts[1] if len(parts) > 1 else "لا يوجد سبب"
        update.message.text = f"/kick {reason}"
        await kick_command(update, context)
        return
    if text.startswith("#خصم"):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2:
            amount = parts[1]
            reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
            update.message.text = f"/deduct {amount} {reason}"
        else:
            update.message.text = "/deduct"
        await add_balance_command(update, context)
        return
    if text.startswith("#مكافأة"):
        parts = text.split(maxsplit=2)
        if len(parts) >= 2:
            amount = parts[1]
            reason = parts[2] if len(parts) > 2 else "لا يوجد سبب"
            update.message.text = f"/reward {amount} {reason}"
        else:
            update.message.text = "/reward"
        await remove_balance_command(update, context)
        return
    if text in ["#مشرف", "#ادمن"]:
        await admin_panel_command(update, context)
        return
    if text == "#مالك":
        await owner_panel_command(update, context)
        return

async def handle_message(update, context):
    if context.user_data.get('waiting_guess') or context.user_data.get('waiting_question') or context.user_data.get('waiting_reverse') or context.user_data.get('waiting_lucky'):
        await handle_game_answer(update, context)
        return
    if context.user_data.get('waiting_add_admin') or context.user_data.get('waiting_add_super') or context.user_data.get('waiting_remove_admin') or context.user_data.get('waiting_broadcast'):
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
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("game", game_command))
    app.add_handler(CommandHandler("shop", shop_command))
    app.add_handler(CommandHandler("daily", daily_reward_command))
    app.add_handler(CommandHandler("warn", warning_command))
    app.add_handler(CommandHandler("mute", mute_command))
    app.add_handler(CommandHandler("deduct", add_balance_command))
    app.add_handler(CommandHandler("reward", remove_balance_command))
    app.add_handler(CommandHandler("ban", ban_command))
    app.add_handler(CommandHandler("kick", kick_command))
    app.add_handler(CommandHandler("admin", admin_panel_command))
    app.add_handler(CommandHandler("owner", owner_panel_command))
    
    app.add_handler(CallbackQueryHandler(game_callback, pattern="^(game_|rps_)"))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern="^shop_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(owner_callback, pattern="^owner_"))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_arabic_commands))
    
    backup = threading.Thread(target=backup_thread, args=(app.bot,), daemon=True)
    backup.start()
    
    print("✅ البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()