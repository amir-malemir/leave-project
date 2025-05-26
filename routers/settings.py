# from fastapi import APIRouter, Request, Depends, Form, HTTPException
# from fastapi.responses import RedirectResponse, HTMLResponse
# from sqlalchemy.orm import Session
# from models import User, AdminSetting
# from dependencies import get_db
# from routers.auth import get_current_user
# from starlette.status import HTTP_302_FOUND
# from fastapi.templating import Jinja2Templates



# router = APIRouter()
# templates = Jinja2Templates(directory="templates")

# # @router.get("/settings", response_class=HTMLResponse)
# # def settings_page(
# #     request: Request,
# #     db: Session = Depends(get_db),
# #     current_user: User = Depends(get_current_user)
# # ):
# #     return templates.TemplateResponse("settings.html", {
# #         "request": request,
# #         "user": current_user
# #     })

# # @router.post("/update-profile")
# # def update_profile(
# #     request: Request,
# #     full_name: str = Form(...),
# #     email: str = Form(...),
# #     new_password: str = Form(None),
# #     db: Session = Depends(get_db),
# #     current_user: User = Depends(get_current_user)
# # ):
# #     current_user.full_name = full_name
# #     current_user.email = email
# #     if new_password:
# #         current_user.set_password(new_password)  
# #     db.commit()
# #     return RedirectResponse(url="/settings", status_code=HTTP_302_FOUND)

# # router = APIRouter()
# # templates = Jinja2Templates(directory="templates")


# # @router.get("/settings", response_class=HTMLResponse)
# # def settings_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
# #     admin_settings = db.query(AdminSetting).first()
# #     if not admin_settings:
# #         admin_settings = AdminSetting(max_leave_days=30, default_shift="A")
# #         db.add(admin_settings)
# #         db.commit()
# #         db.refresh(admin_settings)

# #     shift_names = ["A", "B", "C", "D", "E", "OFF"]

# #     return templates.TemplateResponse("settings.html", {
# #         "request": request,
# #         "user": current_user,
# #         "admin_settings": admin_settings,
# #         "shift_names": shift_names
# #     })


# # @router.post("/update-profile")
# # def update_profile(
# #     request: Request,
# #     full_name: str = Form(...),
# #     email: str = Form(...),
# #     new_password: str = Form(None),
# #     db: Session = Depends(get_db),
# #     current_user: User = Depends(get_current_user)
# # ):
# #     current_user.full_name = full_name
# #     current_user.email = email
# #     if new_password:
# #         current_user.set_password(new_password) 
# #     db.commit()
# #     return RedirectResponse(url="/settings", status_code=HTTP_302_FOUND)

