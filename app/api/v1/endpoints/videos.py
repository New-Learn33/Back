from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import security
from app.core.security import decode_access_token
from app.db.database import get_db
from app.schemas.video import (
    VideoDetailResponse,
    VideoListResponse,
    VideoSearchResponse,
)
from app.services.video_service import (
    get_liked_video_ids,
    get_video_by_id,
    list_videos,
    search_videos_by_title,
)
from app.utils.error_response import error_response
from app.utils.success_response import success_response

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


def serialize_video_list_item(video, like_count: int, comment_count: int, liked: bool) -> dict:
    return {
        "id": video.id,
        "title": video.title,
        "category_id": video.category_id,
        "thumbnail_url": video.thumbnail_url or "",
        "like_count": like_count,
        "comment_count": comment_count,
        "liked": liked,
    }


def serialize_video_search_item(video, like_count: int, comment_count: int) -> dict:
    return {
        "id": video.id,
        "title": video.title,
        "category_id": video.category_id,
        "thumbnail_url": video.thumbnail_url or "",
        "like_count": like_count,
        "comment_count": comment_count,
        "view_count": 0,
    }


def serialize_video_detail_item(video, like_count: int, comment_count: int, liked: bool) -> dict:
    return {
        "id": video.id,
        "title": video.title,
        "category_id": video.category_id,
        "thumbnail_url": video.thumbnail_url or "",
        "like_count": like_count,
        "comment_count": comment_count,
        "liked": liked,
        "video_url": video.video_url,
        "view_count": 0,
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
    except SQLAlchemyError:
        db.rollback()
        return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

    return success_response(
        data={
            "videos": [
                serialize_video_search_item(video, video.like_count, video.comment_count)
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

    return success_response(
        data={
            "videos": serialize_video_detail_item(
                video_row,
                video_row.like_count,
                video_row.comment_count,
                video_row.id in liked_video_ids,
            )
        },
        message="영상 상세 조회 성공",
    )
