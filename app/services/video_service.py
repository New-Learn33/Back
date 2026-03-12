from sqlalchemy.orm import Session

from app.models.video import Video
from app.models.video_like import VideoLike


def list_videos(db: Session, sort: str = "popular"):
    query = db.query(Video)

    if sort == "latest":
        return query.order_by(Video.created_at.desc()).all()

    return query.order_by(Video.like_count.desc(), Video.created_at.desc()).all()


def search_videos_by_title(db: Session, keyword: str):
    return (
        db.query(Video)
        .filter(Video.title.ilike(f"%{keyword}%"))
        .order_by(Video.created_at.desc())
        .all()
    )


def get_video_by_id(db: Session, video_id: int):
    return db.query(Video).filter(Video.id == video_id).first()


def get_liked_video_ids(db: Session, user_id: int, video_ids: list[int]):
    if not video_ids:
        return set()

    rows = (
        db.query(VideoLike.video_id)
        .filter(VideoLike.user_id == user_id, VideoLike.video_id.in_(video_ids))
        .all()
    )
    return {video_id for (video_id,) in rows}


def list_videos_by_user(db: Session, user_id: int):
    return (
        db.query(Video)
        .filter(Video.user_id == user_id)
        .order_by(Video.created_at.desc())
        .all()
    )


def list_liked_videos_by_user(db: Session, user_id: int):
    return (
        db.query(Video)
        .join(VideoLike, VideoLike.video_id == Video.id)
        .filter(VideoLike.user_id == user_id)
        .order_by(VideoLike.created_at.desc())
        .all()
    )
