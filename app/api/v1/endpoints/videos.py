from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import security, get_current_user
from app.core.security import decode_access_token
from app.db.database import get_db
from app.models.generation_job import GenerationJob
from app.schemas.video import (
    VideoDetailResponse,
    VideoListResponse,
    VideoSearchResponse,
)
from app.models.user import User
from app.services.video_service import (
    get_liked_video_ids,
    get_video_by_id,
    list_videos,
    search_videos_by_title,
)
from app.utils.error_response import error_response
from app.utils.success_response import success_response


class VideoUpdateRequest(BaseModel):
    title: Optional[str] = None

router = APIRouter()


def get_optional_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int | None:
    if not credentials:
        return None

    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None

    user_id = payload.get("user_id")
    return int(user_id) if user_id else None


def _creator_fields(user) -> dict:
    if not user:
        return {"creator": None, "creator_nickname": "알 수 없음", "creator_avatar_url": None}
    return {
        "creator": user.name,
        "creator_nickname": user.nickname or user.name or "알 수 없음",
        "creator_avatar_url": user.profile_image_url,
    }


def serialize_video_list_item(video, like_count: int, comment_count: int, liked: bool, user=None) -> dict:
    return {
        "id": video.id,
        "title": video.title,
        "category_id": video.category_id,
        "thumbnail_url": video.thumbnail_url or "",
        "video_url": video.video_url or "",
        "created_at": video.created_at.isoformat() if video.created_at else None,
        "like_count": like_count,
        "comment_count": comment_count,
        "liked": liked,
        "view_count": getattr(video, 'view_count', 0) or 0,
        **_creator_fields(user),
    }


def serialize_video_search_item(video, like_count: int, comment_count: int, user=None) -> dict:
    return {
        "id": video.id,
        "title": video.title,
        "category_id": video.category_id,
        "thumbnail_url": video.thumbnail_url or "",
        "video_url": video.video_url or "",
        "created_at": video.created_at.isoformat() if video.created_at else None,
        "like_count": like_count,
        "comment_count": comment_count,
        "view_count": getattr(video, 'view_count', 0) or 0,
        **_creator_fields(user),
    }


def serialize_video_detail_item(video, like_count: int, comment_count: int, liked: bool, user=None) -> dict:
    return {
        "id": video.id,
        "user_id": video.user_id,
        "title": video.title,
        "category_id": video.category_id,
        "thumbnail_url": video.thumbnail_url or "",
        "like_count": like_count,
        "comment_count": comment_count,
        "liked": liked,
        "video_url": video.video_url or "",
        "created_at": video.created_at.isoformat() if video.created_at else None,
        "view_count": getattr(video, 'view_count', 0) or 0,
        **_creator_fields(user),
    }


@router.get("/videos", response_model=VideoListResponse)
def get_videos(
    sort: str = Query("popular", pattern="^(popular|latest)$"),
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_optional_user_id),
):
    try:
        video_rows = list_videos(db, sort=sort)
        liked_video_ids = (
            get_liked_video_ids(db, user_id, [video.id for video in video_rows])
            if user_id
            else set()
        )
        # 유저 정보 한번에 조회
        user_ids = list({v.user_id for v in video_rows})
        users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    except SQLAlchemyError:
        db.rollback()
        return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

    return success_response(
        data={
            "videos": [
                serialize_video_list_item(
                    video,
                    video.like_count,
                    video.comment_count,
                    video.id in liked_video_ids,
                    user=users.get(video.user_id),
                )
                for video in video_rows
            ]
        },
        message="영상 목록 조회 성공",
    )


@router.get("/videos/search", response_model=VideoSearchResponse)
def search_videos(
    title: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    keyword = title.strip()
    if not keyword:
        return error_response(400, "REQUEST_001", "잘못된 요청입니다.")

    try:
        matched_videos = search_videos_by_title(db, keyword)
        user_ids = list({v.user_id for v in matched_videos})
        users = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    except SQLAlchemyError:
        db.rollback()
        return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

    return success_response(
        data={
            "videos": [
                serialize_video_search_item(video, video.like_count, video.comment_count, user=users.get(video.user_id))
                for video in matched_videos
            ]
        },
        message="영상 검색 성공",
    )


@router.get("/videos/{video_id}", response_model=VideoDetailResponse)
def get_video_detail(
    video_id: int,
    db: Session = Depends(get_db),
    user_id: int | None = Depends(get_optional_user_id),
):
    try:
        video_row = get_video_by_id(db, video_id)
        liked_video_ids = (
            get_liked_video_ids(db, user_id, [video_id]) if user_id else set()
        )
    except SQLAlchemyError:
        db.rollback()
        return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

    if not video_row:
        return error_response(404, "REQUEST_007", "영상을 찾을 수 없습니다.")

    # 작성자 조회
    creator_user = db.query(User).filter(User.id == video_row.user_id).first()

    # 조회수 +1
    try:
        video_row.view_count = (video_row.view_count or 0) + 1
        db.commit()
        db.refresh(video_row)
    except SQLAlchemyError:
        db.rollback()

    return success_response(
        data={
            "videos": serialize_video_detail_item(
                video_row,
                video_row.like_count,
                video_row.comment_count,
                video_row.id in liked_video_ids,
                user=creator_user,
            )
        },
        message="영상 상세 조회 성공",
    )


@router.patch("/videos/{video_id}")
def update_video(
    video_id: int,
    request: VideoUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """영상 제목 수정 (소유자만)"""
    if isinstance(current_user, JSONResponse):
        return current_user

    video = db.query(GenerationJob).filter(
        GenerationJob.id == video_id,
        GenerationJob.user_id == current_user.id,
    ).first()

    if not video:
        return error_response(404, "REQUEST_007", "영상을 찾을 수 없거나 권한이 없습니다.")

    if request.title is not None:
        video.title = request.title

    db.commit()

    return success_response(
        data={"id": video.id, "title": video.title},
        message="영상이 수정되었습니다.",
    )
