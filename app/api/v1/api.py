# v1 버전 API들을 한곳에 모음

from fastapi import APIRouter
from app.api.v1.endpoints import auth, categories, comments, generation, likes, users, videos

# 상위 라우터 생성
api_router = APIRouter()

# auth.py에 정의된 라우터들을 /auth 아래로 연결
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(generation.router, prefix="/generation", tags=["generation"])
api_router.include_router(comments.router, tags=["comments"])
api_router.include_router(likes.router, tags=["likes"])
api_router.include_router(users.router)
api_router.include_router(videos.router, tags=["videos"])
