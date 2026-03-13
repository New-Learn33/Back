from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, ForeignKey
from datetime import datetime
from app.db.database import Base


class Preset(Base):
    __tablename__ = "presets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    prompt = Column(Text, nullable=False)
    category_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
