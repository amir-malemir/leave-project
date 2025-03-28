from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from dependencies import get_db
from models import User
from .auth import get_password_hash

router = APIRouter()

# مدل پایتون برای دریافت اطلاعات کاربر جهت ثبت در دیتابیس
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    phone_number: str
    unit: int
    level: str
    role: str
    password: str

@router.post("/users", tags=["users"])
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # بررسی وجود کاربر با نام کاربری مشابه
    db_user = db.query(User).filter(User.username == user_data.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="کاربر با این نام کاربری وجود دارد"
        )
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        unit=user_data.unit,
        level=user_data.level,
        role=user_data.role,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
