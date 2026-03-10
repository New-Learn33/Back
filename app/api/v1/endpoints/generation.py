from fastapi import APIRouter
from app.schemas.generation_schema import (
    ScriptGenerateRequest,
    ScriptGenerateResponse,
    ImageGenerateRequest,
    ImageGenerateResponse,
)

router = APIRouter()


@router.post("/scripts", response_model=ScriptGenerateResponse)
def generate_scripts(request: ScriptGenerateRequest):
    return {
        "success": True,
        "message": "3컷 대사 생성 성공",
        "data": {
            "job_id": 1,
            "scenes": [
                {
                    "scene_order": 1,
                    "dialogue": "오랜만이네. 진짜 너 맞구나?",
                    "subtitle_text": "예상치 못한 재회"
                },
                {
                    "scene_order": 2,
                    "dialogue": "그러게, 여기서 다시 볼 줄은 몰랐어.",
                    "subtitle_text": "어색한 공기"
                },
                {
                    "scene_order": 3,
                    "dialogue": "이번엔 그냥 지나치지 말자.",
                    "subtitle_text": "다시 시작될까"
                }
            ]
        }
    }


@router.post("/images", response_model=ImageGenerateResponse)
def generate_images(request: ImageGenerateRequest):
    return {
        "success": True,
        "message": "3컷 이미지 생성 성공",
        "data": {
            "job_id": request.job_id,
            "images": [
                {
                    "scene_order": 1,
                    "image_url": "https://example.com/image1.png"
                },
                {
                    "scene_order": 2,
                    "image_url": "https://example.com/image2.png"
                },
                {
                    "scene_order": 3,
                    "image_url": "https://example.com/image3.png"
                }
            ]
        }
    }