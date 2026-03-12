from jose import jwt, JWTError
from datetime import datetime, timedelta
import bcrypt
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET")
# JWT 서명 알고리즘
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# 비밀번호 해싱
def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )

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