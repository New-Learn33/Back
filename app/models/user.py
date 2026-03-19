from sqlalchemy import BigInteger, Boolean, Column, String, DateTime, Integer
from sqlalchemy.sql import func
from app.db.database import Base

STORAGE_LIMIT_BYTES = 3 * 1024 * 1024 * 1024  # 3GB

# 구글 로그인한 사용자를 저장
class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    nickname = Column(String(100), nullable=False, default="익명의 참가자")
    password_hash = Column(String(255), nullable=True)
    profile_image_url = Column(String(500), nullable=True)
    provider = Column(String(50), nullable=False)
    provider_id = Column(String(255), nullable=False, unique=True)
    storage_used = Column(BigInteger, default=0, nullable=False)  # bytes

    # 환경설정
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    auto_save = Column(Boolean, default=True, nullable=False)
    default_quality = Column(String(20), default="high", nullable=False)
    language = Column(String(10), default="ko", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)