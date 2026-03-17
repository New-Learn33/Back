from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.models.user import User


def get_user_by_ws_token(db: Session, token: str):
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id = payload.get("user_id")
    if not user_id:
        return None

    return db.query(User).filter(User.id == int(user_id)).first()