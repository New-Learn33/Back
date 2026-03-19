from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.database import get_db
from app.models.preset import Preset
from app.utils.success_response import success_response
from app.utils.error_response import error_response

router = APIRouter()


SETTINGS_FIELDS = ["art_style", "genre", "image_quality", "motion_intensity"]


def serialize_preset(p: Preset) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "prompt": p.prompt,
        "category_id": p.category_id,
        "art_style": p.art_style,
        "genre": p.genre,
        "image_quality": p.image_quality,
        "motion_intensity": p.motion_intensity,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


# --- Schemas ---
class PresetCreate(BaseModel):
    name: str
    prompt: str
    category_id: int
    art_style: Optional[str] = None
    genre: Optional[str] = None
    image_quality: Optional[str] = None
    motion_intensity: Optional[str] = None


class PresetUpdate(BaseModel):
    name: Optional[str] = None
    prompt: Optional[str] = None
    category_id: Optional[int] = None
    art_style: Optional[str] = None
    genre: Optional[str] = None
    image_quality: Optional[str] = None
    motion_intensity: Optional[str] = None


# --- Endpoints ---

# 프리셋 목록 조회
@router.get("")
def get_presets(db: Session = Depends(get_db)):
    user_id = 1  # TODO: 인증
    presets = db.query(Preset).filter(Preset.user_id == user_id).order_by(Preset.updated_at.desc()).all()
    return success_response(
        {"presets": [serialize_preset(p) for p in presets]},
        "프리셋 목록 조회 성공"
    )


# 프리셋 저장
@router.post("")
def create_preset(request: PresetCreate, db: Session = Depends(get_db)):
    user_id = 1  # TODO: 인증

    try:
        preset = Preset(
            user_id=user_id,
            name=request.name,
            prompt=request.prompt,
            category_id=request.category_id,
            art_style=request.art_style,
            genre=request.genre,
            image_quality=request.image_quality,
            motion_intensity=request.motion_intensity,
        )
        db.add(preset)
        db.commit()
        db.refresh(preset)

        return success_response(serialize_preset(preset), "프리셋 저장 성공")
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return error_response(500, "PRESET_002", f"프리셋 저장 실패: {str(e)}")


# 프리셋 수정
@router.patch("/{preset_id}")
def update_preset(preset_id: int, request: PresetUpdate, db: Session = Depends(get_db)):
    user_id = 1  # TODO: 인증

    preset = db.query(Preset).filter(Preset.id == preset_id, Preset.user_id == user_id).first()
    if not preset:
        return error_response(404, "PRESET_001", "프리셋을 찾을 수 없습니다.")

    for field in ["name", "prompt", "category_id"] + SETTINGS_FIELDS:
        val = getattr(request, field, None)
        if val is not None:
            setattr(preset, field, val)

    db.commit()

    return success_response(serialize_preset(preset), "프리셋 수정 성공")


# 프리셋 삭제
@router.delete("/{preset_id}")
def delete_preset(preset_id: int, db: Session = Depends(get_db)):
    user_id = 1  # TODO: 인증

    preset = db.query(Preset).filter(Preset.id == preset_id, Preset.user_id == user_id).first()
    if not preset:
        return error_response(404, "PRESET_001", "프리셋을 찾을 수 없습니다.")

    db.delete(preset)
    db.commit()

    return success_response({"id": preset_id}, "프리셋 삭제 성공")
