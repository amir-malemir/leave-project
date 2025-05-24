from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
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
    start_date: str
    end_date: str
    reason: Optional[str] = None

class LeaveUpdate(BaseModel):
    status: str
    reason: Optional[str] = None

def gregorian_to_shamsi(gregorian_date, fmt="%Y/%m/%d"):
    """تبدیل تاریخ میلادی به شمسی با فرمت دلخواه"""
    if not gregorian_date:
        return "-"
    try:
        jdate = jdatetime.datetime.fromgregorian(datetime=gregorian_date)
        return jdate.strftime(fmt)
    except Exception as e:
        print(f"Error converting date: {e}")
        return str(gregorian_date)
    
# leave request
@router.get("/create-leave-request", response_class=HTMLResponse)
async def create_leave_request_page(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("create_leave_request.html", {"request": request, "user_role": current_user.role})


@router.post("/leave_request", tags=["leave"])
def create_leave_request(
    start_date: str = Form(...),
    end_date: str = Form(...),
    reason: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # تبدیل تاریخ‌های شمسی به میلادی
        try:
            # تبدیل رشته شمسی به تاریخ میلادی
            start_date_j = jdatetime.datetime.strptime(start_date, "%Y/%m/%d").date()
            end_date_j = jdatetime.datetime.strptime(end_date, "%Y/%m/%d").date()
            start_date_gregorian = start_date_j.togregorian()
            end_date_gregorian = end_date_j.togregorian()

            today = date.today()
            if start_date_gregorian < today or end_date_gregorian < today:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="تاریخ شروع یا پایان نمی‌تواند قبل از امروز باشد."
                )

        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="فرمت تاریخ نامعتبر است. لطفاً تاریخ‌ها را به فرمت YYYY/MM/DD ارسال کنید."
            )

        # بررسی تکراری بودن درخواست
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

        existing_level_request = db.query(LeaveRequest).filter(
            LeaveRequest.level == current_user.level,
            LeaveRequest.team == current_user.team,
            LeaveRequest.start_date <= end_date_gregorian,
            LeaveRequest.end_date >= start_date_gregorian
        ).first()

        if existing_level_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="در این بازه زمانی، کاربری در سطح شما قبلاً درخواست مرخصی ثبت کرده است."
            )

        # ایجاد رکورد جدید
        new_leave = LeaveRequest(
            user_id=current_user.id,
            start_date=start_date_gregorian,
            end_date=end_date_gregorian,
            reason=reason,
            status="pending",
            level=current_user.level,
            team=current_user.team
        )

        db.add(new_leave)
        db.commit()
        db.refresh(new_leave)
        return RedirectResponse(url="/leave-requests-page?success=1", status_code=303)

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"خطا در ثبت درخواست مرخصی: {str(e)}"
            )

@router.get("/leave-requests-page", response_class=HTMLResponse)
def show_user_leave_requests_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    leave_requests = db.query(LeaveRequest).filter(
    LeaveRequest.user_id == current_user.id
).order_by(LeaveRequest.created_at.desc()).all()

    leave_requests_shamsi = []
    for leave in leave_requests:
        leave_requests_shamsi.append({
            "id": leave.id,
            "full_name": current_user.full_name,
            "start_date": jdatetime.date.fromgregorian(date=leave.start_date).strftime("%Y/%m/%d"),
            "end_date": jdatetime.date.fromgregorian(date=leave.end_date).strftime("%Y/%m/%d"),
            "reason": leave.reason,
            "status": leave.status,
            "created_at": jdatetime.datetime.fromgregorian(datetime=leave.created_at).strftime("%Y/%m/%d %H:%M")
        })

    return templates.TemplateResponse("user_leave_requests.html", {
        "request": request,
        "leave_requests": leave_requests_shamsi,
        "user_role": current_user.role
    })
# @router.get("/user-leave-requests", tags=["leave"])
# def get_user_leave_requests(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     try:
#         leave_requests = db.query(LeaveRequest).filter(
#             LeaveRequest.user_id == current_user.id
#         ).all()

#         # تبدیل تاریخ‌ها به شمسی
#         leave_requests_shamsi = []
#         for request in leave_requests:
#             leave_requests_shamsi.append({
#                 "id": request.id,
#                 "username": current_user.username,
#                 "start_date": jdatetime.date.fromgregorian(date=request.start_date).strftime("%Y/%m/%d"),
#                 "end_date": jdatetime.date.fromgregorian(date=request.end_date).strftime("%Y/%m/%d"),
#                 "reason": request.reason,
#                 "status": request.status
#             })

#         return leave_requests_shamsi
#     except Exception as e:
#         print(f"Error: {str(e)}")
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="خطا در دریافت لیست درخواست‌های مرخصی"
#         )

@router.get("/all-leave-requests-page", response_class=HTMLResponse)
def all_leave_requests_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.lower() not in AUTHORIZED_ROLES:
        raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")
    
    if current_user.role == "team_lead" and current_user.team == "Tornado":
        leave_requests = (
            db.query(LeaveRequest)
            .join(User, LeaveRequest.user_id == User.id)
            .filter(User.team == "Tornado")
            .options(joinedload(LeaveRequest.user))
            .order_by(LeaveRequest.created_at.desc())
            .all()
        )
    else:
        # سایر نقش‌ها (از جمله تیم لید غیر توراندو) همه درخواست‌ها رو ببینن
        leave_requests = (
            db.query(LeaveRequest)
            .options(joinedload(LeaveRequest.user))
            .order_by(LeaveRequest.created_at.desc())  
            .all()
        )
    
    leave_requests_data = []
    for req in leave_requests:
        duration_days = (req.end_date - req.start_date).days + 1  # +1 برای شامل بودن هر دو روز
        leave_requests_data.append({
            "id": req.id,
            "full_name": req.user.full_name,
            "username": req.user.username,
            "team": req.user.team,
            "role": req.user.role.value if hasattr(req.user.role, "value") else req.user.role,
            "start_date": gregorian_to_shamsi(req.start_date),
            "end_date": gregorian_to_shamsi(req.end_date),
            "duration_days": duration_days,
            "unit": req.user.unit,
            "phone_number": req.user.phone_number,
            "created_at": gregorian_to_shamsi(req.created_at, "%Y/%m/%d %H:%M"),
            "status": req.status,
            "reason": req.reason or "-",
        })

    return templates.TemplateResponse(
        "all_leave_requests.html",
        {
            "request": request,
            "leave_requests": leave_requests_data,
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

# @router.post("/update-leave-request/{request_id}")
# async def update_leave_request(
#     request_id: int,
#     request: Request,
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     if current_user.role.lower() not in AUTHORIZED_ROLES:
#         raise HTTPException(status_code=403, detail="دسترسی غیرمجاز")

#     form_data = await request.form()
#     leave = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()

#     if not leave:
#         raise HTTPException(status_code=404, detail="درخواست پیدا نشد")

#     target_user = db.query(User).filter(User.id == leave.user_id).first()
#     requesting_team = target_user.team
#     current_team = current_user.team

#     # حالت اول: درخواست‌دهنده از تیم Tornado
#     if requesting_team == "Tornado":
#         if current_team == "Tornado":
#             leave.tornado_approval = True
#             leave.status = "pending_zitel"
#         elif current_team == "Zitel":
#             leave.zitel_approval = True

#         # اگر هر دو تأیید کردند
#         if leave.tornado_approval and leave.zitel_approval:
#             leave.status = "approved"
#             leave.approved_by = current_user.id
#             leave.approved_at = datetime.utcnow()

#     # حالت دوم: درخواست‌دهنده از تیم Zitel
#     elif requesting_team == "Zitel":
#         leave.tornado_approval = False  # مشخصه که نیازی به تایید تورنادو نداره
#         if current_team == "Zitel":
#             leave.zitel_approval = True
#             leave.status = "approved"
#             leave.approved_by = current_user.id
#             leave.approved_at = datetime.utcnow()

#     else:
#         # در صورت تیم ناشناس
#         raise HTTPException(status_code=400, detail="تیم نامعتبر")

#     # به‌روزرسانی مقادیر دیگر
#     leave.reason = form_data.get("reason")
#     leave.manager_comment = form_data.get("manager_comment")
#     leave.updated_at = datetime.utcnow()

#     db.commit()

#     return RedirectResponse(
#         url="/all-leave-requests-page",
#         status_code=303
#     )



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
    leave = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()

    if not leave:
        raise HTTPException(status_code=404, detail="درخواست پیدا نشد")

    target_user = db.query(User).filter(User.id == leave.user_id).first()
    requesting_team = target_user.team
    current_team = current_user.team

    # بررسی وضعیت جدید (از فرم گرفته شده)
    new_status = form_data.get("status")

    # به‌روزرسانی تأییدها طبق تیم و نقش
    if requesting_team == "Tornado":
        if current_team == "Tornado":
            leave.tornado_approval = True
            leave.status = "pending_zitel"
        elif current_team == "Zitel":
            leave.zitel_approval = True

        if leave.tornado_approval and leave.zitel_approval:
            leave.status = "approved"
            leave.approved_by = current_user.id
            leave.approved_at = datetime.utcnow()

    elif requesting_team == "Zitel":
        leave.tornado_approval = False
        if current_team == "Zitel":
            leave.zitel_approval = True
            leave.status = "approved"
            leave.approved_by = current_user.id
            leave.approved_at = datetime.utcnow()

    else:
        raise HTTPException(status_code=400, detail="تیم نامعتبر")

    # اعمال تغییر وضعیت دستی فقط در صورتی که کاربر مجاز است
    if new_status in ["pending", "pending_zitel", "approved", "rejected"]:
        # فقط در صورتی اجازه بدیم که نقش بالایی داشته باشه
        if current_user.role.lower() in ["supervisor", "manager", "superadmin"]:
            leave.status = new_status
            if new_status == "approved":
                leave.approved_by = current_user.id
                leave.approved_at = datetime.utcnow()

    # به‌روزرسانی فیلدهای دیگر
    leave.reason = form_data.get("reason")
    leave.manager_comment = form_data.get("manager_comment")
    leave.updated_at = datetime.utcnow()

    db.commit()

    return RedirectResponse(
        url="/all-leave-requests-page",
        status_code=303
    )