def get_title(money, level):

    if money >= 1000000:
        return "👑 أسطورة VIP"
    elif money >= 500000:
        return "🔥 VIP محترف"
    elif money >= 200000:
        return "⭐ لاعب قوي"
    elif level >= 10:
        return "⚡ نشيط"
    elif level >= 5:
        return "🎮 لاعب"
    else:
        return "👤 مبتدئ"
