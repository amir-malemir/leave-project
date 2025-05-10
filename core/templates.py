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


def fa_status(status, team=None, tornado_approval=False, zitel_approval=False):
    """
    این تابع وضعیت درخواست مرخصی را به فارسی ترجمه می‌کند.
    اگر وضعیت 'approved' باشد، بررسی می‌کند که تأییدات لازم انجام شده‌اند.
    """
    if status == 'pending_zitel':
        return "در انتظار تأیید تیم لید Zitel"
    
    elif status == 'pending':
        if team == 'Tornado':
            return "در انتظار تأیید تیم لید Tornado"
        else:
            return "در انتظار تأیید تیم لید"
    
    elif status == 'approved':
        if team == "Tornado":
            if tornado_approval and zitel_approval:
                return "تأیید شده"
            elif tornado_approval and not zitel_approval:
                return "در انتظار تأیید تیم لید Zitel"
            else:
                return "در انتظار تأیید تیم لید Tornado"
        elif team == "Zitel":
            if zitel_approval:
                return "تأیید شده"
            else:
                return "در انتظار تأیید تیم لید Zitel"
        else:
            return "تأیید شده"  # برای سایر تیم‌ها
    
    elif status == 'rejected':
        return "رد شده"
    
    else:
        return "وضعیت نامشخص"

    
templates.env.filters["fa_status"] = fa_status
    