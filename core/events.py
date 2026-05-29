from aiogram import Dispatcher, types
from aiogram.types import Message
from config import ADMIN_IDS, CURRENCY_NAME
from _core.users import update_user_money, get_user
from _core.xp import add_xp, get_xp_progress
from _core.games import cmd_game
from _core.titles import set_user_title, remove_user_title
import re

async def handle_reply_actions(message: Message):
    if not message.reply_to_message:
        return
    if message.from_user.id not in ADMIN_IDS:
        return
    target = message.reply_to_message.from_user
    text = message.text.strip()
    
    if text.startswith("خصم"):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            amount = int(parts[1])
            await update_user_money(target.id, -amount, "خصم بواسطة أدمن", message.from_user.id)
            await message.reply(f"✅ تم خصم {amount} {CURRENCY_NAME} من {target.full_name}")
        else:
            await message.reply("❌ الصيغة: خصم 100")
    elif text.startswith("اضافة"):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            amount = int(parts[1])
            await update_user_money(target.id, amount, "إضافة بواسطة أدمن", message.from_user.id)
            await message.reply(f"✅ تم إضافة {amount} {CURRENCY_NAME} إلى {target.full_name}")
        else:
            await message.reply("❌ الصيغة: اضافة 100")
    elif text.startswith("لقب"):
        title = text[4:].strip()
        if title:
            await set_user_title(target.id, title)
            await message.reply(f"🏷️ تم منح اللقب '{title}' إلى {target.full_name}")
        else:
            await message.reply("❌ الصيغة: لقب بطل")
    elif text == "ازالة لقب":
        await remove_user_title(target.id)
        await message.reply(f"✅ تم إزالة اللقب عن {target.full_name}")

async def handle_hashtag_commands(message: Message):
    text = message.text.strip()
    user_id = message.from_user.id
    if text in ["#ملفي", "#حسابي", "#معلوماتي"]:
        user = await get_user(user_id)
        progress = await get_xp_progress(user_id)
        reply = f"""👤 *{user['full_name']}* (@{user['username'] or 'لا يوجد'})

━━━━━━━━━━━━━━━
💰 *الرصيد:* {user['money']} {CURRENCY_NAME}
🏆 *اللقب:* {user['title'] or 'لا يوجد'}
⭐ *XP:* {user['xp']}
📊 *المستوى:* {user['level']}

📈 *شريط التقدم:*
{progress['bar']} {progress['percent']}%

⏳ *المتبقي للمستوى التالي:* {progress['remaining']} XP

━━━━━━━━━━━━━━━
🎮 *نقاط الألعاب:* {user['game_points']}
🏅 *عدد الانتصارات:* {user['wins']}
"""
        await message.reply(reply, parse_mode="Markdown")
    elif text in ["#فلوس", "#فلوسي", "#رصيدي"]:
        user = await get_user(user_id)
        await message.reply(f"💰 رصيدك الحالي: {user['money']} {CURRENCY_NAME}")
    elif text in ["#لعبة", "#العب", "#العاب"]:
        await cmd_game(message)
    elif text in ["#مستواي", "#لـيفلي", "#نقاطي"]:
        user = await get_user(user_id)
        progress = await get_xp_progress(user_id)
        await message.reply(f"📊 *المستوى {user['level']}*\n{progress['bar']} {progress['percent']}%\n{progress['remaining']} XP للمستوى التالي", parse_mode="Markdown")
    # يمكن إضافة #ترتيب لاحقاً

def register_event_handlers(dp: Dispatcher):
    dp.message.register(handle_reply_actions)
