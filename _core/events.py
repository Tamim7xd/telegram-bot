from Core_.games import start_game, check_answer, game_menu_ui
from Core_.xp import add_xp
from Core_.callbacks import panel, games_menu


async def handle_message(message):

    await check_answer(message)

    if not message.text:
        return

    text = message.text


    await add_xp(message.from_user.id, message.from_user.full_name)


    if text == "#لوحة":
        await message.answer("🎛 لوحة التحكم", reply_markup=panel())


    elif text == "#لعبة":
        await message.answer(game_menu_ui(), reply_markup=games_menu())


async def handle_callbacks(call):

    data = call.data


    if data.startswith("game_"):
        await start_game(call.message, data.replace("game_", ""))


    elif data == "games":
        await call.message.answer(game_menu_ui(), reply_markup=games_menu())


    elif data == "reward_all":
        from Core_.users import users

        for u in users.values():
            u["money"] += 100

        await call.message.answer("💰 تم توزيع المكافآت")
