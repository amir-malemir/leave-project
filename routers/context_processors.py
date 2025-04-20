# context_processors.py
from fastapi import Request
from typing import Dict, Any
from .auth import get_current_user  # مسیر صحیح به تابع احراز هویت خود را وارد کنید

async def inject_user_role(request: Request) -> Dict[str, Any]:
    try:
        user = await get_current_user(request)
        return {"user_role": user.role}
    except Exception:
        return {"user_role": None}
