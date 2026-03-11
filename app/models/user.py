from sqlalchemy import BigInteger, Column, String, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

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

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)