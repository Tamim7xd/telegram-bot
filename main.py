# أضف هذه الدالة في main.py (بعد دالة start)

async def handle_arabic_commands(update, context):
    """معالجة الأوامر العربية مثل #ملف #لعبة #سوق"""
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    # الأوامر العربية
    if text == "#ملف" or text == "#ملفي" or text == "#الملف" or text == "#معلومات" or text == "#معلوماتي":
        await profile_command(update, context)
    
    elif text == "#لعبة" or text == "#العاب" or text == "#العب":
        await game_command(update, context)
    
    elif text == "#سوق" or text == "#محل" or text == "#شراء" or text == "#اشتري" or text == "#اسواق":
        await shop_command(update, context)
    
    elif text == "#يومي" or text == "#مكافأةيومية":
        await daily_reward_command(update, context)
    
    elif text.startswith("#تحذير"):
        # استخراج السبب
        parts = text.split(maxsplit=1)
        if len(parts) > 1:
            update.message.text = f"/warn {parts[1]}"
        else:
            update.message.text = "/warn"
        await warning_command(update, context)
    
    elif text.startswith("#كتم"):
        parts = text.split(maxsplit=2)
        if len(parts) > 1:
            update.message.text = f"/mute {parts[1]} {parts[2] if len(parts) > 2 else ''}"
        else:
            update.message.text = "/mute"
        await mute_command(update, context)
    
    elif text.startswith("#حظر"):
        parts = text.split(maxsplit=1)
        if len(parts) > 1:
            update.message.text = f"/ban {parts[1]}"
        else:
            update.message.text = "/ban"
        await ban_command(update, context)
    
    elif text.startswith("#طرد"):
        parts = text.split(maxsplit=1)
        if len(parts) > 1:
            update.message.text = f"/kick {parts[1]}"
        else:
            update.message.text = "/kick"
        await kick_command(update, context)
    
    elif text.startswith("#خصم"):
        parts = text.split(maxsplit=2)
        if len(parts) > 1:
            update.message.text = f"/deduct {parts[1]} {parts[2] if len(parts) > 2 else ''}"
        else:
            update.message.text = "/deduct"
        await add_balance_command(update, context)
    
    elif text.startswith("#مكافأة"):
        parts = text.split(maxsplit=2)
        if len(parts) > 1:
            update.message.text = f"/reward {parts[1]} {parts[2] if len(parts) > 2 else ''}"
        else:
            update.message.text = "/reward"
        await remove_balance_command(update, context)
    
    elif text == "#مشرف" or text == "#ادمن":
        await admin_panel_command(update, context)
    
    elif text == "#مالك":
        await owner_panel_command(update, context)
    
    else:
        # ليس أمراً عربياً، تجاهل
        pass