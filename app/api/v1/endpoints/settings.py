from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.api.v1.endpoints.auth import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.utils.success_response import success_response
from app.utils.error_response import error_response

router = APIRouter()


class SettingsUpdate(BaseModel):
    notifications_enabled: Optional[bool] = None
    auto_save: Optional[bool] = None
    default_quality: Optional[str] = None
    language: Optional[str] = None


VALID_QUALITIES = {"low", "medium", "high", "ultra"}
VALID_LANGUAGES = {"ko", "en", "ja"}


def serialize_settings(user: User) -> dict:
    return {
        "notifications_enabled": user.notifications_enabled if user.notifications_enabled is not None else True,
        "auto_save": user.auto_save if user.auto_save is not None else True,
        "default_quality": user.default_quality or "high",
        "language": user.language or "ko",
    }


@router.get("")
def get_settings(current_user: User = Depends(get_current_user)):
    if isinstance(current_user, JSONResponse):
        return current_user

    return success_response(
        data={"settings": serialize_settings(current_user)},
        message="환경설정 조회 성공",
    )


@router.patch("")
def update_settings(
    request: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if isinstance(current_user, JSONResponse):
        return current_user

    updates = request.model_dump(exclude_none=True)
    if not updates:
        return error_response(400, "REQUEST_001", "수정할 항목이 없습니다.")

    if "default_quality" in updates and updates["default_quality"] not in VALID_QUALITIES:
        return error_response(400, "REQUEST_001", f"유효하지 않은 화질입니다. ({', '.join(VALID_QUALITIES)})")

    if "language" in updates and updates["language"] not in VALID_LANGUAGES:
        return error_response(400, "REQUEST_001", f"유효하지 않은 언어입니다. ({', '.join(VALID_LANGUAGES)})")

    try:
        for field, value in updates.items():
            setattr(current_user, field, value)

        db.add(current_user)
        db.commit()
        db.refresh(current_user)
    except Exception:
        db.rollback()
        return error_response(500, "SERVER_001", "설정 저장에 실패했습니다.")

    return success_response(
        data={"settings": serialize_settings(current_user)},
        message="환경설정 저장 성공",
    )
