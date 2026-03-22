from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.schemas.notification import (
    NotificationListResponse,
    NotificationReadAllResponse,
    NotificationReadResponse,
)
from app.services.auth_ws_service import get_user_by_ws_token
from app.services.notification_service import (
    get_unread_count,
    list_notifications,
    mark_all_notifications_as_read,
    mark_notification_as_read,
)
from app.services.websocket_manager import notification_ws_manager
from app.utils.error_response import error_response
from app.utils.success_response import success_response

router = APIRouter()


def serialize_notification_item(notification):
    return {
        "id": notification.id,
        "recipient_user_id": notification.recipient_user_id,
        "actor_user_id": notification.actor_user_id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "video_id": notification.video_id,
        "comment_id": notification.comment_id,
        "job_id": notification.job_id,
        "is_read": notification.is_read,
        "created_at": (notification.created_at.isoformat() + "+00:00") if notification.created_at else None,
    }


@router.get("/notifications", response_model=NotificationListResponse)
def get_my_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    notifications = list_notifications(db, current_user.id)
    unread_count = get_unread_count(db, current_user.id)

    return success_response(
        data={
            "notifications": [serialize_notification_item(n) for n in notifications],
            "unread_count": unread_count,
        },
        message="알림 목록 조회 성공",
    )


@router.patch("/notifications/{notification_id}/read", response_model=NotificationReadResponse)
def read_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    notification = mark_notification_as_read(db, notification_id, current_user.id)
    if not notification:
        return error_response(404, "REQUEST_007", "알림을 찾을 수 없습니다.")

    return success_response(
        data={"notification_id": notification.id},
        message="알림 읽음 처리 성공",
    )


@router.patch("/notifications/read-all", response_model=NotificationReadAllResponse)
def read_all_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    updated_count = mark_all_notifications_as_read(db, current_user.id)

    return success_response(
        data={"updated_count": updated_count},
        message="전체 알림 읽음 처리 성공",
    )


@router.websocket("/ws/notifications")
async def notification_websocket(websocket: WebSocket):
    token = websocket.query_params.get("token")

    db = SessionLocal()
    try:
        user = get_user_by_ws_token(db, token)
        if not user:
            await websocket.close(code=1008)
            return

        await notification_ws_manager.connect(user.id, websocket)

        unread_count = get_unread_count(db, user.id)
        await websocket.send_json(
            {
                "type": "notification",
                "event": "connected",
                "unread_count": unread_count,
            }
        )

        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        if "user" in locals() and user:
            notification_ws_manager.disconnect(user.id, websocket)
    except Exception:
        if "user" in locals() and user:
            notification_ws_manager.disconnect(user.id, websocket)
    finally:
        db.close()