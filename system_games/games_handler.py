import random
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.text_normalizer import is_correct
from shared.message_builder import send_and_delete
from .games_data import (
    GAMES_MENU, GAME_REWARD, QUESTIONS, REVERSE_WORDS,
    LUCKY_NUMBER_CONFIG, LUCKY_BOX_CONFIG
)

async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(g["name"], callback_data=f"game_{g['callback']}")] for g in GAMES_MENU]
    keyboard.append([InlineKeyboardButton("🔙 إغلاق", callback_data="game_close")])
    
    await update.message.reply_text(
        "🎮 **اختر لعبتك:**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "game_close":
        await query.edit_message_text("🔚 تم إغلاق الألعاب")
        return
    
    elif data == "game_guess_number":
        number = random.randint(1, 100)
        context.user_data['guess_number'] = number
        await query.edit_message_text(f"🔢 خمن الرقم بين 1 و 100\n(أكتب رقمك في الرد)")
        context.user_data['waiting_guess'] = True
    
    elif data == "game_rps":
        keyboard = [
            [InlineKeyboardButton("✊ حجر", callback_data="rps_حجر")],
            [InlineKeyboardButton("✋ ورقة", callback_data="rps_ورقة")],
            [InlineKeyboardButton("✌️ مقص", callback_data="rps_مقص")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="game_back")]
        ]
        await query.edit_message_text("✊✋✌️ اختر:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("rps_"):
        user_choice = data.split("_")[1]
        bot_choice = random.choice(["حجر", "ورقة", "مقص"])
        
        rules = {"حجر": "مقص", "ورقة": "حجر", "مقص": "ورقة"}
        
        if user_choice == bot_choice:
            result = "🤝 تعادل!"
            reward = 0
        elif rules[user_choice] == bot_choice:
            result = "✅ فزت!"
            reward = GAME_REWARD
        else:
            result = "❌ خسرت!"
            reward = 0
        
        if reward > 0:
            conn = get_db()
            conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
            conn.commit()
            conn.close()
        
        await query.edit_message_text(f"أنت: {user_choice}\nالبوت: {bot_choice}\n\n{result}\n💰 +{reward} عملة")
    
    elif data == "game_questions":
        q = random.choice(QUESTIONS)
        context.user_data['current_question'] = q
        await query.edit_message_text(f"❓ {q['q']}\n\n(أكتب إجابتك في الرد)")
        context.user_data['waiting_question'] = True
    
    elif data == "game_reverse_words":
        word = random.choice(REVERSE_WORDS)
        context.user_data['current_reverse'] = word
        await query.edit_message_text(f"🔄 اكتب الكلمة بشكل معكوس:\n{word['word']}\n\n(أكتب إجابتك في الرد)")
        context.user_data['waiting_reverse'] = True
    
    elif data == "game_lucky_number":
        num = random.randint(1, 10)
        await query.edit_message_text(f"🎲 اختر رقم حظك من 1 إلى 10\n(أكتب رقمك في الرد)")
        context.user_data['waiting_lucky'] = True
        context.user_data['lucky_number'] = num
    
    elif data == "game_lucky_box":
        last_box = context.user_data.get('last_lucky_box', 0)
        box_count = context.user_data.get('lucky_box_count', 0)
        today = time.strftime("%Y-%m-%d")
        
        if context.user_data.get('lucky_box_date') != today:
            context.user_data['lucky_box_count'] = 0
            context.user_data['lucky_box_date'] = today
            box_count = 0
        
        if time.time() - last_box < LUCKY_BOX_CONFIG["cooldown_minutes"] * 60:
            remaining = int(LUCKY_BOX_CONFIG["cooldown_minutes"] * 60 - (time.time() - last_box))
            await query.edit_message_text(f"⏳ انتظر {remaining//60} دقيقة و {remaining%60} ثانية")
            return
        
        if box_count >= LUCKY_BOX_CONFIG["max_per_day"]:
            await query.edit_message_text("😭 وصلت للحد الأقصى اليومي (10 محاولات)")
            return
        
        rand = random.randint(1, 100)
        cumulative = 0
        reward = 0
        message = ""
        
        for r in LUCKY_BOX_CONFIG["rewards"]:
            cumulative += r["chance"]
            if rand <= cumulative:
                reward = r["amount"]
                message = r["message"]
                break
        
        if reward > 0:
            conn = get_db()
            conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
            conn.commit()
            conn.close()
        
        context.user_data['last_lucky_box'] = time.time()
        context.user_data['lucky_box_count'] = box_count + 1
        
        await query.edit_message_text(f"🎁 لوكي بوكس\n\n{message}\n💰 +{reward} عملة")
    
    elif data == "game_back":
        keyboard = [[InlineKeyboardButton(g["name"], callback_data=f"game_{g['callback']}")] for g in GAMES_MENU]
        keyboard.append([InlineKeyboardButton("🔙 إغلاق", callback_data="game_close")])
        await query.edit_message_text("🎮 **اختر لعبتك:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_game_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    if context.user_data.get('waiting_guess'):
        try:
            guess = int(message_text)
            number = context.user_data.get('guess_number')
            if guess == number:
                reward = GAME_REWARD
                conn = get_db()
                conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
                conn.execute("UPDATE users SET messages = messages + 1 WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"✅ صحيح! الرقم كان {number}\n💰 +{reward} عملة")
            else:
                await update.message.reply_text(f"❌ خطأ! الرقم كان {number}")
        except:
            await update.message.reply_text("❌ أرسل رقماً صحيحاً")
        context.user_data['waiting_guess'] = False
    
    elif context.user_data.get('waiting_question'):
        q = context.user_data.get('current_question')
        if q and is_correct(message_text, q['a']):
            reward = GAME_REWARD
            conn = get_db()
            conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
            conn.execute("UPDATE users SET messages = messages + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            await update.message.reply_text(f"✅ إجابة صحيحة!\n💰 +{reward} عملة")
        else:
            await update.message.reply_text(f"❌ خطأ! الإجابة الصحيحة: {q['a']}")
        context.user_data['waiting_question'] = False
    
    elif context.user_data.get('waiting_reverse'):
        word = context.user_data.get('current_reverse')
        if word and is_correct(message_text, word['reverse']):
            reward = GAME_REWARD
            conn = get_db()
            conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
            conn.execute("UPDATE users SET messages = messages + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            await update.message.reply_text(f"✅ صحيح! معكوس {word['word']} هو {word['reverse']}\n💰 +{reward} عملة")
        else:
            await update.message.reply_text(f"❌ خطأ! الإجابة الصحيحة: {word['reverse']}")
        context.user_data['waiting_reverse'] = False
    
    elif context.user_data.get('waiting_lucky'):
        try:
            guess = int(message_text)
            number = context.user_data.get('lucky_number')
            if guess == number:
                reward = GAME_REWARD
                conn = get_db()
                conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
                conn.execute("UPDATE users SET messages = messages + 1 WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"🎉 فزت! رقم الحظ كان {number}\n💰 +{reward} عملة")
            else:
                await update.message.reply_text(f"❌ خسرت! رقم الحظ كان {number}")
        except:
            await update.message.reply_text("❌ أرسل رقماً صحيحاً")
        context.user_data['waiting_lucky'] = False