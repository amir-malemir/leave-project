# core/templates.py
from fastapi.templating import Jinja2Templates
from models import Role        # مسیر رو با پروژه‌ت تنظیم کن

templates = Jinja2Templates(directory="templates")

def fa_role(role):
    """
    این تابع یک شیء Enum از کلاس Role می‌گیرد و معادل فارسی‌شده‌اش را برمی‌گرداند.
    """
    mapping = {
        Role.EMPLOYEE:   "کارمند",
        Role.MANAGER:    "مدیر",
        Role.SUPERVISOR: "سرپرست",
        Role.TEAM_LEAD:  "رهبر تیم",
        Role.SUPERADMIN: "مدیر ارشد",
    }
    return mapping.get(role, "نامشخص")

# این سطر حتماً باید بعد از تعریف تابع بیاید
templates.env.filters["fa_role"] = fa_role
