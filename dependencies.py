# app/dependencies.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# رشته اتصال به دیتابیس PostgreSQL را جایگزین کنید
DATABASE_URL = "postgresql://postgres:root@localhost/leavepro"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """سازماندهی جلسه دیتابیس برای هر درخواست"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()