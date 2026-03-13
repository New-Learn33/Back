from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, Text
from datetime import datetime
from app.db.database import Base


class Preset(Base):
    __tablename__ = "presets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)  # 프리셋 이름
    prompt = Column(Text, nullable=False)  # 저장된 프롬프트
    category_id = Column(Integer, nullable=False)  # 카테고리

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
