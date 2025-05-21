from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, APIRouter, FastAPI, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from pydantic import BaseModel
from dependencies import get_db
from models import User


router = APIRouter()


# تنظیمات امنیتی
SECRET_KEY = "f2b8e5f6d8c3a1b2e4f7c8d3a9e6b1f0"
ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class TokenData(BaseModel):
    sub: int


#  کانتکست رمزنگاری
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """هش کردن رمز عبور"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """بررسی صحت رمز عبور"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# def get_current_user(request: Request, db: Session = Depends(get_db)):
#     print("========= شروع get_current_user =========")
#     token = request.cookies.get("access_token")  # دریافت توکن از کوکی
#     if not token:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="توکن یافت نشد.",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     try:
#         payload = jwt.decode(token.split(" ")[1], SECRET_KEY, algorithms=["HS256"])
#         print("Payload توکن:", payload)  # لاگ داده‌های موجود در payload
#         user_id = payload.get("sub")
#         if user_id is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="توکن نامعتبر است.",
#                 headers={"WWW-Authenticate": "Bearer"},
#             )
#         user = db.query(User).filter(User.id == int(user_id)).first()
#         if user is None:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="کاربر یافت نشد.",
#                 headers={"WWW-Authenticate": "Bearer"},
#             )
#         return user
#     except JWTError as e:
#         print(f"خطا در بررسی توکن: {e}")
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="توکن نامعتبر است.",
#             headers={"WWW-Authenticate": "Bearer"},
#         )


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="توکن یافت نشد.",
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="توکن نامعتبر است.")
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(status_code=401, detail="کاربر یافت نشد.")
        return user
    except Exception as e:
        print("خطا در بررسی توکن:", e)
        raise HTTPException(status_code=401, detail="توکن نامعتبر است.")

@router.post("/token", tags=["auth"])
def login_for_access_token(
    response: Response,
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    دریافت توکن دسترسی و ذخیره آن در کوکی.
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="نام کاربری یا رمز عبور اشتباه است",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})

    # ذخیره توکن در کوکی
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,  # جلوگیری از دسترسی جاوااسکریپت
        secure=True,    # فقط در HTTPS ارسال شود
        samesite="Strict"  # جلوگیری از ارسال کوکی در درخواست‌های Cross-Site
    )

    return {"message": "ورود موفقیت‌آمیز بود"}