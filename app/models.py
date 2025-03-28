# app/models.py

from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from dependencies import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    phone_number = Column(String, unique=True, index=True)
    unit = Column(Integer)
    level = Column(String)
    role = Column(String)
    hashed_password = Column(String)

    leave_requests = relationship("LeaveRequest", back_populates="user")

class LeaveRequest(Base):
    __tablename__ = 'leave_requests'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    start_date = Column(Date)
    end_date = Column(Date)
    reason = Column(String, nullable=True)
    status = Column(String, default="pending")

    user = relationship("User", back_populates="leave_requests")
