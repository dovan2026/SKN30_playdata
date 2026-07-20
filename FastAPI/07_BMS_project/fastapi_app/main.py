"""BMS(Book Management System) FastAPI 애플리케이션 진입점.

실행:
    cd 07_BMS_project/fastapi_app
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI

import models
from database import engine
from routers import books

# 등록된 ORM 모델을 기준으로 없는 테이블을 생성함.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BMS API",
    description="FastAPI, APIRouter, SQLAlchemy 책 관리",
    version="0.1.0"
)

# books.py의 모든 엔드포인트를 최종 FastAPI 앱에 등록.
app.include_router(books.router)

@app.get("/", tags=['root'])
def root():
    return {
        "message": "BMS API",
        "docs": "/docs",
        "sqlalchemy":"2.x",
        "router":["/books"]
    }
