from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.like import LikeResponse
from app.services.like_service import (
    count_likes_by_video,
    create_like,
    delete_like,
    get_like,
)
from app.services.video_service import get_video_by_id
from app.utils.error_response import error_response
from app.utils.success_response import success_response

router = APIRouter()


@router.post("/videos/{video_id}/likes", response_model=LikeResponse)
def add_video_like(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    if not get_video_by_id(db, video_id):
        return error_response(404, "REQUEST_007", "영상을 찾을 수 없습니다.")

    try:
        existing_like = get_like(db, video_id=video_id, user_id=current_user.id)
        if not existing_like:
            create_like(db, video_id=video_id, user_id=current_user.id)

        like_count = count_likes_by_video(db, video_id)
    except IntegrityError:
        db.rollback()
        like_count = count_likes_by_video(db, video_id)
    except SQLAlchemyError:
        db.rollback()
        return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

    return success_response(
        data={"video_id": video_id, "liked": True, "like_count": like_count},
        message="좋아요 추가 성공",
        status_code=201,
    )


@router.delete("/videos/{video_id}/likes", response_model=LikeResponse)
def remove_video_like(
    video_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    if not get_video_by_id(db, video_id):
        return error_response(404, "REQUEST_007", "영상을 찾을 수 없습니다.")

    try:
        existing_like = get_like(db, video_id=video_id, user_id=current_user.id)
        if existing_like:
            delete_like(db, existing_like)

        like_count = count_likes_by_video(db, video_id)
    except SQLAlchemyError:
        db.rollback()
        return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

    return success_response(
        data={"video_id": video_id, "liked": False, "like_count": like_count},
        message="좋아요 취소 성공",
    )
