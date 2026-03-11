from fastapi import APIRouter, Query

from app.schemas.video import (
    VideoDetailResponse,
    VideoListResponse,
    VideoSearchResponse,
)
from app.utils.error_response import error_response
from app.utils.success_response import success_response

router = APIRouter()

VIDEO_ITEMS = [
    {
        "id": 1,
        "title": "토끼의 우주 모험",
        "category_id": 1,
        "video_url": "https://cdn.example.com/video1.mp4",
        "thumbnail_url": "https://cdn.example.com/thumb1.jpg",
        "like_count": 23,
        "comment_count": 5,
        "view_count": 120,
        "liked": True,
    },
    {
        "id": 2,
        "title": "히어로의 늦잠",
        "category_id": 2,
        "video_url": "https://cdn.example.com/video2.mp4",
        "thumbnail_url": "https://cdn.example.com/thumb2.jpg",
        "like_count": 15,
        "comment_count": 2,
        "view_count": 98,
        "liked": False,
    },
    {
        "id": 3,
        "title": "토끼와 친구들",
        "category_id": 1,
        "video_url": "https://cdn.example.com/video3.mp4",
        "thumbnail_url": "https://cdn.example.com/thumb3.jpg",
        "like_count": 10,
        "comment_count": 2,
        "view_count": 87,
        "liked": False,
    },
]


def serialize_video_list_item(video: dict) -> dict:
    return {
        "id": video["id"],
        "title": video["title"],
        "category_id": video["category_id"],
        "thumbnail_url": video["thumbnail_url"],
        "like_count": video["like_count"],
        "comment_count": video["comment_count"],
        "liked": video["liked"],
    }


def serialize_video_search_item(video: dict) -> dict:
    return {
        "id": video["id"],
        "title": video["title"],
        "category_id": video["category_id"],
        "thumbnail_url": video["thumbnail_url"],
        "like_count": video["like_count"],
        "comment_count": video["comment_count"],
        "view_count": video["view_count"],
    }


@router.get("/videos", response_model=VideoListResponse)
def get_videos():
    videos = sorted(VIDEO_ITEMS, key=lambda video: video["like_count"], reverse=True)
    return success_response(
        data={"videos": [serialize_video_list_item(video) for video in videos]},
        message="영상 목록 조회 성공",
    )


@router.get("/videos/search", response_model=VideoSearchResponse)
def search_videos(title: str = Query(..., min_length=1)):
    keyword = title.strip().lower()
    matched_videos = [
        video for video in VIDEO_ITEMS if keyword in video["title"].lower()
    ]
    return success_response(
        data={"videos": [serialize_video_search_item(video) for video in matched_videos]},
        message="영상 검색 성공",
    )


@router.get("/videos/{video_id}", response_model=VideoDetailResponse)
def get_video_detail(video_id: int):
    video = next((item for item in VIDEO_ITEMS if item["id"] == video_id), None)
    if not video:
        return error_response(404, "REQUEST_007", "영상을 찾을 수 없습니다.")

    return success_response(
        data={"videos": video},
        message="영상 상세 조회 성공",
    )
