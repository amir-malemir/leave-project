from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from dependencies import get_db
from models import LeaveRequest, User
from .auth import get_current_user

router = APIRouter()

# مدل پایتون جهت ثبت درخواست مرخصی
class LeaveRequestCreate(BaseModel):
    start_date: date
    end_date: date
    reason: str = None

@router.post("/leave", tags=["leave"])
def create_leave_request(
    leave_data: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        print("Request received at /leave")  # بررسی دریافت درخواست
        print(f"Current User: {current_user}")  # چاپ اطلاعات کاربر
        print(f"User ID: {current_user.id}, Level: {current_user.level}, Role: {current_user.role}")

        # بررسی وجود درخواست تایید شده در سطح کاربر
        existing_request = db.query(LeaveRequest).filter(
            LeaveRequest.level == current_user.level,
            LeaveRequest.status == "approved"
        ).first()
        print(f"Existing Request: {existing_request}")  # چاپ درخواست موجود

        if existing_request:
            status = "waiting"
        else:
            status = "pending"

        new_leave = LeaveRequest(
            user_id=current_user.id,
            start_date=leave_data.start_date,
            end_date=leave_data.end_date,
            reason=leave_data.reason,
            status=status,
            level=current_user.level
        )
        print(f"New Leave Request: {new_leave}")  # چاپ درخواست جدید

        db.add(new_leave)
        db.commit()
        db.refresh(new_leave)
        return new_leave
    except Exception as e:
        print(f"Error: {str(e)}")  # چاپ خطا در کنسول
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"خطا در ثبت درخواست مرخصی: {str(e)}"
        )

@router.get("/leave-requests", tags=["leave"])
def get_leave_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # سوپرادمین می‌تواند تمام درخواست‌ها را مشاهده کند
    if current_user.role == "superadmin":
        return db.query(LeaveRequest).all()

    # مدیر، سوپروایزر و تیم لید فقط می‌توانند درخواست‌های مربوط به واحد خودشان را مشاهده کنند
    elif current_user.role in ["manager", "supervisor", "team_lead"]:
        return db.query(LeaveRequest).join(User).filter(User.unit == current_user.unit).all()

    # کارمند فقط می‌تواند درخواست‌های خودش را مشاهده کند
    elif current_user.role == "employee":
        return db.query(LeaveRequest).filter(LeaveRequest.user_id == current_user.id).all()

    # اگر نقش کاربر مشخص نیست، دسترسی ممنوع است
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="شما دسترسی لازم برای مشاهده درخواست‌ها را ندارید"
    )


@router.put("/leave/{leave_id}/status", tags=["leave"])
def update_leave_status(
    leave_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in ["manager", "supervisor"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما اجازه تغییر وضعیت درخواست‌ها را ندارید."
        )

    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="درخواست مرخصی یافت نشد."
        )

    leave_request.status = status
    db.commit()
    db.refresh(leave_request)
    return leave_request



@router.put("/leave/{leave_id}/status", tags=["leave"])
def update_leave_status(
    leave_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # بررسی نقش کاربر
    if current_user.role not in ["manager", "supervisor", "team_lead"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما اجازه تغییر وضعیت درخواست‌ها را ندارید."
        )

    # پیدا کردن درخواست مرخصی
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not leave_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="درخواست مرخصی یافت نشد."
        )

    # پیدا کردن کاربری که درخواست مرخصی را ثبت کرده است
    request_user = db.query(User).filter(User.id == leave_request.user_id).first()
    if not request_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="کاربری که درخواست مرخصی را ثبت کرده است یافت نشد."
        )

    # منطق دسترسی بر اساس نقش
    if current_user.role == "team_lead":
        # تیم لید فقط می‌تواند درخواست‌های مربوط به بخش خودش را تغییر دهد
        if request_user.unit != current_user.unit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="تیم لید فقط می‌تواند وضعیت درخواست‌های بخش خودش را تغییر دهد."
            )

    elif current_user.role == "supervisor":
        # سوپروایزر فقط می‌تواند درخواست‌های مربوط به بخش خودش را تغییر دهد
        if request_user.unit != current_user.unit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="سوپروایزر فقط می‌تواند وضعیت درخواست‌های بخش خودش را تغییر دهد."
            )

    # مدیر نیازی به محدودیت ندارد و می‌تواند همه درخواست‌ها را تغییر دهد

    # تغییر وضعیت درخواست
    leave_request.status = status
    db.commit()
    db.refresh(leave_request)
    return leave_request



@router.get("/leave-report", tags=["leave"])
def leave_report(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما اجازه دسترسی به گزارش‌ها را ندارید."
        )

    approved_count = db.query(LeaveRequest).filter(
        LeaveRequest.status == "approved",
        LeaveRequest.start_date >= start_date,
        LeaveRequest.end_date <= end_date
    ).count()

    rejected_count = db.query(LeaveRequest).filter(
        LeaveRequest.status == "rejected",
        LeaveRequest.start_date >= start_date,
        LeaveRequest.end_date <= end_date
    ).count()

    return {
        "approved_requests": approved_count,
        "rejected_requests": rejected_count
    }