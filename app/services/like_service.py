from sqlalchemy.orm import Session

from app.models.video import Video
from app.models.video_like import VideoLike


def get_like(db: Session, *, video_id: int, user_id: int):
    return (
        db.query(VideoLike)
        .filter(VideoLike.video_id == video_id, VideoLike.user_id == user_id)
        .first()
    )


def create_like(db: Session, *, video_id: int, user_id: int) -> VideoLike:
    like = VideoLike(video_id=video_id, user_id=user_id)
    db.add(like)
    video = db.query(Video).filter(Video.id == video_id).first()
    if video:
        video.like_count += 1
    db.commit()
    db.refresh(like)
    return like


def delete_like(db: Session, like: VideoLike) -> None:
    video = db.query(Video).filter(Video.id == like.video_id).first()
    if video and video.like_count > 0:
        video.like_count -= 1
    db.delete(like)
    db.commit()


def count_likes_by_video(db: Session, video_id: int) -> int:
    video = db.query(Video).filter(Video.id == video_id).first()
    return video.like_count if video else 0
