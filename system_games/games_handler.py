import random
import time
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from shared.database import get_db
from shared.text_normalizer import is_correct
from .games_data import GAMES_MENU, GAME_REWARD, QUESTIONS, REVERSE_WORDS, LUCKY_BOX_REWARDS

async def game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(g["name"], callback_data=f"game_{g['callback']}")] for g in GAMES_MENU]
    keyboard.append([InlineKeyboardButton("🔙 إغلاق", callback_data="game_close")])
    
    await update.message.reply_text("🎮 اختر لعبتك:", reply_markup=InlineKeyboardMarkup(keyboard))

async def game_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "game_close":
        await query.edit_message_text("🔚 تم إغلاق الألعاب")
        return
    
    if data == "game_guess":
        number = random.randint(1, 100)
        context.user_data['guess_number'] = number
        context.user_data['game_owner'] = user_id
        await query.edit_message_text("🔢 خمن الرقم بين 1 و 100\n(أكتب رقمك)")
        context.user_data['waiting_guess'] = True
    
    elif data == "game_rps":
        context.user_data['game_owner'] = user_id
        keyboard = [
            [InlineKeyboardButton("✊ حجر", callback_data="rps_حجر")],
            [InlineKeyboardButton("✋ ورقة", callback_data="rps_ورقة")],
            [InlineKeyboardButton("✌️ مقص", callback_data="rps_مقص")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="game_back")]
        ]
        await query.edit_message_text("✊✋✌️ اختر:", reply_markup=InlineKeyboardMarkup(keyboard))
    
    elif data.startswith("rps_"):
        if context.user_data.get('game_owner') != user_id:
            return
        user_choice = data.split("_")[1]
        bot_choice = random.choice(["حجر", "ورقة", "مقص"])
        rules = {"حجر": "مقص", "ورقة": "حجر", "مقص": "ورقة"}
        
        if user_choice == bot_choice:
            result, reward = "🤝 تعادل!", 0
        elif rules[user_choice] == bot_choice:
            result, reward = "✅ فزت!", GAME_REWARD
        else:
            result, reward = "❌ خسرت!", 0
        
        if reward > 0:
            conn = get_db()
            conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
            conn.execute("UPDATE users SET messages = messages + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
        
        await query.edit_message_text(f"أنت: {user_choice}\nالبوت: {bot_choice}\n\n{result}\n💰 +{reward} عملة")
    
    elif data == "game_questions":
        q = random.choice(QUESTIONS)
        context.user_data['current_question'] = q
        context.user_data['game_owner'] = user_id
        await query.edit_message_text(f"❓ {q['q']}\n\n(أكتب إجابتك)")
        context.user_data['waiting_question'] = True
    
    elif data == "game_reverse":
        word = random.choice(REVERSE_WORDS)
        context.user_data['current_reverse'] = word
        context.user_data['game_owner'] = user_id
        await query.edit_message_text(f"🔄 اكتب الكلمة بشكل معكوس:\n{word['word']}\n\n(أكتب إجابتك)")
        context.user_data['waiting_reverse'] = True
    
    elif data == "game_lucky":
        num = random.randint(1, 10)
        context.user_data['lucky_number'] = num
        context.user_data['game_owner'] = user_id
        await query.edit_message_text(f"🎲 اختر رقم حظك من 1 إلى 10\n(أكتب رقمك)")
        context.user_data['waiting_lucky'] = True
    
    elif data == "game_box":
        context.user_data['game_owner'] = user_id
        last_box = context.user_data.get('last_lucky_box', 0)
        if time.time() - last_box < 300:
            remaining = int(300 - (time.time() - last_box))
            await query.edit_message_text(f"⏳ انتظر {remaining//60} دقيقة")
            return
        
        rand = random.randint(1, 100)
        cumulative = 0
        reward = 0
        message = ""
        for r in LUCKY_BOX_REWARDS:
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
        await query.edit_message_text(f"🎁 لوكي بوكس\n\n{message}\n💰 +{reward} عملة")
    
    elif data == "game_back":
        keyboard = [[InlineKeyboardButton(g["name"], callback_data=f"game_{g['callback']}")] for g in GAMES_MENU]
        keyboard.append([InlineKeyboardButton("🔙 إغلاق", callback_data="game_close")])
        await query.edit_message_text("🎮 اختر لعبتك:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_game_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if context.user_data.get('game_owner') != user_id:
        return
    
    if context.user_data.get('waiting_guess'):
        try:
            guess = int(text)
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
            await update.message.reply_text("❌ أرسل رقماً")
        context.user_data['waiting_guess'] = False
    
    elif context.user_data.get('waiting_question'):
        q = context.user_data.get('current_question')
        if q and is_correct(text, q['a']):
            reward = GAME_REWARD
            conn = get_db()
            conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
            conn.execute("UPDATE users SET messages = messages + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            await update.message.reply_text(f"✅ صحيح!\n💰 +{reward} عملة")
        else:
            await update.message.reply_text(f"❌ خطأ! الإجابة الصحيحة: {q['a']}")
        context.user_data['waiting_question'] = False
    
    elif context.user_data.get('waiting_reverse'):
        word = context.user_data.get('current_reverse')
        if word and is_correct(text, word['reverse']):
            reward = GAME_REWARD
            conn = get_db()
            conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
            conn.execute("UPDATE users SET messages = messages + 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            conn.close()
            await update.message.reply_text(f"✅ صحيح!\n💰 +{reward} عملة")
        else:
            await update.message.reply_text(f"❌ خطأ! الإجابة الصحيحة: {word['reverse']}")
        context.user_data['waiting_reverse'] = False
    
    elif context.user_data.get('waiting_lucky'):
        try:
            guess = int(text)
            number = context.user_data.get('lucky_number')
            if guess == number:
                reward = GAME_REWARD
                conn = get_db()
                conn.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (reward, user_id))
                conn.execute("UPDATE users SET messages = messages + 1 WHERE user_id = ?", (user_id,))
                conn.commit()
                conn.close()
                await update.message.reply_text(f"🎉 فزت! الرقم كان {number}\n💰 +{reward} عملة")
            else:
                await update.message.reply_text(f"❌ خسرت! الرقم كان {number}")
        except:
            await update.message.reply_text("❌ أرسل رقماً")
        context.user_data['waiting_lucky'] = False