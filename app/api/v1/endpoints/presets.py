from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.database import get_db
from app.models.preset import Preset
from app.utils.success_response import success_response
from app.utils.error_response import error_response

router = APIRouter()


# --- Schemas ---
class PresetCreate(BaseModel):
    name: str
    prompt: str
    category_id: int


class PresetUpdate(BaseModel):
    name: Optional[str] = None
    prompt: Optional[str] = None
    category_id: Optional[int] = None


# --- Endpoints ---

# 프리셋 목록 조회
@router.get("")
def get_presets(db: Session = Depends(get_db)):
    # TODO: 인증 후 user_id 사용, 지금은 테스트용 user_id=1
    user_id = 1
    presets = db.query(Preset).filter(Preset.user_id == user_id).order_by(Preset.updated_at.desc()).all()

    return success_response(
        {
            "presets": [
                {
                    "id": p.id,
                    "name": p.name,
                    "prompt": p.prompt,
                    "category_id": p.category_id,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in presets
            ]
        },
        "프리셋 목록 조회 성공"
    )


# 프리셋 저장
@router.post("")
def create_preset(request: PresetCreate, db: Session = Depends(get_db)):
    user_id = 1  # TODO: 인증

    preset = Preset(
        user_id=user_id,
        name=request.name,
        prompt=request.prompt,
        category_id=request.category_id,
    )
    db.add(preset)
    db.commit()
    db.refresh(preset)

    return success_response(
        {
            "id": preset.id,
            "name": preset.name,
            "prompt": preset.prompt,
            "category_id": preset.category_id,
        },
        "프리셋 저장 성공"
    )


# 프리셋 수정
@router.patch("/{preset_id}")
def update_preset(preset_id: int, request: PresetUpdate, db: Session = Depends(get_db)):
    user_id = 1  # TODO: 인증

    preset = db.query(Preset).filter(Preset.id == preset_id, Preset.user_id == user_id).first()
    if not preset:
        return error_response(404, "PRESET_001", "프리셋을 찾을 수 없습니다.")

    if request.name is not None:
        preset.name = request.name
    if request.prompt is not None:
        preset.prompt = request.prompt
    if request.category_id is not None:
        preset.category_id = request.category_id

    db.commit()

    return success_response(
        {
            "id": preset.id,
            "name": preset.name,
            "prompt": preset.prompt,
            "category_id": preset.category_id,
        },
        "프리셋 수정 성공"
    )


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
