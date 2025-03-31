from fastapi import FastAPI
from routers import leave, auth, users
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.requests import Request
from dependencies import engine, Base
import models
import logging
# logging.basicConfig()
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

app = FastAPI(debug=True)

Base.metadata.create_all(bind=engine)


templates = Jinja2Templates(directory="templates")


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(leave.router)

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "message": "سلام، به سامانه مرخصی خوش آمدید!"})
