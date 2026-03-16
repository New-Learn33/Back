from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from datetime import datetime
from app.db.database import Base


class GenerationScene(Base):
    __tablename__ = "generation_scenes"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False)
    scene_order = Column(Integer, nullable=False)

    dialogue = Column(Text, nullable=True)
    subtitle_text = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)