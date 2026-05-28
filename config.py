import os

# TOKEN من البيئة (Railway / Render / VPS)
TOKEN = os.getenv("BOT_TOKEN")

# حماية: إذا التوكن غير موجود يظهر خطأ واضح بدل انهيار غامض
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود! تأكد من إعداد Environment Variables")

# باقي الإعدادات
GROUP_ID = int(os.getenv("GROUP_ID", "0"))
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
