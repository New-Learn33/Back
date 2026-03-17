from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.db.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)

    recipient_user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )
    actor_user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    type = Column(String(50), nullable=False, index=True)  
    # like / comment / video_completed / video_failed

    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    video_id = Column(BigInteger, nullable=True, index=True)
    comment_id = Column(BigInteger, nullable=True, index=True)
    job_id = Column(Integer, nullable=True, index=True)

    is_read = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)