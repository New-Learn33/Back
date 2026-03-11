# character_profiles.json을 읽어오는 역할

import json
import os
from typing import Dict, List, Any

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # app/
DATA_DIR = os.path.join(BASE_DIR, "data")
PROFILE_PATH = os.path.join(DATA_DIR, "character_profiles.json")

_cached_profiles: Dict[str, List[dict]] | None = None


def load_character_profiles(force_reload: bool = False) -> Dict[str, List[dict]]:
    global _cached_profiles

    if _cached_profiles is not None and not force_reload:
        return _cached_profiles

    if not os.path.exists(PROFILE_PATH):
        raise FileNotFoundError(
            f"character_profiles.json 파일이 없습니다: {PROFILE_PATH}"
        )

    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 카테고리 key를 문자열로 통일
    normalized: Dict[str, List[dict]] = {}
    for key, value in data.items():
        normalized[str(key)] = value

    _cached_profiles = normalized
    return _cached_profiles


def get_profiles_by_category(category_id: int) -> List[dict]:
    profiles = load_character_profiles()
    return profiles.get(str(category_id), [])


def pick_random_character(category_id: int) -> dict | None:
    import random

    candidates = get_profiles_by_category(category_id)
    if not candidates:
        return None
    return random.choice(candidates)