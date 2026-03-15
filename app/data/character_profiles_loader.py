# DB 기반 캐릭터 프로필 로더

import random
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.services.asset_library_service import asset_to_dict


def pick_random_character(category_id: int, user_id: int, db: Session) -> dict | None:
    """해당 유저의 에셋 중 카테고리에 맞는 것을 랜덤 선택"""
    assets = db.query(Asset).filter(
        Asset.user_id == user_id,
        Asset.category_id == category_id,
    ).all()

    if not assets:
        return None

    selected = random.choice(assets)
    return asset_to_dict(selected)
