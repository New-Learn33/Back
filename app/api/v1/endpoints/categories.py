from fastapi import APIRouter
from app.schemas.category_schema import CategoryListResponse

router = APIRouter()


@router.get("", response_model=CategoryListResponse)
def get_categories():
    return {
        "success": True,
        "message": "카테고리 목록 조회 성공",
        "data": [
            {
                "id": 1,
                "name": "애니",
                "description": "감정 표현이 크고 애니메이션풍 연출",
                "template_images": [
                    {
                        "id": 101,
                        "image_url": "https://example.com/anime1.png",
                        "name": "애니 캐릭터 1"
                    },
                    {
                        "id": 102,
                        "image_url": "https://example.com/anime2.png",
                        "name": "애니 캐릭터 2"
                    }
                ]
            },
            {
                "id": 2,
                "name": "히어로",
                "description": "정의, 액션, 구출 장면 중심",
                "template_images": [
                    {
                        "id": 201,
                        "image_url": "https://example.com/hero1.png",
                        "name": "히어로 캐릭터 1"
                    },
                    {
                        "id": 202,
                        "image_url": "https://example.com/hero2.png",
                        "name": "히어로 캐릭터 2"
                    }
                ]
            },
            {
                "id": 3,
                "name": "게임",
                "description": "퀘스트, 전투, 레벨업 분위기",
                "template_images": [
                    {
                        "id": 301,
                        "image_url": "https://example.com/game1.png",
                        "name": "게임 캐릭터 1"
                    },
                    {
                        "id": 302,
                        "image_url": "https://example.com/game2.png",
                        "name": "게임 캐릭터 2"
                    }
                ]
            },
            {
                "id": 4,
                "name": "판타지",
                "description": "마법, 왕국, 모험 분위기",
                "template_images": [
                    {
                        "id": 401,
                        "image_url": "https://example.com/fantasy1.png",
                        "name": "판타지 캐릭터 1"
                    },
                    {
                        "id": 402,
                        "image_url": "https://example.com/fantasy2.png",
                        "name": "판타지 캐릭터 2"
                    }
                ]
            }
        ]
    }