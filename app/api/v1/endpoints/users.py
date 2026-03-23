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
from app.models.user import STORAGE_LIMIT_BYTES
from app.models.generation_job import GenerationJob
from app.models.video import Video
from app.models.comment import Comment
from app.models.video_like import VideoLike
from app.models.notification import Notification
from app.models.generation_scene import GenerationScene
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
        "view_count": getattr(video, 'view_count', 0) or 0,
    }


def serialize_user_comment(comment) -> dict:
    return {
        "id": comment.id,
        "video_id": comment.video_id,
        "video_title": getattr(comment, 'video_title', None),
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


@router.get("/me/storage")
def get_my_storage(current_user: User = Depends(get_current_user)):
    if isinstance(current_user, JSONResponse):
        return current_user

    used = current_user.storage_used or 0
    return success_response(
        data={
            "storage_used": used,
            "storage_limit": STORAGE_LIMIT_BYTES,
            "storage_used_mb": round(used / (1024 ** 2), 1),
            "storage_used_gb": round(used / (1024 ** 3), 2),
            "storage_limit_gb": round(STORAGE_LIMIT_BYTES / (1024 ** 3), 1),
        },
        message="저장공간 조회 성공",
    )


@router.get("/me/projects")
def get_my_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """내 작업 목록: 완료된 영상 + 진행중인 생성 작업"""
    if isinstance(current_user, JSONResponse):
        return current_user

    try:
        # 완료된 영상
        videos = list_videos_by_user(db, current_user.id)
        # 진행중인 생성 작업 (pending, processing)
        jobs = (
            db.query(GenerationJob)
            .filter(
                GenerationJob.user_id == current_user.id,
                GenerationJob.status.in_(["pending", "processing"]),
            )
            .order_by(GenerationJob.created_at.desc())
            .all()
        )
    except SQLAlchemyError:
        db.rollback()
        return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

    projects = []

    # 완료된 영상
    for v in videos:
        projects.append({
            "id": v.id,
            "job_id": v.job_id,
            "type": "video",
            "title": v.title,
            "category_id": v.category_id,
            "thumbnail_url": v.thumbnail_url or "",
            "video_url": v.video_url or "",
            "status": "completed",
            "like_count": v.like_count,
            "comment_count": v.comment_count,
            "view_count": getattr(v, "view_count", 0) or 0,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        })

    # 진행중인 작업
    for j in jobs:
        projects.append({
            "id": j.id,
            "type": "job",
            "title": j.title or "생성 중...",
            "category_id": j.category_id,
            "thumbnail_url": j.thumbnail_url or "",
            "video_url": "",
            "status": j.status,  # pending or processing
            "progress": j.progress or 0,
            "like_count": 0,
            "comment_count": 0,
            "view_count": 0,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        })

    # 최신순 정렬
    projects.sort(key=lambda p: p.get("created_at") or "", reverse=True)

    return success_response(
        data={"projects": projects},
        message="작업 목록 조회 성공",
    )


@router.delete("/me/projects/{job_id}")
def cancel_my_project(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """작업 삭제 (진행중이면 취소, 완료면 삭제)"""
    if isinstance(current_user, JSONResponse):
        return current_user

    job = (
        db.query(GenerationJob)
        .filter(GenerationJob.id == job_id, GenerationJob.user_id == current_user.id)
        .first()
    )

    if not job:
        return error_response(404, "REQUEST_007", "작업을 찾을 수 없습니다.")

    if job.status in ("pending", "processing"):
        job.status = "cancelled"
        db.commit()
        return success_response(
            data={"job_id": job.id, "status": "cancelled"},
            message="작업이 취소되었습니다.",
        )

    # 완료/실패/취소된 작업은 DB에서 삭제
    try:
        # 연결된 Video 및 관련 데이터 삭제
        video = db.query(Video).filter(Video.job_id == job.id).first()
        if video:
            db.query(Comment).filter(Comment.video_id == video.id).delete(synchronize_session=False)
            db.query(VideoLike).filter(VideoLike.video_id == video.id).delete(synchronize_session=False)
            db.query(Notification).filter(Notification.video_id == video.id).delete(synchronize_session=False)
            db.delete(video)
            db.flush()

        # job_id 기반 알림 삭제
        db.query(Notification).filter(Notification.job_id == job.id).delete(synchronize_session=False)

        # 연결된 GenerationScene 삭제
        db.query(GenerationScene).filter(GenerationScene.job_id == job.id).delete(synchronize_session=False)

        # GenerationJob 삭제
        db.delete(job)
        db.commit()
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return error_response(500, "SERVER_001", f"삭제 중 오류가 발생했습니다: {str(e)}")

    return success_response(
        data={"job_id": job_id, "status": "deleted"},
        message="작업이 삭제되었습니다.",
    )
