from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.db.database import Base, engine
from app.models.comment import Comment
from app.models.like import Like
from app.models.user import User
from app.db.database import init_db

init_db()

app = FastAPI(
    title="NewLearn API",
    version="1.0"
)

# CORS 설정 - 프론트엔드에서 백엔드 API 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "server running"}

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 연결
app.include_router(api_router, prefix="/api/v1")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
