from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

def fa_role(role):
    mapping = {
        "Role.EMPLOYEE": "کارمند",
        "Role.MANAGER": "مدیر",
        "Role.SUPERVISOR": "سرپرست",
        "Role.TEAM_LEAD": "رهبر تیم",
    }
    return mapping.get(role, "نامشخص")

templates.env.filters["fa_role"] = fa_role