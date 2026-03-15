from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func

from app.db.database import Base


class Asset(Base):
    __tablename__ = "assets"

    id = Column(String(255), primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    category_id = Column(Integer, nullable=False)

    name = Column(String(255), nullable=False)
    image_url = Column(String(500), nullable=False)
    category_hint = Column(String(255), nullable=True)
    character_name = Column(String(255), nullable=True)
    gender = Column(String(50), nullable=True)

    appearance = Column(JSON, nullable=True)
    outfit = Column(JSON, nullable=True)
    style_keywords = Column(JSON, nullable=True)
    forbidden_changes = Column(JSON, nullable=True)
    custom_tags = Column(JSON, nullable=True)  # 사용자 정의 태그 ["주인공", "검사"]

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
