from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.db.database import Base


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    category_id = Column(Integer, nullable=True)

    # job 상태
    # pending    : 생성 요청 후 아직 처리 시작 전
    # processing : 자막 합성 / 영상 생성 진행 중
    # completed  : 영상 생성 완료
    # failed     : 생성 중 오류 발생
    
    status = Column(String(50), default="pending")
    progress = Column(Integer, default=0)

    video_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
