from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from dependencies import get_db
from models import User, LeaveRequest
from .auth import get_password_hash, verify_password, create_access_token
from typing import Optional, List
from .auth import get_current_user
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from schemas import UserOut, RoleUpdate


router = APIRouter()


templates = Jinja2Templates(directory="templates")

# مدل پایتون برای دریافت اطلاعات کاربر جهت ثبت در دیتابیس
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    phone_number: str
    unit: str
    level: str
    role: Optional[str] = "employee"
    password: str
    
# مدل پایتون برای دریافت اطلاعات لاگین
class UserLogin(BaseModel):
    username: str
    password: str


@router.get("/register", response_class=HTMLResponse, tags=["users"])
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/users", tags=["users"])
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        # بررسی مقادیر معتبر برای واحد و سطح
        valid_units = ["callcenter", "noc"]
        valid_levels = {
            "callcenter": ["inbound", "outbound", "ahd"],
            "noc": ["ecs", "fo"]
        }

        if user_data.unit not in valid_units:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="واحد انتخاب‌شده معتبر نیست"
            )

        if user_data.level not in valid_levels[user_data.unit]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="سطح انتخاب‌شده معتبر نیست"
            )

        # بررسی وجود کاربر با نام کاربری مشابه
        db_user = db.query(User).filter(User.username == user_data.username).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="کاربر با این نام کاربری وجود دارد"
            )

        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            unit=user_data.unit,
            level=user_data.level,
            role=user_data.role.lower(),
            hashed_password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        print(f"خطای سمت سرور: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطایی در سمت سرور رخ داد"
        )

@router.get("/dashboard", response_class=HTMLResponse, tags=["dashboard"])
def dashboard_page(request: Request):
    """
    نمایش صفحه داشبورد بدون نیاز به احراز هویت.
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/dashboard-data", tags=["dashboard"])
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    دریافت اطلاعات داشبورد برای کاربر جاری.
    """
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
        LeaveRequest.status == "pending"
    ).count()

    return {
        "total_requests": total_requests,
        "approved_requests": approved_requests,
        "rejected_requests": rejected_requests,
        "pending_requests": pending_requests
    }

# مسیر صفحه لاگین
@router.get("/login", response_class=HTMLResponse, tags=["users"])
def login_page():
    return templates.TemplateResponse("login.html", {"request": {}})

# مسیر API برای لاگین
@router.post("/login", tags=["users"])
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    # بررسی وجود کاربر
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if not db_user or not verify_password(user_data.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است"
        )
    
    # ایجاد توکن دسترسی
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/user-management-page", response_class=HTMLResponse, tags=["users"])
def user_management_page(request: Request):
    """
    نمایش صفحه مدیریت کاربران.
    """
    return templates.TemplateResponse("user_management.html", {"request": request})


@router.get("/user-management", response_model=List[UserOut], tags=["users"])
def get_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    دریافت لیست کاربران برای مدیریت.
    """
    if current_user.role == "manager":
        return db.query(User).all()
    elif current_user.role in ["supervisor", "team_lead"]:
        return db.query(User).filter(User.unit == current_user.unit).all()
    else:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")

@router.put("/user-management/{user_id}/role")
def update_user_role(user_id: int, role_update: RoleUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "manager":
        raise HTTPException(status_code=403, detail="فقط مدیر می‌تواند نقش کاربران را تغییر دهد")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")
    user.role = role_update.role
    db.commit()
    return {"message": "نقش کاربر با موفقیت تغییر کرد"}