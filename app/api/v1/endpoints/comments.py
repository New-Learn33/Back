import asyncio
from app.services.notification_service import create_notification, push_notification_to_user
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.comment import (
    CommentCreateRequest,
    CommentCreateResponse,
    CommentDeleteResponse,
    CommentListResponse,
)
from app.services.comment_service import (
    create_comment,
    delete_comment,
    get_comment_by_id,
    get_comment_with_user,
    list_comments_by_video,
)
from app.services.video_service import get_video_by_id
from app.utils.error_response import error_response
from app.utils.success_response import success_response

router = APIRouter()


def serialize_comment(comment, nickname: str):
    return {
        "comment_id": comment.id,
        "video_id": comment.video_id,
        "nickname": nickname,
        "content": comment.content,
    }

# 알림 기능 추가 전 댓글 작성 API
# @router.post("/videos/{video_id}/comments", response_model=CommentCreateResponse)
# def create_video_comment(
#     video_id: int,
#     request: CommentCreateRequest,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db),
# ):
#     if isinstance(current_user, JSONResponse):
#         return current_user

#     if not get_video_by_id(db, video_id):
#         return error_response(404, "REQUEST_007", "영상을 찾을 수 없습니다.")

#     try:
#         comment = create_comment(
#             db,
#             video_id=video_id,
#             user_id=current_user.id,
#             content=request.content.strip(),
#         )
#         comment_row = get_comment_with_user(db, comment.id)
#     except SQLAlchemyError:
#         db.rollback()
#         return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

#     saved_comment, nickname = comment_row
#     return success_response(
#         data={"comment": serialize_comment(saved_comment, nickname)},
#         message="댓글 작성 성공",
#         status_code=201,
#     )

# 댓글 작성 API를 백그라운드 작업으로 처리하여 알림 전송과 DB 작업이 동시에 이루어지도록 개선
@router.post("/videos/{video_id}/comments", response_model=CommentCreateResponse)
def create_video_comment(
    video_id: int,
    request: CommentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    video = get_video_by_id(db, video_id)
    if not video:
        return error_response(404, "REQUEST_007", "영상을 찾을 수 없습니다.")

    try:
        comment = create_comment(
            db,
            video_id=video_id,
            user_id=current_user.id,
            content=request.content.strip(),
        )
        comment_row = get_comment_with_user(db, comment.id)

        if video.user_id != current_user.id:
            notification = create_notification(
                db,
                recipient_user_id=video.user_id,
                actor_user_id=current_user.id,
                type="comment",
                title="댓글 알림",
                message=f"{current_user.nickname}님이 회원님의 영상에 댓글을 남겼습니다.",
                video_id=video.id,
                comment_id=comment.id,
            )
            asyncio.run(push_notification_to_user(db, video.user_id, notification))

    except SQLAlchemyError:
        db.rollback()
        return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

    saved_comment, nickname = comment_row
    return success_response(
        data={"comment": serialize_comment(saved_comment, nickname)},
        message="댓글 작성 성공",
        status_code=201,
    )

@router.get("/videos/{video_id}/comments", response_model=CommentListResponse)
def get_video_comments(video_id: int, db: Session = Depends(get_db)):
    if not get_video_by_id(db, video_id):
        return error_response(404, "REQUEST_007", "영상을 찾을 수 없습니다.")

    comments = list_comments_by_video(db, video_id)
    return success_response(
        data={
            "comments": [
                serialize_comment(comment, nickname) for comment, nickname in comments
            ]
        },
        message="댓글 목록 조회 성공",
    )


@router.delete("/comments/{comment_id}", response_model=CommentDeleteResponse)
def delete_my_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    comment = get_comment_by_id(db, comment_id)
    if not comment:
        return error_response(404, "REQUEST_007", "댓글을 찾을 수 없습니다.")

    if comment.user_id != current_user.id:
        return error_response(403, "REQUEST_007", "잘못된 접근입니다.")

    try:
        delete_comment(db, comment)
    except SQLAlchemyError:
        db.rollback()
        return error_response(500, "RESPONSE_001", "서버와의 연결에 실패했습니다.")

    return success_response(
        data={"comment_id": comment_id},
        message="댓글 삭제 성공",
    )
