from sqlalchemy import Column, Integer, String, DateTime, BigInteger, ForeignKey, Text, JSON
from datetime import datetime
from app.db.database import Base


class Preset(Base):
    __tablename__ = "presets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)  # 프리셋 이름
    prompt = Column(Text, nullable=False)  # 저장된 프롬프트
    category_id = Column(Integer, nullable=False, default=0)  # 하위 호환
    tags = Column(JSON, nullable=True)  # 태그 기반 프리셋
    art_style = Column(String(50), nullable=True)
    genre = Column(String(50), nullable=True)
    image_quality = Column(String(20), nullable=True)
    motion_intensity = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
