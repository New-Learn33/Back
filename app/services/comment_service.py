from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.user import User
from app.models.video import Video


def create_comment(db: Session, *, video_id: int, user_id: int, content: str) -> Comment:
    comment = Comment(video_id=video_id, user_id=user_id, content=content)
    db.add(comment)
    video = db.query(Video).filter(Video.id == video_id).first()
    if video:
        video.comment_count += 1
    db.commit()
    db.refresh(comment)
    return comment


def get_comment_with_user(db: Session, comment_id: int):
    return (
        db.query(Comment, User.nickname)
        .join(User, User.id == Comment.user_id)
        .filter(Comment.id == comment_id)
        .first()
    )


def list_comments_by_video(db: Session, video_id: int):
    return (
        db.query(Comment, User.nickname)
        .join(User, User.id == Comment.user_id)
        .filter(Comment.video_id == video_id)
        .order_by(Comment.created_at.asc(), Comment.id.asc())
        .all()
    )


def get_comment_by_id(db: Session, comment_id: int):
    return db.query(Comment).filter(Comment.id == comment_id).first()


def delete_comment(db: Session, comment: Comment) -> None:
    video = db.query(Video).filter(Video.id == comment.video_id).first()
    if video and video.comment_count > 0:
        video.comment_count -= 1
    db.delete(comment)
    db.commit()


def list_comments_by_user(db: Session, user_id: int):
    from app.models.generation_job import GenerationJob
    results = (
        db.query(Comment, GenerationJob.title)
        .outerjoin(GenerationJob, Comment.video_id == GenerationJob.id)
        .filter(Comment.user_id == user_id)
        .order_by(Comment.created_at.desc(), Comment.id.desc())
        .all()
    )
    # (Comment, title) 튜플에 video_title 속성 부착
    comments = []
    for comment, video_title in results:
        comment.video_title = video_title
        comments.append(comment)
    return comments
