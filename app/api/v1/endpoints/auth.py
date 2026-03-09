from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.user import User
from app.services.google_auth_service import verify_google_token
from app.core.security import create_access_token

router = APIRouter()

class GoogleLoginRequest(BaseModel):
    id_token: str

@router.post("/google/login")
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    google_user = verify_google_token(request.id_token)

    if not google_user:
        raise HTTPException(status_code=401, detail="유효하지 않은 구글 토큰입니다.")

    provider = "google"
    provider_id = google_user.get("sub")

    if not provider_id:
        raise HTTPException(status_code=400, detail="구글 사용자 식별값이 없습니다.")

    user = db.query(User).filter(
        User.provider == provider,
        User.provider_id == provider_id
    ).first()

    if not user:
        user = User(
            email=google_user.get("email"),
            name=google_user.get("name"),
            nickname="익명의 참가자",
            profile_image_url=google_user.get("picture"),
            provider=provider,
            provider_id=provider_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.email = google_user.get("email")
        user.name = google_user.get("name")
        user.profile_image_url = google_user.get("picture")
        db.commit()
        db.refresh(user)

    access_token = create_access_token({
        "user_id": user.id,
        "email": user.email
    })

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