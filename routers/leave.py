from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import Optional, List
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from datetime import date
from dependencies import get_db
from models import LeaveRequest, User
from .auth import get_current_user
import jdatetime
from schemas import LeaveRequestOut


router = APIRouter()

templates = Jinja2Templates(directory="templates")

AUTHORIZED_ROLES = ["admin", "manager", "team_lead", "supervisor"]

# مدل پایتون جهت ثبت درخواست مرخصی
class LeaveRequestCreate(BaseModel):
    start_date: date
    end_date: date
    reason: str = None

# leave request
@router.get("/create-leave-request", response_class=HTMLResponse)
async def create_leave_request_page(request: Request):
    """
    صفحه ایجاد درخواست مرخصی
    """
    return templates.TemplateResponse("create_leave_request.html", {"request": request})


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
def show_user_leave_requests_page(request: Request):
    return templates.TemplateResponse("user_leave_requests.html", {"request": request})

@router.get("/user-leave-requests", tags=["leave"])
def get_user_leave_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # احراز هویت کاربر
):
    """
    دریافت لیست درخواست‌های مرخصی کاربر فعلی
    """
    try:
        leave_requests = db.query(LeaveRequest).filter(
            LeaveRequest.user_id == current_user.id
        ).all()

        # تبدیل تاریخ‌ها به شمسی
        leave_requests_shamsi = []
        for request in leave_requests:
            leave_requests_shamsi.append({
                "id": request.id,
                "username": current_user.username,  # این خط اضافه بشه
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
    # # سوپرادمین می‌تواند تمام درخواست‌ها را مشاهده کند
    # if current_user.role == "manager":  #SUPERUSER
    #     return db.query(LeaveRequest).all()

    # # مدیر، سوپروایزر و تیم لید فقط می‌توانند درخواست‌های مربوط به واحد خودشان را مشاهده کنند
    # elif current_user.role in ["manager", "supervisor", "team_lead"]:
    #     return db.query(LeaveRequest).join(User).filter(User.unit == current_user.unit).all()

    # # کارمند فقط می‌تواند درخواست‌های خودش را مشاهده کند
    # elif current_user.role == "employee":
    #     return db.query(LeaveRequest).filter(LeaveRequest.user_id == current_user.id).all()

    # # اگر نقش کاربر مشخص نیست، دسترسی ممنوع است
    # raise HTTPException(
    #     status_code=status.HTTP_403_FORBIDDEN,
    #     detail="شما دسترسی لازم برای مشاهده درخواست‌ها را ندارید"
    # )


# @router.put("/leave/{leave_id}/status", tags=["leave"])
# def update_leave_status(
#     leave_id: int,
#     status: str,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role not in ["manager", "supervisor"]:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="شما اجازه تغییر وضعیت درخواست‌ها را ندارید."
#         )

#     leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
#     if not leave_request:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="درخواست مرخصی یافت نشد."
#         )

#     leave_request.status = status
#     db.commit()
#     db.refresh(leave_request)
#     return leave_request



# @router.put("/leave/{leave_id}/status", tags=["leave"])
# def update_leave_status(
#     leave_id: int,
#     status: str,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     # بررسی نقش کاربر
#     if current_user.role not in ["manager", "supervisor", "team_lead"]:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="شما اجازه تغییر وضعیت درخواست‌ها را ندارید."
#         )

#     # پیدا کردن درخواست مرخصی
#     leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
#     if not leave_request:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="درخواست مرخصی یافت نشد."
#         )

#     # پیدا کردن کاربری که درخواست مرخصی را ثبت کرده است
#     request_user = db.query(User).filter(User.id == leave_request.user_id).first()
#     if not request_user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="کاربری که درخواست مرخصی را ثبت کرده است یافت نشد."
#         )

#     # منطق دسترسی بر اساس نقش
#     if current_user.role == "team_lead":
#         # تیم لید فقط می‌تواند درخواست‌های مربوط به بخش خودش را تغییر دهد
#         if request_user.unit != current_user.unit:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="تیم لید فقط می‌تواند وضعیت درخواست‌های بخش خودش را تغییر دهد."
#             )

#     elif current_user.role == "supervisor":
#         # سوپروایزر فقط می‌تواند درخواست‌های مربوط به بخش خودش را تغییر دهد
#         if request_user.unit != current_user.unit:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="سوپروایزر فقط می‌تواند وضعیت درخواست‌های بخش خودش را تغییر دهد."
#             )

#     # مدیر نیازی به محدودیت ندارد و می‌تواند همه درخواست‌ها را تغییر دهد

#     # تغییر وضعیت درخواست
#     leave_request.status = status
#     db.commit()
#     db.refresh(leave_request)
#     return leave_request



# @router.get("/leave-report", tags=["leave"])
# def leave_report(
#     start_date: date,
#     end_date: date,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role != "manager":
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="شما اجازه دسترسی به گزارش‌ها را ندارید."
#         )

#     approved_count = db.query(LeaveRequest).filter(
#         LeaveRequest.status == "approved",
#         LeaveRequest.start_date >= start_date,
#         LeaveRequest.end_date <= end_date
#     ).count()

#     rejected_count = db.query(LeaveRequest).filter(
#         LeaveRequest.status == "rejected",
#         LeaveRequest.start_date >= start_date,
#         LeaveRequest.end_date <= end_date
#     ).count()

#     return {
#         "approved_requests": approved_count,
#         "rejected_requests": rejected_count
#     }

# all request 
@router.get("/all-leave-requests-page", response_class=HTMLResponse)
async def all_leave_requests_page(request: Request, current_user: User = Depends(get_current_user)):
    if current_user.role.lower() not in [role.lower() for role in AUTHORIZED_ROLES]:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    
    return templates.TemplateResponse("all_leave_requests.html", {"request": request})


@router.get("/all-leave-requests")
def get_all_leave_requests(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    print(current_user)
    if current_user.role.lower() not in [role.lower() for role in AUTHORIZED_ROLES]:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    
    leave_requests = db.query(LeaveRequest).options(joinedload(LeaveRequest.user)).all()
    result = []
    for req in leave_requests:
        result.append({
            "id": req.id,
            "startDate": req.start_date.strftime("%Y-%m-%d"),
            "endDate": req.end_date.strftime("%Y-%m-%d"),
            "status": req.status,
            "reason": req.reason,
            "user": {
                "id": req.user.id,
                "username": req.user.username,
                "email": req.user.email,
                "fullName": req.user.full_name,
                "role": req.user.role,
            }
        })
    
    return result