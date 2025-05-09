from fastapi import FastAPI, Response, Depends
from fastapi.staticfiles import StaticFiles
from routers import leave, auth, users, reports
from core.templates import templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.requests import Request
from dependencies import engine, Base, get_db
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from routers.context_processors import inject_user_role
import inspect


import models
import logging


app = FastAPI(debug=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # یا لیست دامنه‌های مجاز
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(leave.router)
app.include_router(reports.router)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "message": "سلام، به سامانه مرخصی خوش آمدید!"})

@app.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "خروج موفقیت‌آمیز بود"}