from sqlalchemy.orm import Session

from app.models.comment import Comment
from app.models.user import User


def create_comment(db: Session, *, video_id: int, user_id: int, content: str) -> Comment:
    comment = Comment(video_id=video_id, user_id=user_id, content=content)
    db.add(comment)
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
    db.delete(comment)
    db.commit()
