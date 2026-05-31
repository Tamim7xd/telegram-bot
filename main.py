import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import BOT_TOKEN
from shared.database import init_db

from system_games.games_handler import game_command, game_callback, handle_game_answer
from system_profile.profile_handler import profile_command

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
        "#ملف - عرض ملفك الشخصي\n"
        "#لعبة - فتح الألعاب\n"
        "#سوق - فتح المتجر\n"
        "#تحذير - تحذير عضو (للمشرفين)\n"
        "#كتم - كتم عضو (للمشرفين)\n"
        "#مشرف - لوحة المشرفين\n"
        "#مالك - لوحة المالك",
        parse_mode="Markdown"
    )

def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ملف", profile_command))
    app.add_handler(CommandHandler("لعبة", game_command))
    app.add_handler(CallbackQueryHandler(game_callback, pattern="^(game_|rps_)"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_game_answer))
    
    print("✅ البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()