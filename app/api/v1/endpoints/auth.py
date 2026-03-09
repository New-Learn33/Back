from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import get_db
from app.models.user import User
from app.services.google_auth_service import verify_google_token
from app.core.security import create_access_token

# 라우터 생성
router = APIRouter()

class GoogleLoginRequest(BaseModel):
    id_token: str

# 로그인 API
@router.post("/google/login")
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):

    # 구글 토큰 검증
    google_user = verify_google_token(request.id_token)

    if not google_user:
        raise HTTPException(status_code=401, detail="유효하지 않은 구글 토큰입니다.")

    # provider 정보 설정
    provider = "google"
    provider_id = google_user.get("sub")

    if not provider_id:
        raise HTTPException(status_code=400, detail="구글 사용자 식별값이 없습니다.")

    # DB에서 기존 유저 찾기
    user = db.query(User).filter(
        User.provider == provider,
        User.provider_id == provider_id
    ).first()

    try:
        # 신규 회원 생성 ->  DB에 없으면 회원가입
        if not user:
            user = User(
                email=google_user.get("email"),
                name=google_user.get("name"),
                nickname="익명의 참가자",
                profile_image_url=google_user.get("picture"),
                provider=provider,
                provider_id=provider_id,
            )

            # DB 저장
            db.add(user)

        else:
            user.email = google_user.get("email")
            user.name = google_user.get("name")
            user.profile_image_url = google_user.get("picture")

        db.commit()
        db.refresh(user)

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="데이터베이스 처리 중 오류가 발생했습니다.")

    # JWT 발급
    access_token = create_access_token({
        "user_id": user.id,
        "email": user.email
    })

    # 사용자 정보 반환
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "nickname": user.nickname,
            "profile_image_url": user.profile_image_url,
            "provider": user.provider,
            "provider_id": user.provider_id,
        }
    }