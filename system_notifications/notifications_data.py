
NOTIFICATION_CONFIG = {
    "timeout": 5,
    "border": "═",
    "icons": {
        "warning": "⚠️",
        "mute": "🔇",
        "ban": "🚫",
        "kick": "👢",
        "reward": "🎁",
        "unmute": "🔓",
        "unban": "🔓",
        "success": "✅",
        "error": "❌",
        "info": "📢",
        "backup": "💾",
        "game": "🎮",
        "shop": "🛒",
    }
}

def build_notification(title, icon, content, admin_name):
    return f"""{icon} **{title}**

{content}

👮 بواسطة: {admin_name}"""

def build_warning_notification(user_name, reason, warnings_count, admin_name):
    return f"""⚠️ **تحذير**

👤 {user_name}
📝 {reason}
🔢 {warnings_count}

👮 {admin_name}"""

def build_mute_notification(user_name, duration, reason, admin_name):
    return f"""🔇 **كتم**

👤 {user_name}
⏱️ {duration}
📝 {reason}

👮 {admin_name}"""