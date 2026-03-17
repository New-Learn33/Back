from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.services.websocket_manager import notification_ws_manager


def serialize_notification(notification: Notification):
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
    }


def get_unread_count(db: Session, user_id: int) -> int:
    return (
        db.query(Notification)
        .filter(
            Notification.recipient_user_id == user_id,
            Notification.is_read == False
        )
        .count()
    )


def list_notifications(db: Session, user_id: int):
    return (
        db.query(Notification)
        .filter(Notification.recipient_user_id == user_id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .all()
    )


def mark_notification_as_read(db: Session, notification_id: int, user_id: int):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.recipient_user_id == user_id
        )
        .first()
    )

    if not notification:
        return None

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_notifications_as_read(db: Session, user_id: int):
    notifications = (
        db.query(Notification)
        .filter(
            Notification.recipient_user_id == user_id,
            Notification.is_read == False
        )
        .all()
    )

    count = 0
    for notification in notifications:
        notification.is_read = True
        count += 1

    db.commit()
    return count


async def push_notification_to_user(db: Session, user_id: int, notification: Notification):
    unread_count = get_unread_count(db, user_id)

    await notification_ws_manager.send_to_user(
        user_id,
        {
            "type": "notification",
            "event": "created",
            "unread_count": unread_count,
            "notification": serialize_notification(notification),
        },
    )


def create_notification(
    db: Session,
    *,
    recipient_user_id: int,
    actor_user_id: int | None,
    type: str,
    title: str,
    message: str,
    video_id: int | None = None,
    comment_id: int | None = None,
    job_id: int | None = None,
):
    notification = Notification(
        recipient_user_id=recipient_user_id,
        actor_user_id=actor_user_id,
        type=type,
        title=title,
        message=message,
        video_id=video_id,
        comment_id=comment_id,
        job_id=job_id,
        is_read=False,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification