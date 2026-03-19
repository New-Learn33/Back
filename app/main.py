from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.v1.api import api_router
from app.db.database import Base, engine
from app.models.comment import Comment
from app.models.video_like import VideoLike
from app.models.user import User
from app.db.database import init_db
import traceback

init_db()

app = FastAPI(
    title="NewLearn API",
    version="1.0"
)

# CORS 설정 - 프론트엔드에서 백엔드 API 호출 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://www.newlearn33.store",
        "https://newlearn33.store",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 글로벌 예외 핸들러 - 500 에러에도 CORS 헤더가 포함되도록
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )


@app.get("/")
def root():
    return {"message": "server running"}

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 연결
app.include_router(api_router, prefix="/api/v1")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
