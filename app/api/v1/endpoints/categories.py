from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.asset import Asset

router = APIRouter()


CATEGORY_META = {
    1: {"id": 1, "name": "ani", "description": "애니풍 캐릭터"},
    2: {"id": 2, "name": "hero", "description": "히어로풍 캐릭터"},
    3: {"id": 3, "name": "game", "description": "게임풍 캐릭터"},
    4: {"id": 4, "name": "fantasy", "description": "판타지풍 캐릭터"},
}


@router.get("")
def get_categories(db: Session = Depends(get_db)):
    result = []
    for category_id, meta in CATEGORY_META.items():
        characters = db.query(Asset).filter(Asset.category_id == category_id).all()

        result.append(
            {
                "id": meta["id"],
                "name": meta["name"],
                "description": meta["description"],
                "template_images": [
                    {
                        "id": character.id,
                        "name": character.name,
                        "image_url": character.image_url,
                    }
                    for character in characters
                ],
            }
        )

    return {
        "success": True,
        "message": "카테고리 목록 조회 성공",
        "data": result,
    }
