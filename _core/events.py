from Core_.users import users


def profile(uid):

    u = users[uid]

    win_rate = 0
    if u["games"] > 0:
        win_rate = round((u["wins"] / u["games"]) * 100, 1)

    return (
        f"👤 PROFILE\n"
        f"━━━━━━━━━━━━━━\n"
        f"🆔 ID: {u['id']}\n"
        f"👤 Name: {u['name']}\n"
        f"💰 Money: {u['money']}\n"
        f"⭐ XP: {u['xp']}\n"
        f"🏆 Level: {u['level']}\n"
        f"🎖 Title: {u['title']}\n"
        f"🎮 Games: {u['games']}\n"
        f"🏅 Wins: {u['wins']}\n"
        f"💀 Losses: {u['losses']}\n"
        f"📊 WinRate: {win_rate}%\n"
        f"━━━━━━━━━━━━━━"
    )
