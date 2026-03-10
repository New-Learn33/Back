import random
from fastapi import APIRouter, HTTPException

from app.schemas.generation_schema import GenerationRequest, GenerationResponse
from app.services.script_service import generate_three_cut_script
from app.services.image_service import generate_three_cut_images

router = APIRouter()

CATEGORY_TEMPLATE_MAP = {
    1: [
        {
            "id": 101,
            "name": "애니 캐릭터 1",
            "image_url": "https://example.com/anime1.png",
            "category_hint": "anime style",
            "character_name": "anime_hero_1",
        },
        {
            "id": 102,
            "name": "애니 캐릭터 2",
            "image_url": "https://example.com/anime2.png",
            "category_hint": "anime style",
            "character_name": "anime_hero_2",
        },
    ],
    2: [
        {
            "id": 201,
            "name": "히어로 캐릭터 1",
            "image_url": "https://example.com/hero1.png",
            "category_hint": "superhero style",
            "character_name": "hero_main_1",
        },
        {
            "id": 202,
            "name": "히어로 캐릭터 2",
            "image_url": "https://example.com/hero2.png",
            "category_hint": "superhero style",
            "character_name": "hero_main_2",
        },
    ],
    3: [
        {
            "id": 301,
            "name": "게임 캐릭터 1",
            "image_url": "https://example.com/game1.png",
            "category_hint": "game cinematic style",
            "character_name": "game_character_1",
        },
        {
            "id": 302,
            "name": "게임 캐릭터 2",
            "image_url": "https://example.com/game2.png",
            "category_hint": "game cinematic style",
            "character_name": "game_character_2",
        },
    ],
    4: [
        {
            "id": 401,
            "name": "판타지 캐릭터 1",
            "image_url": "https://example.com/fantasy1.png",
            "category_hint": "fantasy epic style",
            "character_name": "fantasy_wizard_1",
        },
        {
            "id": 402,
            "name": "판타지 캐릭터 2",
            "image_url": "https://example.com/fantasy2.png",
            "category_hint": "fantasy epic style",
            "character_name": "fantasy_knight_2",
        },
    ],
}


@router.post("", response_model=GenerationResponse)
def generate_content(request: GenerationRequest):
    template_candidates = CATEGORY_TEMPLATE_MAP.get(request.category_id)

    if not template_candidates:
        raise HTTPException(status_code=400, detail="유효하지 않은 category_id 입니다.")

    selected_template = random.choice(template_candidates)

    script_result = generate_three_cut_script(request)

    # TODO: 나중에 generation_jobs insert 후 실제 DB id 사용
    job_id = 1

    image_results = generate_three_cut_images(
        job_id=job_id,
        template_info=selected_template,
        scenes=script_result["scenes"],
    )

    return {
        "success": True,
        "message": "3컷 생성 성공",
        "data": {
            "job_id": job_id,
            "title": script_result["title"],
            "category_id": request.category_id,
            "selected_template_image": {
                "id": selected_template["id"],
                "name": selected_template["name"],
                "image_url": selected_template["image_url"],
            },
            "scenes": script_result["scenes"],
            "images": [
                {
                    "scene_order": img["scene_order"],
                    "image_url": img["image_url"],
                }
                for img in image_results
            ],
        },
    }