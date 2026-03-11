from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func

from app.db.database import Base


class VideoLike(Base):
    __tablename__ = "video_likes"
    __table_args__ = (
        UniqueConstraint(
            "video_id",
            "user_id",
            name="uq_video_likes_video_user",
        ),
    )

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    video_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
