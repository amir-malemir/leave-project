from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import date
from dependencies import get_db
from models import LeaveRequest

router = APIRouter()

# مدل پایتون جهت ثبت درخواست مرخصی
class LeaveRequestCreate(BaseModel):
    user_id: int
    start_date: date
    end_date: date
    reason: str = None

@router.post("/leave", tags=["leave"])
def create_leave_request(leave_data: LeaveRequestCreate, db: Session = Depends(get_db)):
    new_leave = LeaveRequest(
        user_id=leave_data.user_id,
        start_date=leave_data.start_date,
        end_date=leave_data.end_date,
        reason=leave_data.reason,
        status="pending"
    )
    db.add(new_leave)
    db.commit()
    db.refresh(new_leave)
    return new_leave
