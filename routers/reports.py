from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from dependencies import get_db
from schemas import LeaveRequestOut
from datetime import date, datetime
from io import BytesIO
from openpyxl import Workbook
from fastapi.responses import StreamingResponse
from models import LeaveRequest, User
from typing import Optional


router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)

@router.get("/report/")
def get_leave_report(
    start_date: date = Query(None),
    end_date: date = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(LeaveRequest)

    if start_date:
        query = query.filter(LeaveRequest.start_date >= start_date)
    if end_date:
        query = query.filter(LeaveRequest.end_date <= end_date)

    results = query.all()
    return results


@router.get("/leave-requests/excel", summary="Export leave requests to Excel with filters")
def export_leave_requests_excel(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    role: Optional[str] = Query(None)
):
    wb = Workbook()
    ws = wb.active
    ws.title = "Leave Requests"

    headers = [
        "ID",
        "Full Name",
        "Username",
        "Unit",
        "User Level",
        "Leave Level",
        "Status",
        "Start Date",
        "End Date",
        "Reason",
        "Created At",
    ]
    ws.append(headers)

    # ساخت کوئری با فیلترهای داینامیک
    query = db.query(LeaveRequest).join(User)

    if start_date:
        query = query.filter(LeaveRequest.start_date >= start_date)
    if end_date:
        query = query.filter(LeaveRequest.end_date <= end_date)
    if status:
        query = query.filter(LeaveRequest.status == status)
    if role:
        query = query.filter(User.role == role)

    leave_requests = query.all()

    for lr in leave_requests:
        ws.append([
            lr.id,
            lr.user.full_name if lr.user else "N/A",
            lr.user.username if lr.user else "N/A",
            lr.user.unit if lr.user else "N/A",
            lr.user.level if lr.user else "N/A",
            lr.level or "",
            lr.status or "",
            lr.start_date.strftime("%Y-%m-%d") if lr.start_date else "",
            lr.end_date.strftime("%Y-%m-%d") if lr.end_date else "",
            lr.reason or "",
            lr.created_at.strftime("%Y-%m-%d %H:%M") if lr.created_at else ""
        ])

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    filename = f"leave_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
