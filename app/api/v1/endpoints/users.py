from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import (
    UserCommentListResponse,
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserVideoListResponse,
)
from app.services.comment_service import list_comments_by_user
from app.services.video_service import list_liked_videos_by_user, list_videos_by_user
from app.utils.error_response import error_response
from app.utils.success_response import success_response

router = APIRouter(prefix="/users", tags=["users"])


def serialize_profile(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "profile_image_url": user.profile_image_url,
    }


def serialize_user_video(video) -> dict:
    return {
        "id": video.id,
        "title": video.title,
        "category_id": video.category_id,
        "thumbnail_url": video.thumbnail_url or "",
        "video_url": video.video_url,
        "like_count": video.like_count,
        "comment_count": video.comment_count,
        "view_count": 0,
    }


def serialize_user_comment(comment) -> dict:
    return {
        "id": comment.id,
        "video_id": comment.video_id,
        "content": comment.content,
    }


@router.get("/me/profile", response_model=UserProfileResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    if isinstance(current_user, JSONResponse):
        return current_user

    return success_response(
        data={"user": serialize_profile(current_user)},
        message="내 프로필 조회 성공",
    )


@router.patch("/me/profile", response_model=UserProfileResponse)
def update_my_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    updates = request.model_dump(exclude_none=True)
    if not updates:
        return error_response(400, "REQUEST_001", "잘못된 요청입니다.")

    try:
        if "nickname" in updates:
            current_user.nickname = updates["nickname"]
        if "profile_image_url" in updates:
            current_user.profile_image_url = updates["profile_image_url"]

        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    except SQLAlchemyError:
        db.rollback()
        return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

    return success_response(
        data={"user": serialize_profile(current_user)},
        message="내 프로필 수정 성공",
    )


@router.get("/me/videos", response_model=UserVideoListResponse)
def get_my_videos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    try:
        videos = list_videos_by_user(db, current_user.id)
    except SQLAlchemyError:
        db.rollback()
        return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

    return success_response(
        data={"videos": [serialize_user_video(video) for video in videos]},
        message="내 업로드 영상 조회 성공",
    )


@router.get("/me/comments", response_model=UserCommentListResponse)
def get_my_comments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    try:
        comments = list_comments_by_user(db, current_user.id)
    except SQLAlchemyError:
        db.rollback()
        return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

    return success_response(
        data={"comments": [serialize_user_comment(comment) for comment in comments]},
        message="내 댓글 목록 조회 성공",
    )


@router.get("/me/likes", response_model=UserVideoListResponse)
def get_my_liked_videos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    try:
        videos = list_liked_videos_by_user(db, current_user.id)
    except SQLAlchemyError:
        db.rollback()
        return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

    return success_response(
        data={"videos": [serialize_user_video(video) for video in videos]},
        message="내 좋아요 영상 조회 성공",
    )
