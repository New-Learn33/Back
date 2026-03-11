from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

#.env에서 DB 주소 가져옴
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#요청 들어옴 -> DB 세션 생성 -> 라우터/서비스에서 사용
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 모든 모델 import 후 테이블 생성
def init_db():
    import app.models.user
    import app.models.generation_job
    import app.models.video

    Base.metadata.create_all(bind=engine)