from fastapi import Depends, HTTPException, status
from models import User
from routers.auth import get_current_user

def check_role(required_roles: list[str], current_user: User = Depends(get_current_user)):
    """بررسی نقش کاربر برای دسترسی به منابع خاص"""
    if current_user.role not in required_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما دسترسی لازم برای این عملیات را ندارید"
        )
    return current_user