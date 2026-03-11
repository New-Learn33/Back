# 기본 파일, 테스트를 위해 주석 처리해둠
# 아래에 테스트용 코드 있음

# import random
# from fastapi import APIRouter, HTTPException

# from app.schemas.generation_schema import GenerationRequest, GenerationResponse
# from app.services.script_service import generate_three_cut_script
# from app.services.image_service import generate_three_cut_images

# router = APIRouter()

# CATEGORY_TEMPLATE_MAP = {
#     1: [
#         {
#             "id": 101,
#             "name": "애니 캐릭터 1",
#             "image_url": "https://example.com/anime1.png",
#             "category_hint": "anime style",
#             "character_name": "anime_hero_1",
#         },
#         {
#             "id": 102,
#             "name": "애니 캐릭터 2",
#             "image_url": "https://example.com/anime2.png",
#             "category_hint": "anime style",
#             "character_name": "anime_hero_2",
#         },
#     ],
#     2: [
#         {
#             "id": 201,
#             "name": "히어로 캐릭터 1",
#             "image_url": "https://example.com/hero1.png",
#             "category_hint": "superhero style",
#             "character_name": "hero_main_1",
#         },
#         {
#             "id": 202,
#             "name": "히어로 캐릭터 2",
#             "image_url": "https://example.com/hero2.png",
#             "category_hint": "superhero style",
#             "character_name": "hero_main_2",
#         },
#     ],
#     3: [
#         {
#             "id": 301,
#             "name": "게임 캐릭터 1",
#             "image_url": "https://example.com/game1.png",
#             "category_hint": "game cinematic style",
#             "character_name": "game_character_1",
#         },
#         {
#             "id": 302,
#             "name": "게임 캐릭터 2",
#             "image_url": "https://example.com/game2.png",
#             "category_hint": "game cinematic style",
#             "character_name": "game_character_2",
#         },
#     ],
#     4: [
#         {
#             "id": 401,
#             "name": "판타지 캐릭터 1",
#             "image_url": "https://example.com/fantasy1.png",
#             "category_hint": "fantasy epic style",
#             "character_name": "fantasy_wizard_1",
#         },
#         {
#             "id": 402,
#             "name": "판타지 캐릭터 2",
#             "image_url": "https://example.com/fantasy2.png",
#             "category_hint": "fantasy epic style",
#             "character_name": "fantasy_knight_2",
#         },
#     ],
# }


# @router.post("", response_model=GenerationResponse)
# def generate_content(request: GenerationRequest):
#     template_candidates = CATEGORY_TEMPLATE_MAP.get(request.category_id)

#     if not template_candidates:
#         raise HTTPException(status_code=400, detail="유효하지 않은 category_id 입니다.")

#     selected_template = random.choice(template_candidates)

#     script_result = generate_three_cut_script(request)

#     # TODO: 나중에 generation_jobs insert 후 실제 DB id 사용
#     job_id = 1

#     image_results = generate_three_cut_images(
#         job_id=job_id,
#         template_info=selected_template,
#         scenes=script_result["scenes"],
#     )

#     return {
#         "success": True,
#         "message": "3컷 생성 성공",
#         "data": {
#             "job_id": job_id,
#             "title": script_result["title"],
#             "category_id": request.category_id,
#             "selected_template_image": {
#                 "id": selected_template["id"],
#                 "name": selected_template["name"],
#                 "image_url": selected_template["image_url"],
#             },
#             "scenes": script_result["scenes"],
#             "images": [
#                 {
#                     "scene_order": img["scene_order"],
#                     "image_url": img["image_url"],
#                 }
#                 for img in image_results
#             ],
#         },
#     }




# 테스트용
import random, os
from fastapi import APIRouter

from app.schemas.generation_schema import GenerationRequest, GenerationResponse
from app.services.script_service import generate_three_cut_script
from app.services.image_service import generate_three_cut_images
from app.schemas.generation_schema import RenderSubtitleRequest, RenderVideoRequest
from app.services.subtitle_render_service import render_subtitle_image
from app.services.video_render_service import create_video_from_images
from app.utils.error_response import error_response
from app.utils.success_response import success_response

router = APIRouter()

CATEGORY_TEMPLATE_MAP = {
    1: [
        {
            "id": 101,
            "name": "테스트 애니 캐릭터",
            "image_url": "/static/templates/test_character.png",
            "category_hint": "anime style",
            "character_name": "test_anime_character",
        }
    ],
    2: [
        {
            "id": 201,
            "name": "테스트 히어로 캐릭터",
            "image_url": "/static/templates/test_character.png",
            "category_hint": "superhero style",
            "character_name": "test_hero_character",
        }
    ],
    3: [
        {
            "id": 301,
            "name": "테스트 게임 캐릭터",
            "image_url": "/static/templates/test_character.png",
            "category_hint": "game cinematic style",
            "character_name": "test_game_character",
        }
    ],
    4: [
        {
            "id": 401,
            "name": "테스트 판타지 캐릭터",
            "image_url": "/static/templates/test_character.png",
            "category_hint": "fantasy epic style",
            "character_name": "test_fantasy_character",
        }
    ],
}


@router.post("", response_model=GenerationResponse)
def generate_content(request: GenerationRequest):
    template_candidates = CATEGORY_TEMPLATE_MAP.get(request.category_id)

    if not template_candidates:
        return error_response(400, "REQUEST_001", "유효하지 않은 category_id 입니다.")
    
    selected_template = random.choice(template_candidates)

    script_result = generate_three_cut_script(request)

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


def url_to_file_path(url: str):
    clean = url.lstrip("/")
    return os.path.join("app", clean)


# 자막 합성 API
@router.post("/render/subtitles")
def render_subtitles(request: RenderSubtitleRequest):

    try:
        scene_map = {scene.scene_order: scene for scene in request.scenes}
        results = []

        for img in request.images:

            # 현재 이미지와 같은 scene_order의 대사 찾기
            scene = scene_map.get(img.scene_order)

            if not scene:
                return error_response(400, "REQUEST_001", "scene 정보가 없습니다.")

            # URL을 실제 파일 경로로 바꿔줌
            input_path = url_to_file_path(img.image_url)
            output_path = f"app/static/rendered/{request.job_id}_{img.scene_order}.png"

            # 실제 자막 합성 실행
            render_subtitle_image(
                input_path,
                output_path,
                scene.dialogue
            )

            results.append({
                "scene_order": img.scene_order,
                "image_url": f"/static/rendered/{request.job_id}_{img.scene_order}.png"
            })

        return success_response(
            {
                "job_id": request.job_id,
                "subtitle_images": results
            },
            "자막 생성 성공"
        )

    except FileNotFoundError:
        return error_response(404, "REQUEST_007", "이미지를 찾을 수 없습니다.")

    except Exception as e:
        return error_response(500, "SERVER_001", str(e))
    

# 영상 생성 API
@router.post("/render/video")
def render_video(request: RenderVideoRequest):

    try:

        # 컷 순서대로 정렬
        sorted_images = sorted(request.subtitle_images, key=lambda x: x.scene_order)

        image_paths = [url_to_file_path(i.image_url) for i in sorted_images]

        output_path = f"app/static/videos/{request.job_id}.mp4"

        # ffmpeg 실행
        create_video_from_images(image_paths, output_path)

        return success_response(
            {
                "job_id": request.job_id,
                "video_url": f"/static/videos/{request.job_id}.mp4"
            },
            "영상 생성 성공"
        )

    except Exception as e:
        return error_response(500, "SERVER_001", str(e))
