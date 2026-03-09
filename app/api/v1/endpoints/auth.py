from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import get_db
from app.models.user import User
from app.services.google_auth_service import verify_google_token
from app.core.security import create_access_token
from app.utils.error_response import error_response

# 라우터 생성
router = APIRouter()

class GoogleLoginRequest(BaseModel):
    id_token: str

# 로그인 API
@router.post("/google/login")
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):

    # id_token 출력 (디버깅용)
    print("=== 받은 Google id_token ===")
    print(request.id_token)
    print("============================")

    # 구글 토큰 검증
    google_user = verify_google_token(request.id_token)

    if not google_user:
        return error_response(
            401,
            "REQUEST_003",
            "유효하지 않은 JWT입니다."
        )

    # provider 정보 설정
    provider = "google"
    provider_id = google_user.get("sub")

    if not provider_id:
        return error_response(
            400,
            "REQUEST_001",
            "잘못된 요청입니다."
        )

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
        return error_response(
            500,
            "RESPONSE_001",
            "서버와의 연결에 실패했습니다."
        )

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