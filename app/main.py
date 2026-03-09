from fastapi import FastAPI
from app.api.v1.api import api_router
from app.db.database import Base, engine
from app.models.user import User

app = FastAPI(
    title="NewLearn API",
    version="1.0"
)

@app.get("/")
def root():
    return {"message": "server running"}

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

# 라우터 연결
app.include_router(api_router, prefix="/api/v1")