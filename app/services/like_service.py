from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.like import Like


def get_like(db: Session, *, video_id: int, user_id: int):
    return (
        db.query(Like)
        .filter(Like.video_id == video_id, Like.user_id == user_id)
        .first()
    )


def create_like(db: Session, *, video_id: int, user_id: int) -> Like:
    like = Like(video_id=video_id, user_id=user_id)
    db.add(like)
    db.commit()
    db.refresh(like)
    return like


def delete_like(db: Session, like: Like) -> None:
    db.delete(like)
    db.commit()


def count_likes_by_video(db: Session, video_id: int) -> int:
    return (
        db.query(func.count(Like.id))
        .filter(Like.video_id == video_id)
        .scalar()
    ) or 0
