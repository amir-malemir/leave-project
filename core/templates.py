from fastapi.templating import Jinja2Templates
from models import Role
from jdatetime import date as jdate

templates = Jinja2Templates(directory="templates")

def fa_role(role):
    """
    این تابع یک شیء Enum از کلاس Role می‌گیرد و معادل فارسی‌شده‌اش را برمی‌گرداند.
    """
    mapping = {
        Role.EMPLOYEE:   "کارمند",
        Role.MANAGER:    "مدیر",
        Role.SUPERVISOR: "سرپرست",
        Role.TEAM_LEAD:  "تیم لید",
        Role.SUPERADMIN: "مدیر ارشد",
    }
    return mapping.get(role, "نامشخص")

# این سطر حتماً باید بعد از تعریف تابع بیاید
templates.env.filters["fa_role"] = fa_role

# تنظیم فیلتر سفارشی
def jalali_filter(dt, fmt="%Y/%m/%d"):
    if not dt:
        return ""
    try:
        return jdate.fromgregorian(date=dt).strftime(fmt)
    except:
        return str(dt)
templates.env.filters["jdate"] = jalali_filter