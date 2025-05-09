from sqlalchemy import Column, Integer, String, Date, ForeignKey, DateTime, func, Boolean
from sqlalchemy.orm import relationship
from dependencies import Base
from enum import Enum as PyEnum
from sqlalchemy.types import Enum

class Role(str, PyEnum):
    SUPERADMIN = "superadmin"
    MANAGER = "manager"
    SUPERVISOR = "supervisor"
    TEAM_LEAD = "team_lead"
    EMPLOYEE = "employee"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String, nullable=False)
    phone_number = Column(String, unique=True, index=True)
    unit = Column(String, nullable=False)
    level = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False, default="employee")
    hashed_password = Column(String, nullable=False)
    team = Column(String, nullable=True)
    
    leave_requests = relationship("LeaveRequest", back_populates="user", foreign_keys='LeaveRequest.user_id')
    approved_requests = relationship("LeaveRequest", foreign_keys='LeaveRequest.approved_by', backref="approver")


class LeaveRequest(Base):
    __tablename__ = 'leave_requests'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, default="pending")
    level = Column(String)
    team = Column(String, nullable=True)
    tornado_approval = Column(Boolean, default=None)
    zitel_approval = Column(Boolean, default=None)
    approved_by = Column(Integer, ForeignKey('users.id'))

    created_at = Column(DateTime(timezone=True),server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="leave_requests", foreign_keys=[user_id])

class AdminSetting(Base):
    __tablename__ = "admin_settings"

    id = Column(Integer, primary_key=True)
    max_leave_days = Column(Integer, default=30)
    default_shift = Column(String, nullable=True)
