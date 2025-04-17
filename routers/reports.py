from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from dependencies import get_db
from models import LeaveRequest
from schemas import LeaveRequestOut
from datetime import date

router = APIRouter()

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