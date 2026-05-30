from config import ADMIN_IDS, CURRENCY_NAME
from db import execute, fetchone, fetchall
from _core.users import create_user, add_money
from _core.xp import update_level
from _core.games import start_game_menu, process_game_answer


# 🔥 تحديث المستخدم عند أي رسالة
async def handle_text(message):

    if not message.text:
        return

    await create_user(message.from_user)

    text = message.text.strip()
    uid = message.from_user.id

    # =========================
    # 👤 أوامر الأعضاء #
    # =========================
    if text.startswith("#"):

        if text in ["#لعبة", "#العاب", "#العب"]:
            await start_game_menu(message)
            return

        if text == "#ملفي":
            user = fetchone("SELECT * FROM users WHERE telegram_id=?", (uid,))
            await message.reply(
                f"👤 {user[2]}\n💰 {user[3]} {CURRENCY_NAME}\n⭐ XP: {user[4]}\n📊 Level: {user[5]}"
            )
            return

        if text == "#فلوسي":
            user = fetchone("SELECT money FROM users WHERE telegram_id=?", (uid,))
            await message.reply(f"💰 رصيدك: {user[0]} {CURRENCY_NAME}")
            return

    # =========================
    # 👮 أوامر الأدمن $
    # =========================
    if text.startswith("$"):

        if uid not in ADMIN_IDS:
            await message.reply("❌ ليس لديك صلاحية")
            return

        parts = text.split()

        # ➕ إعطاء فلوس
        if parts[0] == "$اعطاء":
            amount = int(parts[1])
            target = message.reply_to_message.from_user.id
            await add_money(target, amount)
            await message.reply("✅ تم الإضافة")
            return

        # ➖ خصم
        if parts[0] == "$خصم":
            amount = int(parts[1])
            target = message.reply_to_message.from_user.id
            await add_money(target, -amount)
            await message.reply("✅ تم الخصم")
            return

        # 🔇 كتم (بسيط)
        if parts[0] == "$كتم":
            target = message.reply_to_message.from_user.id
            execute("UPDATE users SET status='muted' WHERE telegram_id=?", (target,))
            await message.reply("🔇 تم الكتم")
            return

        # 🚫 حظر
        if parts[0] == "$حظر":
            target = message.reply_to_message.from_user.id
            execute("UPDATE users SET status='banned' WHERE telegram_id=?", (target,))
            await message.reply("🚫 تم الحظر")
            return
