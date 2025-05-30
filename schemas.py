from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime



class TeamBase(BaseModel):
    id: int
    name: str
    is_vendor: bool

    class Config:
        orm_mode = True

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    phone_number: str
    unit: str
    level: str
    role: str
    team: Optional[TeamBase] = None


class RoleUpdate(BaseModel):
    role: str


class LeaveRequestCreate(BaseModel):
    start_date: date
    end_date: date
    reason: str


class LeaveRequestOut(BaseModel):
    id: int
    user_id: int
    start_date: date
    end_date: date
    status: str
    level: Optional[str]
    reason: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class AdminSettingsUpdate(BaseModel):
    max_leave_days: int
    default_shift: Optional[str]


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None