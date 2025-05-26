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
from temp.templates import templates
from starlette.requests import Request
from schemas import UserOut, RoleUpdate
from datetime import date
from enum import Enum
import jdatetime

router = APIRouter()

AUTHORIZED_ROLES = ["admin", "manager", "supervisor", "team_lead"]

# کاربر جدید
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
    
# لاگین
class UserLogin(BaseModel):
    username: str
    password: str


class Role(str, Enum):
    EMPLOYEE = "employee"
    TEAM_LEAD = "team_lead"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    ADMIN = "admin"


def can_change_password(editor: User, target: User) -> bool:
    if editor.role == "admin":
        return True

    if editor.role == "manager":
        return target.role != "admin"

    if editor.role == "supervisor":
        return target.role not in ["admin", "manager"]

    if editor.role == "zitel_team_lead":
        return target.role in ["inbound_zitel", "outbound", "ahd", "tornado_team_lead"]

    if editor.role == "tornado_team_lead":
        return target.role == "inbound_tornado"

    return False

def can_edit_user(editor: User, target: User, new_role: Optional[str] = None) -> bool:
    if editor.role == "admin":
        return True

    if editor.role == "manager":
        return target.role != "admin"

    if editor.role == "supervisor":
        allowed = [
            "team_lead", "inbound_zitel", "inbound_tornado",
            "outbound", "ahd", "noc_team_lead", "noc_ecs", "noc_fo", "noc_ops"
        ]
        return target.role in allowed and (new_role in allowed if new_role else True)

    if editor.role == "team_lead":
        return target.role in ["inbound_zitel", "inbound_tornado", "outbound", "ahd"]

    if editor.role == "noc_team_lead":
        return target.role in ["noc_ecs", "noc_fo", "noc_ops"]

    return False

def validate_unit_level_team(unit: str, level: str, team: Optional[str] = None) -> bool:
    unit = unit.lower()
    level = level.lower()
    team = (team or "").lower()

    if unit == "callcenter":
        if team == "zitel" and level in ["inbound", "outbound", "ahd"]:
            return True
        if team == "tornado" and level == "inbound":
            return True

    elif unit == "noc":
        if team == "zitel" and level in ["ecs", "fo", "ops"]:
            return True

    return False


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
            .join(User, LeaveRequest.user_id == User.id)
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

# مسیر صفحه لاگین
@router.get("/login", response_class=HTMLResponse, tags=["users"])
def login_page(request: Request):
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

    access_token = create_access_token(data={"sub": str(user.id)})
    response = RedirectResponse(url="/dashboard", status_code=302)

    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="Strict",
        secure=False
    )
    return response


@router.post("/logout")
def logout_get():
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
    
    #  ویرایش
    if not can_edit_user(current_user, target_user):
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    
    # رمز جدید
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

    target_user.full_name = full_name
    target_user.email = email
    target_user.unit = unit
    target_user.role = role
    
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
