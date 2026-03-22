from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse

from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.database import get_db
from app.models.user import User
from app.services.google_auth_service import verify_google_token
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.utils.error_response import error_response
from app.utils.success_response import success_response

# 라우터 생성
router = APIRouter()

# Authorization: Bearer <token> 형식의 헤더를 받기 위한 보안 스키마
security = HTTPBearer(auto_error=False)

class GoogleLoginRequest(BaseModel):
    id_token: str

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

# 현재 로그인한 사용자 정보를 조회하는 공통 함수
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    # Authorization 헤더가 없는 경우
    if not credentials:
        return error_response(
            401,
            "REQUEST_002",
            "JWT를 입력해주세요."
        )

    token = credentials.credentials
    payload = decode_access_token(token)

    # JWT decode 실패 또는 만료/위조된 토큰인 경우
    if not payload:
        return error_response(
            401,
            "REQUEST_003",
            "유효하지 않은 JWT입니다."
        )

    user_id = payload.get("user_id")

    # 토큰 payload에 user_id가 없는 경우
    if not user_id:
        return error_response(
            401,
            "REQUEST_003",
            "유효하지 않은 JWT입니다."
        )

     # 토큰에 담긴 user_id로 DB에서 사용자 조회
    user = db.query(User).filter(User.id == int(user_id)).first()

    # 해당 유저가 존재하지 않는 경우
    if not user:
        return error_response(
            404,
            "REQUEST_007",
            "잘못된 접근입니다."
        )

    return user

# 로그인 API
@router.post("/google/login")
def google_login(request: GoogleLoginRequest, db: Session = Depends(get_db)):

    # 구글 토큰 검증
    google_user = verify_google_token(request.id_token)

    if not google_user:
        return error_response(
            401,
            "REQUEST_003",
            "유효하지 않은 구글 토큰입니다."
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
    return success_response(
    data={
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
    },
    message="로그인 성공"
)

# 이메일 회원가입 API
@router.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):

    # 이메일 중복 체크
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        return error_response(
            409,
            "REQUEST_004",
            "이미 사용 중인 이메일입니다."
        )

    try:
        # 유저 생성
        user = User(
            email=request.email,
            name=request.name,
            nickname=request.name,
            password_hash=hash_password(request.password),
            provider="email",
            provider_id=request.email,
        )
        db.add(user)
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

    return success_response(
        data={
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
        },
        message="회원가입 성공"
    )

# 이메일 로그인 API
@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):

    # 이메일로 유저 조회
    user = db.query(User).filter(
        User.email == request.email,
        User.provider == "email"
    ).first()

    if not user:
        return error_response(
            401,
            "REQUEST_005",
            "이메일 또는 비밀번호가 올바르지 않습니다."
        )

    # 비밀번호 검증
    if not user.password_hash or not verify_password(request.password, user.password_hash):
        return error_response(
            401,
            "REQUEST_005",
            "이메일 또는 비밀번호가 올바르지 않습니다."
        )

    # JWT 발급
    access_token = create_access_token({
        "user_id": user.id,
        "email": user.email
    })

    return success_response(
        data={
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
        },
        message="로그인 성공"
    )

# 현재 로그인한 사용자 정보 조회 API
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):

    if isinstance(current_user, JSONResponse):
        return current_user
    
    return success_response(
        data={
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "nickname": current_user.nickname,
            "profile_image_url": current_user.profile_image_url,
            "provider": current_user.provider,
            "provider_id": current_user.provider_id,
            "storage_used": current_user.storage_used or 0,
        },
        message="내 정보 조회 성공"
    )

# 로그아웃 API
@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):

    if isinstance(current_user, JSONResponse):
        return current_user
    
    return success_response(
        data={},
        message="로그아웃 성공"
    )
