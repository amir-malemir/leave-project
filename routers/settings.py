from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from models import User, AdminSetting
from dependencies import get_db
from routers.auth import get_current_user
from starlette.status import HTTP_302_FOUND
from fastapi.templating import Jinja2Templates



router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/settings", response_class=HTMLResponse)
def settings_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": current_user
    })

@router.post("/update-profile")
def update_profile(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    new_password: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    current_user.full_name = full_name
    current_user.email = email
    if new_password:
        current_user.set_password(new_password)  # تابعی که رمز رو هش می‌کنه
    db.commit()
    return RedirectResponse(url="/settings", status_code=HTTP_302_FOUND)

# router = APIRouter()
# templates = Jinja2Templates(directory="templates")


# @router.get("/settings", response_class=HTMLResponse)
# def settings_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
#     admin_settings = db.query(AdminSetting).first()
#     if not admin_settings:
#         admin_settings = AdminSetting(max_leave_days=30, default_shift="A")
#         db.add(admin_settings)
#         db.commit()
#         db.refresh(admin_settings)

#     shift_names = ["A", "B", "C", "D", "E", "OFF"]

#     return templates.TemplateResponse("settings.html", {
#         "request": request,
#         "user": current_user,
#         "admin_settings": admin_settings,
#         "shift_names": shift_names
#     })


# @router.post("/update-profile")
# def update_profile(
#     request: Request,
#     full_name: str = Form(...),
#     email: str = Form(...),
#     new_password: str = Form(None),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     current_user.full_name = full_name
#     current_user.email = email
#     if new_password:
#         current_user.set_password(new_password)  # فرض بر اینه تابع داره
#     db.commit()
#     return RedirectResponse(url="/settings", status_code=HTTP_302_FOUND)


# @router.post("/admin-settings")
# def update_admin_settings(
#     max_leave_days: int = Form(...),
#     default_shift: str = Form(None),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role not in ["admin", "manager", "supervisor", "team_lead"]:
#         raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")

#     settings = db.query(AdminSetting).first()
#     if settings:
#         settings.max_leave_days = max_leave_days
#         settings.default_shift = default_shift
#     else:
#         settings = AdminSetting(max_leave_days=max_leave_days, default_shift=default_shift)
#         db.add(settings)
#     db.commit()
#     return RedirectResponse(url="/settings", status_code=HTTP_302_FOUND)