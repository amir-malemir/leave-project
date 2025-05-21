from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel, EmailStr
from dependencies import get_db
from models import User, LeaveRequest
from .auth import get_password_hash, verify_password, create_access_token
from typing import Optional, List
from .auth import get_current_user
from starlette.status import HTTP_302_FOUND
from fastapi.responses import RedirectResponse, HTMLResponse
from core.templates import templates
from starlette.requests import Request
from schemas import UserOut, RoleUpdate
from datetime import date
from enum import Enum
import jdatetime

router = APIRouter()

AUTHORIZED_ROLES = ["admin", "manager", "supervisor", "team_lead"]

# مدل پایتون برای دریافت اطلاعات کاربر جهت ثبت در دیتابیس
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    phone_number: str
    unit: str
    level: str
    role: str = "employee"
    password: str
    team: Optional[str] = None
    
# مدل پایتون برای دریافت اطلاعات لاگین
class UserLogin(BaseModel):
    username: str
    password: str


class Role(str, Enum):
    EMPLOYEE = "employee"
    TEAM_LEAD = "team_lead"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    ADMIN = "admin"


def can_change_password(editor: User, target_user: User) -> bool:
    # ادمین می‌تواند رمز همه را تغییر دهد
    if editor.role == "admin":
        return True
    
    # مدیر می‌تواند رمز همه به جز ادمین را تغییر دهد
    if editor.role == "manager":
        return target_user.role != "admin"
    
    # سوپروایزر می‌تواند رمز همه به جز مدیر و ادمین را تغییر دهد
    if editor.role == "supervisor":
        return target_user.role not in ["manager", "admin"]
    
    # تیم لید Zitel
    if editor.role == "zitel_team_lead":
        return target_user.role in ["inbound_zitel", "outbound", "ahd", "tornado_team_lead"]
    
    # تیم لید Tornado
    if editor.role == "tornado_team_lead":
        return target_user.role == "inbound_tornado"
    
    return False

def can_edit_user(editor: User, target_user: User, new_role: str = None) -> bool:
    # ادمین می‌تواند همه را ویرایش کند
    if editor.role == "admin":
        return True
    
    # مدیر می‌تواند همه به جز ادمین را ویرایش کند
    if editor.role == "manager":
        return target_user.role != "admin"
    
    # سوپروایزر می‌تواند کاربران زیردست خود را ویرایش کند
    if editor.role == "supervisor":
        allowed_roles = [
            "team_lead",
            "inbound_zitel",
            "inbound_tornado",
            "outbound",
            "ahd",
            "noc_team_lead",
            "noc_ecs",
            "noc_fo",
            "noc_ops"
        ]
        return target_user.role in allowed_roles and (new_role in allowed_roles if new_role else True)
    
    # تیم لید callcenter
    if editor.role == "team_lead":
        return target_user.role in ["inbound_zitel", "inbound_tornado", "outbound", "ahd"]
    
    # تیم لید noc
    if editor.role == "noc_team_lead":
        return target_user.role in ["noc_ecs", "noc_fo", "noc_ops"]
    
    return False

def validate_unit_level_team(
    unit: str,
    level: str,
    team: Optional[str] = None
) -> bool:
    valid_team_levels = {
        "callcenter": {
            "zitel": ["inbound", "outbound", "ahd"],
            "tornado": ["inbound"]
        },
        "noc": {
            "zitel": ["ecs", "fo", "ops"]
        }
    }

    unit = unit.lower()
    level = level.lower()
    team = (team or "").lower()

    if unit not in valid_team_levels:
        return False

    if team not in valid_team_levels[unit]:
        return False

    if level not in valid_team_levels[unit][team]:
        return False

    return True


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.post("/register", response_class=HTMLResponse)
def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    full_name: str = Form(...),
    phone_number: str = Form(...),
    unit: str = Form(...),
    team: Optional[str] = Form(None),
    level: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "رمز عبور و تکرار آن یکسان نیستند."
        })

    if not validate_unit_level_team(unit, level, team):
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "ترکیب سطح/تیم/واحد نامعتبر است."
        })

    if db.query(User).filter(User.username == username).first():
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "کاربری با این نام وجود دارد."
        })

    hashed_password = get_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        phone_number=phone_number,
        unit=unit,
        level=level,
        team=team,
        hashed_password=hashed_password,
        role="employee"
    )
    db.add(new_user)
    db.commit()

    return RedirectResponse("/login", status_code=302)

@router.get("/dashboard", response_class=HTMLResponse, tags=["dashboard"])
def dashboard_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = date.today()

    total_requests = db.query(LeaveRequest).filter(LeaveRequest.user_id == current_user.id).count()
    approved_requests = db.query(LeaveRequest).filter(
        LeaveRequest.user_id == current_user.id,
        LeaveRequest.status == "approved"
    ).count()
    rejected_requests = db.query(LeaveRequest).filter(
        LeaveRequest.user_id == current_user.id,
        LeaveRequest.status == "rejected"
    ).count()
    pending_requests = db.query(LeaveRequest).filter(
        LeaveRequest.user_id == current_user.id,
        LeaveRequest.status.in_(["pending", "pending_zitel"])
    ).count()

    leave_today = []
    if current_user.role in ["admin", "manager", "supervisor", "team_lead"]:
        leave_today = (
            db.query(LeaveRequest)
            .join(User, LeaveRequest.user_id == User.id)  # ✅ این خط
            .filter(
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= today,
                LeaveRequest.status == "approved"
            )
            .options(joinedload(LeaveRequest.user))
            .all()
        )

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user_role": current_user.role,
        "total_requests": total_requests,
        "approved_requests": approved_requests,
        "rejected_requests": rejected_requests,
        "pending_requests": pending_requests,
        "leave_today": leave_today
    })
# مسیر API برای لاگین
# @router.post("/login", tags=["users"])
# def login(user_data: UserLogin, db: Session = Depends(get_db)):
#     # بررسی وجود کاربر
#     db_user = db.query(User).filter(User.username == user_data.username).first()
#     if not db_user or not verify_password(user_data.password, db_user.hashed_password):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="نام کاربری یا رمز عبور اشتباه است"
#         )
    
#     # ایجاد توکن دسترسی
#     access_token = create_access_token(data={"sub": db_user.username})
#     return {"access_token": access_token, "token_type": "bearer"}

# مسیر صفحه لاگین
@router.get("/login", response_class=HTMLResponse, tags=["users"])
def login_page(request: Request):
    print("Login page rendered") 
    return templates.TemplateResponse("login.html", {"request": request})



@router.post("/login", response_class=HTMLResponse)
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "نام کاربری یا رمز عبور اشتباه است!"
        })

    access_token = create_access_token(data={"sub": str(user.id)})  # ✅ باید ID باشد
    response = RedirectResponse(url="/dashboard", status_code=302)

    # در محیط لوکال secure=False بگذار
    response.set_cookie(
        key="access_token",
        value=access_token,  # فقط خود توکن، بدون "Bearer "
        httponly=True,
        samesite="Strict",
        secure=False
    )
    return response


@router.post("/logout")
def logout_user():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response

@router.get("/user-management-page", response_class=HTMLResponse)
def user_management_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == "manager":
        users = db.query(User).all()
    elif current_user.role in ["supervisor", "team_lead"]:
        users = db.query(User).filter(User.unit == current_user.unit).all()
    else:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    return templates.TemplateResponse("user_management.html", {"request": request, "users": users, "user_role": current_user.role})


@router.put("/user-management/{user_id}/role")
def update_user_role(
    user_id: int,
    role_update: RoleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")
    
    if not can_edit_user(current_user, target_user, role_update.role):
        raise HTTPException(
            status_code=403,
            detail="شما مجوز تغییر نقش این کاربر را ندارید"
        )
    
    if not validate_unit_level_team(unit=target_user.unit, level=target_user.level, team=target_user.team):

        raise HTTPException(
            status_code=400,
            detail="نقش انتخاب شده با واحد کاربر سازگار نیست"
        )
    
    target_user.role = role_update.role
    db.commit()
    return {"message": "نقش کاربر با موفقیت تغییر کرد"}

@router.get("/edit-user/{user_id}", response_class=HTMLResponse)
def edit_user_page(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")
    
    if not can_edit_user(current_user, user):
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    
    return templates.TemplateResponse("edit_user.html", {
        "request": request,
        "user_to_edit": user,
        "user_role": current_user.role,
    })

@router.post("/edit-user/{user_id}")
def update_user(
    user_id: int,
    full_name: str = Form(...),
    email: str = Form(...),
    unit: str = Form(...),
    role: str = Form(...),
    new_password: str = Form(None),
    level: str = Form(...),
    team: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")
    
    # بررسی مجوز ویرایش
    if not can_edit_user(current_user, target_user):
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    
    # بررسی مجوز تغییر رمز (اگر رمز جدید ارائه شده)
    if new_password and not can_change_password(current_user, target_user):
        raise HTTPException(status_code=403, detail="شما مجوز تغییر رمز این کاربر را ندارید")
    
    # اعتبارسنجی واحد و نقش
    if not validate_unit_level_team(
        unit=unit,
        level=level,
        team=team
    ):
        raise HTTPException(
            status_code=400,
            detail="ترکیب واحد/سطح/تیم نامعتبر است"
        )
    # اعمال تغییرات
    target_user.full_name = full_name
    target_user.email = email
    target_user.unit = unit
    target_user.role = role
    
    # اگر رمز جدید ارائه شده، آن را اعمال کن
    if new_password:
        target_user.hashed_password = get_password_hash(new_password)
    
    db.commit()
    return RedirectResponse(url="/user-management-page", status_code=302)

@router.post("/delete-user/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="فقط مدیر می‌تواند کاربران را حذف کند")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")

    db.delete(user)
    db.commit()
    return RedirectResponse(url="/user-management-page", status_code=302)


@router.get("/settings", response_class=HTMLResponse)
def settings_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": current_user,
        "user_role": current_user.role,
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
        current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    return RedirectResponse(url="/settings", status_code=HTTP_302_FOUND)
