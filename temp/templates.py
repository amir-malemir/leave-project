from fastapi.templating import Jinja2Templates
from models import Role
from jdatetime import date as jdate

templates = Jinja2Templates(directory="templates")

def fa_role(role):
    mapping = {
        Role.EMPLOYEE:   "کارمند",
        Role.MANAGER:    "مدیر",
        Role.SUPERVISOR: "سرپرست",
        Role.TEAM_LEAD:  "تیم لید",
        Role.SUPERADMIN: "مدیر ارشد",
    }
    return mapping.get(role, "نامشخص")

templates.env.filters["fa_role"] = fa_role


# jalali_filter
def jalali_filter(dt, fmt="%Y/%m/%d"):
    if not dt:
        return ""
    try:
        return jdate.fromgregorian(date=dt).strftime(fmt)
    except:
        return str(dt)
templates.env.filters["jdate"] = jalali_filter


def fa_status(status, team=None, tornado_approval=False, zitel_approval=False):
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
            return "تأیید شده"
    
    elif status == 'rejected':
        return "رد شده"
    
    else:
        return "وضعیت نامشخص"

    
templates.env.filters["fa_status"] = fa_status
    