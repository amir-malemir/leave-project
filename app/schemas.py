from pydantic import BaseModel
from typing import Optional
from datetime import date

# اسکیمای خروجی برای اطلاعات کاربر
class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    phone_number: str
    unit: str
    level: str
    role: str

    class Config:
        from_attributes = True

# اسکیمای تغییر نقش کاربر
class RoleUpdate(BaseModel):
    role: str


class LeaveRequestCreate(BaseModel):
    start_date: date
    end_date: date
    reason: str