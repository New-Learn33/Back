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
                "name": "로맨스",
                "description": "감성적인 대화 중심 카테고리",
                "template_images": [
                    {
                        "id": 101,
                        "image_url": "https://example.com/romance1.png",
                        "name": "기본 로맨스 템플릿"
                    }
                ]
            },
            {
                "id": 2,
                "name": "스릴러",
                "description": "긴장감 있는 전개 중심 카테고리",
                "template_images": [
                    {
                        "id": 201,
                        "image_url": "https://example.com/thriller1.png",
                        "name": "기본 스릴러 템플릿"
                    }
                ]
            }
        ]
    }