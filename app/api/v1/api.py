# v1 버전 API들을 한곳에 모음

from fastapi import APIRouter
from app.api.v1.endpoints import auth

# 상위 라우터 생성
api_router = APIRouter()

# auth.py에 정의된 라우터들을 /auth 아래로 연결
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])