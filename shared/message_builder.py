async def edit_message(update, text, keyboard=None, timeout=3):
    query = update.callback_query
    await query.edit_message_text(text, reply_markup=keyboard)
    
    if timeout > 0:
        import asyncio
        await asyncio.sleep(timeout)
        try:
            await query.delete_message()
        except:
            pass

async def send_temp_message(context, chat_id, text, timeout=3):
    msg = await context.bot.send_message(chat_id, text)
    import asyncio
    await asyncio.sleep(timeout)
    try:
        await msg.delete()
    except:
        pass