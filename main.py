from fastapi import FastAPI, Response, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from routers import leave, auth, users, reports
from temp.templates import templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.requests import Request
from dependencies import engine, Base, get_db
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
import inspect


import models
import logging


app = FastAPI(debug=True)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.exception_handler(HTTPException)
async def redirect_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 303 and str(exc.detail).startswith("redirect:"):
        url = exc.detail.replace("redirect:", "", 1)
        return RedirectResponse(url, status_code=303)
    raise exc

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    return RedirectResponse(url="/login")
