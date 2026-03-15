from sqlalchemy import create_engine, text, inspect
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
    import app.models.video_like
    import app.models.comment
    import app.models.preset
    import app.models.asset

    Base.metadata.create_all(bind=engine)

    # 기존 테이블에 누락된 컬럼 자동 추가
    _migrate_missing_columns()


def _migrate_missing_columns():
    """create_all은 새 컬럼을 추가하지 않으므로 수동으로 ALTER TABLE 실행"""
    insp = inspect(engine)
    migrations = [
        ("assets", "custom_tags", "JSON NULL"),
    ]
    for table, column, col_type in migrations:
        if table in insp.get_table_names():
            existing = [c["name"] for c in insp.get_columns(table)]
            if column not in existing:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                    print(f"[migrate] Added column {table}.{column}")
