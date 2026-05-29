from Core_.users import get_user
from Core_.notify import send_notify


async def add_xp(uid, name):

    u = await get_user(uid)

    u["xp"] += 5
    u["money"] += 50

    need = u["level"] * 100

    leveled = False

    if u["xp"] >= need:
        u["xp"] -= need
        u["level"] += 1
        leveled = True

    if leveled:
        await send_notify(
            uid,
            "LEVEL UP",
            f"🎉 وصلت مستوى {u['level']}\n💰 +50 مكافأة\n🏆 استمر!",
            "🔥"
        )

    return leveled
