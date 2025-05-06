from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional, List
from fastapi.responses import HTMLResponse, RedirectResponse
from core.templates import templates
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from datetime import date, datetime
from dependencies import get_db
from models import LeaveRequest, User
from .auth import get_current_user
from schemas import LeaveRequestOut, UserUpdate
import jdatetime


router = APIRouter()

# templates = Jinja2Templates(directory="templates")

AUTHORIZED_ROLES = ["admin", "manager", "supervisor", "team_lead"]

# مدل پایتون جهت ثبت درخواست مرخصی
class LeaveRequestCreate(BaseModel):
    start_date: date
    end_date: date
    reason: str = None

class LeaveUpdate(BaseModel):
    status: str
    reason: Optional[str] = None

def gregorian_to_shamsi(gregorian_date):
    """تبدیل تاریخ میلادی به شمسی"""
    if not gregorian_date:
        return "-"
    try:
        jdate = jdatetime.date.fromgregorian(date=gregorian_date)
        return jdate.strftime("%Y/%m/%d")
    except Exception as e:
        print(f"Error converting date: {e}")
        return str(gregorian_date)  # در صورت خطا تاریخ میلادی را برگردان

# leave request
@router.get("/create-leave-request", response_class=HTMLResponse)
async def create_leave_request_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("create_leave_request.html", {"request": request, "user_role": current_user.role})


@router.post("/leave_request", tags=["leave"])
def create_leave_request(
    leave_data: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # تبدیل تاریخ‌های شمسی به میلادی
        try:
            today = date.today()

            if leave_data.start_date < today or leave_data.end_date < today:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="تاریخ شروع یا پایان نمی‌تواند قبل از امروز باشد."
                )
            # تبدیل تاریخ‌های شمسی به میلادی
            start_date_gregorian = leave_data.start_date
            end_date_gregorian = leave_data.end_date

            print(f"Received Start Date (Gregorian): {start_date_gregorian}")
            print(f"Received End Date (Gregorian): {end_date_gregorian}")

        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="فرمت تاریخ نامعتبر است. لطفاً تاریخ‌ها را به فرمت YYYY-MM-DD ارسال کنید."
            )
        
        # بررسی وجود درخواست مرخصی تکراری برای کاربر فعلی
        existing_user_request = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == current_user.id,
            LeaveRequest.start_date <= end_date_gregorian,
            LeaveRequest.end_date >= start_date_gregorian
        ).first()

        if existing_user_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="شما قبلاً برای این بازه زمانی درخواست مرخصی ثبت کرده‌اید."
            )

        # بررسی وجود درخواست مرخصی در سطح کاربر فعلی
        existing_level_request = db.query(LeaveRequest).filter(
            LeaveRequest.level == current_user.level,
            LeaveRequest.start_date <= end_date_gregorian,
            LeaveRequest.end_date >= start_date_gregorian
        ).first()

        if existing_level_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="در این بازه زمانی، کاربری در سطح شما قبلاً درخواست مرخصی ثبت کرده است."
            )

        # ایجاد درخواست جدید
        new_leave = LeaveRequest(
            user_id=current_user.id,
            start_date=start_date_gregorian,
            end_date=end_date_gregorian,
            reason=leave_data.reason,
            status="pending", 
            level=current_user.level
        )

        db.add(new_leave)
        db.commit()
        db.refresh(new_leave)

        # بازگشت اطلاعات درخواست جدید
        return {
            "id": new_leave.id,
            "start_date": leave_data.start_date,
            "end_date": leave_data.end_date,
            "reason": new_leave.reason,
            "status": new_leave.status
        }

    except Exception as e:
        print(f"Error: {str(e)}")  # چاپ خطا در کنسول
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در ثبت درخواست مرخصی: {str(e)}"
        )

@router.get("/leave-requests-page", response_class=HTMLResponse)
def show_user_leave_requests_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("user_leave_requests.html", {"request": request, "user_role": current_user.role})

@router.get("/user-leave-requests", tags=["leave"])
def get_user_leave_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        leave_requests = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == current_user.id
        ).all()

        # تبدیل تاریخ‌ها به شمسی
        leave_requests_shamsi = []
        for request in leave_requests:
            leave_requests_shamsi.append({
                "id": request.id,
                "username": current_user.username,
                "start_date": jdatetime.date.fromgregorian(date=request.start_date).strftime("%Y/%m/%d"),
                "end_date": jdatetime.date.fromgregorian(date=request.end_date).strftime("%Y/%m/%d"),
                "reason": request.reason,
                "status": request.status
            })

        return leave_requests_shamsi
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="خطا در دریافت لیست درخواست‌های مرخصی"
        )

@router.get("/all-leave-requests-page", response_class=HTMLResponse)
def all_leave_requests_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.lower() not in AUTHORIZED_ROLES:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    
    if current_user.role == "team_lead":
        if current_user.team == "Tornado":
            leave_requests = (
                db.query(LeaveRequest)
                .join(User, LeaveRequest.user_id == User.id)
                .filter(User.team == "Tornado")
                .options(joinedload(LeaveRequest.user))
                .order_by(LeaveRequest.start_date.desc())
                .all()
            )
    else:
        leave_requests = (
            db.query(LeaveRequest)
            .options(joinedload(LeaveRequest.user))
            .order_by(LeaveRequest.start_date.desc())
            .all()
        )
    
    # تبدیل تاریخ‌ها
    for req in leave_requests:
        req.start_date_shamsi = gregorian_to_shamsi(req.start_date)
        req.end_date_shamsi = gregorian_to_shamsi(req.end_date)
    
    return templates.TemplateResponse(
        "all_leave_requests.html",
        {
            "request": request,
            "leave_requests": leave_requests,
            "current_user": current_user,
            "user_role": current_user.role,
        }
    )

@router.get("/edit-leave-request/{request_id}", response_class=HTMLResponse)
def edit_leave_page(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.lower() not in AUTHORIZED_ROLES:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    
    leave_request = db.query(LeaveRequest).filter(
        LeaveRequest.id == request_id
    ).first()
    
    if not leave_request:
        raise HTTPException(status_code=404, detail="درخواست پیدا نشد")
    
    return templates.TemplateResponse(
        "edit_leave.html",
        {
            "request": request,
            "leave": leave_request,
            "current_user": current_user,
            "user_role": current_user.role,
        }
    )

@router.post("/update-leave-request/{request_id}")
async def update_leave_request(
    request_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.lower() not in AUTHORIZED_ROLES:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    
    form_data = await request.form()
    leave = db.query(LeaveRequest).filter(
        LeaveRequest.id == request_id
    ).first()
    
    if not leave:
        raise HTTPException(status_code=404, detail="درخواست پیدا نشد")
    
    # اعتبارسنجی وضعیت
    valid_statuses = ["pending", "approved", "rejected"]
    if form_data.get("status") not in valid_statuses:
        raise HTTPException(status_code=400, detail="وضعیت نامعتبر")
    
    # اعمال تغییرات
    leave.status = form_data.get("status")
    leave.reason = form_data.get("reason")
    leave.manager_comment = form_data.get("manager_comment")
    leave.updated_at = datetime.utcnow()
    
    # اگر وضعیت به تأیید/رد تغییر کرد، مدیر تأییدکننده را ثبت کنید
    if form_data.get("status") in ["approved", "rejected"]:
        leave.approved_by = current_user.id
        leave.approved_at = datetime.utcnow()
    
    db.commit()
    
    return RedirectResponse(
        url="/all-leave-requests-page",
        status_code=303
    )