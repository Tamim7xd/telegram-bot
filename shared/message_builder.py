import asyncio

async def send_and_delete(context, chat_id, text, timeout=5, reply_markup=None):
    msg = await context.bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode="Markdown")
    await asyncio.sleep(timeout)
    try:
        await msg.delete()
    except:
        pass
    return msg

async def edit_and_delete(query, text, timeout=5, reply_markup=None):
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    await asyncio.sleep(timeout)
    try:
        await query.delete_message()
    except:
        pass

def build_notification(title, icon, content, admin_name):
    return f"""{icon} **{title}**

{content}

👮 بواسطة: {admin_name}"""

def build_user_card(user_id, username, first_name, balance, warnings, level, title):
    title_text = f"🏆 {title}" if title else "🏆 لا يوجد"
    return f"""👤 **{first_name}** (@{username})

💰 الرصيد: {balance} 🪙
⚠️ التحذيرات: {warnings}
🎖️ المستوى: {level}
{title_text}"""