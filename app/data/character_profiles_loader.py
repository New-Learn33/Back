# DB 기반 캐릭터 프로필 로더

import random
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.asset import Asset
from app.services.asset_library_service import asset_to_dict, normalize_tags


def pick_random_character(
    user_id: int,
    db: Session,
    tags: Optional[List[str]] = None,
    category_id: Optional[int] = None,
) -> dict | None:
    """해당 유저의 에셋 중 태그(우선) 또는 카테고리(하위 호환) 기준으로 랜덤 선택"""
    query = db.query(Asset).filter(Asset.user_id == user_id)

    normalized_tags = normalize_tags(tags or [])

    if normalized_tags:
        candidates: List[dict] = []
        for asset in query.all():
            info = asset_to_dict(asset)
            asset_tags = set(normalize_tags(info.get("tags") or []))
            if any(tag in asset_tags for tag in normalized_tags):
                candidates.append(info)
        if not candidates:
            return None
        return random.choice(candidates)

    if category_id is not None:
        assets = query.filter(Asset.category_id == category_id).all()
        if not assets:
            return None
        selected = random.choice(assets)
        return asset_to_dict(selected)

    return None
