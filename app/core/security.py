from jose import jwt, JWTError
from datetime import datetime, timedelta
from passlib.context import CryptContext
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
# JWT 서명 알고리즘
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# 비밀번호 해싱
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT 만드는 함수
def create_access_token(data: dict):
    
    if not SECRET_KEY:
        raise ValueError("JWT_SECRET is not set")
    
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    # payload를 SECRET_KEY로 서명해서 문자열 토큰으로 변환
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# JWT decode 함수
def decode_access_token(token: str):
    if not SECRET_KEY:
        raise ValueError("JWT_SECRET is not set")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None