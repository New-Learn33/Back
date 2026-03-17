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

    # 기존 영상 썸네일 URL 수정 (rendered/ → generated/)
    _fix_thumbnail_urls()

    # 기존 에셋 file_size 및 storage_used 동기화
    _sync_storage_usage()


def _migrate_missing_columns():
    """create_all은 새 컬럼을 추가하지 않으므로 수동으로 ALTER TABLE 실행"""
    insp = inspect(engine)
    migrations = [
        ("assets", "custom_tags", "JSON NULL"),
        ("assets", "file_size", "BIGINT NOT NULL DEFAULT 0"),
        ("videos", "view_count", "INT NOT NULL DEFAULT 0"),
        ("users", "storage_used", "BIGINT NOT NULL DEFAULT 0"),
    ]
    for table, column, col_type in migrations:
        if table in insp.get_table_names():
            existing = [c["name"] for c in insp.get_columns(table)]
            if column not in existing:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
                    print(f"[migrate] Added column {table}.{column}")


def _fix_thumbnail_urls():
    """썸네일 URL 수정: rendered/ → generated/, NULL/빈값 → generated 이미지로 채움"""
    from app.models.video import Video
    from app.models.generation_job import GenerationJob
    from sqlalchemy import or_

    r2_base = os.getenv("R2_PUBLIC_BASE_URL", "")
    db = SessionLocal()
    try:
        fixed = 0

        # 1) rendered/ → generated/ 변환
        broken = db.query(Video).filter(Video.thumbnail_url.like("%/rendered/%")).all()
        for v in broken:
            v.thumbnail_url = v.thumbnail_url.replace("/rendered/", "/generated/")
            fixed += 1

        # 2) thumbnail_url이 NULL이거나 빈 문자열인 영상 → job_id 기반으로 generated 이미지 설정
        empty = db.query(Video).filter(
            or_(Video.thumbnail_url == None, Video.thumbnail_url == "")
        ).all()
        for v in empty:
            job_id = v.job_id
            if r2_base:
                v.thumbnail_url = f"{r2_base}/generated/{job_id}_1.png"
            else:
                v.thumbnail_url = f"/static/generated/{job_id}_1.png"
            fixed += 1

        if fixed:
            db.commit()
            print(f"[fix] Fixed {fixed} video thumbnail URLs ({len(broken)} rendered→generated, {len(empty)} empty→generated)")
    except Exception as e:
        db.rollback()
        print(f"[fix] Thumbnail URL fix error: {e}")
    finally:
        db.close()


def _sync_storage_usage():
    """기존 에셋의 file_size가 0인 것들을 실제 파일 크기로 업데이트하고, storage_used 재계산"""
    from app.models.asset import Asset
    from app.models.user import User

    db = SessionLocal()
    try:
        # 1) file_size가 0인 에셋들 실제 파일 크기로 업데이트 (로컬 파일이 있을 때만)
        zero_assets = db.query(Asset).filter(Asset.file_size == 0).all()
        updated_count = 0
        if zero_assets:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            for asset in zero_assets:
                image_url = asset.image_url or ""
                if image_url.startswith("/static/"):
                    file_path = os.path.join(base_dir, "app", image_url.lstrip("/"))
                    if os.path.exists(file_path):
                        asset.file_size = os.path.getsize(file_path)
                        updated_count += 1
            db.commit()
            if updated_count:
                print(f"[sync] Updated file_size for {updated_count}/{len(zero_assets)} assets")

        # 2) 유저별 storage_used 재계산 (file_size > 0인 에셋만 합산)
        from sqlalchemy import func as sqlfunc
        user_storage = (
            db.query(Asset.user_id, sqlfunc.sum(Asset.file_size))
            .filter(Asset.file_size > 0)
            .group_by(Asset.user_id)
            .all()
        )
        for user_id, total in user_storage:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.storage_used = total or 0
        db.commit()
        if user_storage:
            print(f"[sync] Recalculated storage_used for {len(user_storage)} users")
    except Exception as e:
        db.rollback()
        print(f"[sync] Storage sync error: {e}")
    finally:
        db.close()
