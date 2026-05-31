from aiogram import Bot, Dispatcher
from config import CURRENCY_NAME, LEVELUP_BONUS_MONEY, LEVELUP_BONUS_XP, GROUP_ID
from _core.xp import get_xp_progress
import asyncio
from datetime import datetime

bot = None

def set_bot_instance(b: Bot):
    global bot
    bot = b

async def send_auto_delete(chat_id: int, text: str, delay: int = 30, parse_mode: str = "HTML"):
    try:
        msg = await bot.send_message(chat_id, text, parse_mode=parse_mode)
        asyncio.create_task(delete_after(msg, delay))
    except Exception as e:
        print(f"⚠️ فشل الإشعار: {e}")

async def delete_after(msg, seconds: int):
    await asyncio.sleep(seconds)
    try:
        await msg.delete()
    except:
        pass

async def send_levelup_notification(chat_id: int, user_id: int, new_level: int, user_name: str):
    progress = await get_xp_progress(user_id)
    text = f"""╔══════════════════════════════╗
┃ 🎉 <b>تـهـنـئـة</b> 🎉
╚══════════════════════════════╝

✨ <b>مبروك يا {user_name}</b> ✨
لقد وصلت إلى 🔥 <b>المستوى {new_level}</b> 🔥

💰 <b>مكافأة الترقية:</b> {LEVELUP_BONUS_MONEY:,} {CURRENCY_NAME}
⭐ <b>XP إضافي:</b> {LEVELUP_BONUS_XP} نقطة

📊 <b>شريط XP الجديد:</b>
{progress['bar']} {progress['percent']}%

📌 <b>المتبقي للمستوى التالي:</b> {progress['remaining']} XP"""
    await send_auto_delete(chat_id, text, delay=30)

async def send_deduction_notification(chat_id: int, executor_name: str, target_name: str, amount: int, reason: str):
    border = "╔══════════════════════════════╗"
    text = f"""{border}
┃ 💰 <b>خـصـم رصـيـد</b> 💰
╚══════════════════════════════╝

👤 <b>المنفذ:</b> {executor_name}
👥 <b>المستخدم:</b> {target_name}
⚙️ <b>الإجراء:</b> خصم رصيد
📝 <b>المبلغ:</b> {amount:,} {CURRENCY_NAME}
📝 <b>السبب:</b> {reason}
🕒 <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    await send_auto_delete(chat_id, text, delay=30)

async def send_reward_notification(chat_id: int, executor_name: str, target_name: str, amount: int, reason: str):
    border = "╔══════════════════════════════╗"
    text = f"""{border}
┃ 🎁 <b>مـكافـأة</b> 🎁
╚══════════════════════════════╝

👤 <b>المنفذ:</b> {executor_name}
👥 <b>المستخدم:</b> {target_name}
⚙️ <b>الإجراء:</b> إضافة رصيد
📝 <b>المبلغ:</b> {amount:,} {CURRENCY_NAME}
📝 <b>السبب:</b> {reason}
🕒 <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    await send_auto_delete(chat_id, text, delay=30)

async def send_warning_notification(chat_id: int, executor_name: str, target_name: str, warning_count: int, reason: str):
    border = "╔══════════════════════════════╗"
    text = f"""{border}
┃ ⚠️ <b>تـحـذيـر</b> ⚠️
╚══════════════════════════════╝

👤 <b>المنفذ:</b> {executor_name}
👥 <b>المستخدم:</b> {target_name}
⚙️ <b>الإجراء:</b> تحذير
📊 <b>عدد التحذيرات:</b> {warning_count}/100
📝 <b>السبب:</b> {reason}
🕒 <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    await send_auto_delete(chat_id, text, delay=30)

async def send_admin_notification(executor_name: str, target_name: str, action: str, detail: str = ""):
    if not GROUP_ID:
        print("⚠️ GROUP_ID غير معرف")
        return
    border = "╔══════════════════════════════╗"
    text = f"""{border}
┃ 🔔 <b>إشـارة إداريـة</b> 🔔
╚══════════════════════════════╝

👤 <b>المنفذ:</b> {executor_name}
👥 <b>المستخدم:</b> {target_name}
⚙️ <b>الإجراء:</b> {action}
📝 <b>التفاصيل:</b> {detail}
🕒 <b>الوقت:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
━━━━━━━━━━━━━━━━━━━━━━━━━━"""
    await send_auto_delete(GROUP_ID, text, delay=30)

def register_notify_handlers(dp: Dispatcher):
    pass
