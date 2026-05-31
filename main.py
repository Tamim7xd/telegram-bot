import logging
import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN, GROUP_ID, OWNER_ID
from shared.database import init_db

# استيراد جميع الأنظمة
from system_profile.profile_handler import profile_command
from system_games.games_handler import game_command, game_callback, handle_game_answer
from system_shop.shop_handler import shop_command, shop_callback
from system_warnings.warnings_handler import warning_command
from system_punishments.punishments_handler import mute_command, ban_command, kick_command
from system_economy.economy_handler import add_balance_command, remove_balance_command, daily_reward_command
from system_admin.admin_handler import admin_panel_command, admin_callback
from system_owner.owner_handler import owner_panel_command, owner_callback
from system_backup.backup_handler import start_backup_scheduler, create_backup

logging.basicConfig(level=logging.INFO)

async def start(update, context):
    user_id = update.effective_user.id
    username = update.effective_user.username or "لا يوجد"
    first_name = update.effective_user.first_name or ""
    
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

async def handle_message(update, context):
    # معالجة الألعاب التي تنتظر إجابة
    if context.user_data.get('waiting_guess') or \
       context.user_data.get('waiting_question') or \
       context.user_data.get('waiting_reverse') or \
       context.user_data.get('waiting_lucky'):
        await handle_game_answer(update, context)
        return

async def backup_loop(app):
    """تشغيل النسخ الاحتياطي كل ساعة"""
    while True:
        await asyncio.sleep(3600)  # كل ساعة
        await create_backup(app.bot)

def main():
    # تهيئة قاعدة البيانات
    init_db()
    
    # إنشاء التطبيق
    app = Application.builder().token(BOT_TOKEN).build()
    
    # ========================================
    # الأوامر العامة (تعمل للجميع)
    # ========================================
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ملف", profile_command))
    app.add_handler(CommandHandler("لعبة", game_command))
    app.add_handler(CommandHandler("سوق", shop_command))
    app.add_handler(CommandHandler("يومي", daily_reward_command))
    
    # ========================================
    # أوامر المشرفين (تتطلب رد على الرسالة)
    # ========================================
    app.add_handler(CommandHandler("تحذير", warning_command))
    app.add_handler(CommandHandler("كتم", mute_command))
    app.add_handler(CommandHandler("خصم", add_balance_command))
    app.add_handler(CommandHandler("مكافأة", remove_balance_command))
    
    # ========================================
    # أوامر المشرف الإداري
    # ========================================
    app.add_handler(CommandHandler("حظر", ban_command))
    app.add_handler(CommandHandler("طرد", kick_command))
    
    # ========================================
    # لوحات التحكم
    # ========================================
    app.add_handler(CommandHandler("مشرف", admin_panel_command))
    app.add_handler(CommandHandler("مالك", owner_panel_command))
    
    # ========================================
    # معالجات الأزرار (Callback Queries)
    # ========================================
    app.add_handler(CallbackQueryHandler(game_callback, pattern="^(game_|rps_)"))
    app.add_handler(CallbackQueryHandler(shop_callback, pattern="^shop_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(owner_callback, pattern="^owner_"))
    
    # ========================================
    # معالج الرسائل (للألعاب)
    # ========================================
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # ========================================
    # تشغيل النسخ الاحتياطي في الخلفية
    # ========================================
    asyncio.create_task(backup_loop(app))
    
    # ========================================
    # تشغيل البوت
    # ========================================
    print("✅ البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()