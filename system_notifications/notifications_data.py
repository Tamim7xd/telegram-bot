# كل إشعارات البوت في مكان واحد

NOTIFICATION_CONFIG = {
    "timeout": 3,
    "border": "═",
    "icons": {
        "warning": "⚠️",
        "mute": "🔇",
        "ban": "🚫",
        "kick": "👢",
        "reward": "🎁",
        "success": "✅",
        "error": "❌",
        "info": "📢",
    }
}

def build_mute_notification(user_name, duration, reason, admin_name):
    return f"""🔇 **كتم**

👤 العضو: {user_name}
⏱️ المدة: {duration}
📝 السبب: {reason}

👮 بواسطة: {admin_name}"""

def build_ban_notification(user_name, reason, admin_name):
    return f"""🚫 **حظر**

👤 العضو: {user_name}
📝 السبب: {reason}

👮 بواسطة: {admin_name}"""

def build_warning_notification(user_name, reason, warnings_count, admin_name):
    return f"""⚠️ **تحذير**

👤 العضو: {user_name}
📝 السبب: {reason}
🔢 عدد التحذيرات: {warnings_count}

👮 بواسطة: {admin_name}"""

def build_reward_notification(user_name, amount, admin_name):
    return f"""🎁 **مكافأة**

👤 العضو: {user_name}
💰 المبلغ: {amount} عملة

👮 بواسطة: {admin_name}"""