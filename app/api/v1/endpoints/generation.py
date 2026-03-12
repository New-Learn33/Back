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




# # 테스트용
# import random, os
# from app.models.video import Video
# from fastapi import APIRouter, Depends

# from app.schemas.generation_schema import GenerationRequest, GenerationResponse
# from app.schemas.generation_schema import RenderSubtitleRequest, RenderVideoRequest
# from app.schemas.generation_schema import ThumbnailSelectRequest
# from app.services.script_service import generate_three_cut_script
# from app.services.image_service import generate_three_cut_images
# from app.services.subtitle_render_service import render_subtitle_image
# from app.services.video_render_service import create_video_from_images
# from app.utils.error_response import error_response
# from app.utils.success_response import success_response
# from sqlalchemy.orm import Session
# from app.db.database import get_db
# from app.models.generation_job import GenerationJob

# router = APIRouter()

# CATEGORY_TEMPLATE_MAP = {
#     1: [
#         {
#             "id": 101,
#             "name": "테스트 애니 캐릭터",
#             "image_url": "/static/templates/test_character.png",
#             "category_hint": "anime style",
#             "character_name": "test_anime_character",
#         }
#     ],
#     2: [
#         {
#             "id": 201,
#             "name": "테스트 히어로 캐릭터",
#             "image_url": "/static/templates/test_character.png",
#             "category_hint": "superhero style",
#             "character_name": "test_hero_character",
#         }
#     ],
#     3: [
#         {
#             "id": 301,
#             "name": "테스트 게임 캐릭터",
#             "image_url": "/static/templates/test_character.png",
#             "category_hint": "game cinematic style",
#             "character_name": "test_game_character",
#         }
#     ],
#     4: [
#         {
#             "id": 401,
#             "name": "테스트 판타지 캐릭터",
#             "image_url": "/static/templates/test_character.png",
#             "category_hint": "fantasy epic style",
#             "character_name": "test_fantasy_character",
#         }
#     ],
# }


# @router.post("", response_model=GenerationResponse)
# def generate_content(request: GenerationRequest, db: Session = Depends(get_db)):
#     template_candidates = CATEGORY_TEMPLATE_MAP.get(request.category_id)

#     if not template_candidates:
#         return error_response(400, "REQUEST_001", "유효하지 않은 category_id 입니다.")
    
#     selected_template = random.choice(template_candidates)

#     script_result = generate_three_cut_script(request)

#     job = GenerationJob(
#         user_id=1,  # 테스트용, 나중에 현재 로그인 유저 id로 교체
#         title=script_result["title"],
#         prompt=request.prompt,
#         category_id=request.category_id,
#         status="pending",
#         progress=0
#     )
#     db.add(job)
#     db.commit()
#     db.refresh(job)

#     job_id = job.id

#     image_results = generate_three_cut_images(
#         job_id=job_id,
#         template_info=selected_template,
#         scenes=script_result["scenes"],
#     )

#     job.status = "processing"
#     job.progress = 30
#     db.commit()

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

import os
from app.models.video import Video
from fastapi import APIRouter, Depends, HTTPException

from app.schemas.generation_schema import GenerationRequest, GenerationResponse
from app.schemas.generation_schema import RenderSubtitleRequest, RenderVideoRequest
from app.schemas.generation_schema import ThumbnailSelectRequest
from app.services.script_service import generate_three_cut_script
from app.services.image_service import generate_three_cut_images
from app.data.character_profiles_loader import pick_random_character
from app.services.subtitle_render_service import render_subtitle_image
from app.services.video_render_service import create_video_from_images
from app.utils.error_response import error_response
from app.utils.success_response import success_response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.generation_job import GenerationJob

from app.services.r2_service import upload_local_file_to_r2


# 네가 이미 쓰고 있는 모델이 있으면 유지
# from app.models.generation_job import GenerationJob

router = APIRouter()

# 로컬 작업 경로용 함수
def local_url_to_file_path(url: str):
    clean = url.lstrip("/")
    return os.path.join("app", clean)

def generated_image_local_path(job_id: int, scene_order: int):
    return f"app/static/generated/{job_id}_{scene_order}.png"

def rendered_image_local_path(job_id: int, scene_order: int):
    return f"app/static/rendered/{job_id}_{scene_order}.png"

def video_local_path(job_id: int):
    return f"app/static/videos/{job_id}.mp4"


@router.post("", response_model=GenerationResponse)
def generate_content(request: GenerationRequest, db: Session = Depends(get_db)):
    selected_character = pick_random_character(request.category_id)

    if not selected_character:
        raise HTTPException(
            status_code=400,
            detail="유효하지 않은 category_id 이거나 해당 카테고리에 캐릭터가 없습니다."
        )

    script_result = generate_three_cut_script(request)

    job = GenerationJob(
        user_id=1,  # 테스트용
        title=script_result["title"],
        prompt=request.prompt,
        category_id=request.category_id,
        status="pending",
        progress=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    job_id = job.id

    # DB 저장 안 쓰면 임시 job_id
    # job_id = random.randint(100000, 999999)

    image_results = generate_three_cut_images(
        job_id=job_id,
        character_profile=selected_character,
        scenes=script_result["scenes"],
    )

    uploaded_images = []

    for img in image_results:
        scene_order = img["scene_order"]
        local_path = local_url_to_file_path(img["image_url"])

        uploaded = upload_local_file_to_r2(
            local_file_path=local_path,
            folder="generated",
            filename=f"{job_id}_{scene_order}.png",
            content_type="image/png"
        )

        uploaded_images.append({
            "scene_order": scene_order,
            "image_url": uploaded["url"],
        })

    job.status = "processing"
    job.progress = 30
    db.commit()

    return {
        "success": True,
        "message": "3컷 생성 성공",
        "data": {
            "job_id": job_id,
            "title": script_result["title"],
            "category_id": request.category_id,
            "selected_template_image": {
                "id": selected_character["id"],
                "name": selected_character["name"],
                "image_url": selected_character["image_url"],
            },
            "scenes": script_result["scenes"],
            "images": uploaded_images
        },
    }


# 자막 합성 API
@router.post("/render/subtitles")
def render_subtitles(request: RenderSubtitleRequest, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == request.job_id).first()
    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    try:
        scene_map = {scene.scene_order: scene for scene in request.scenes}
        results = []

        for img in request.images:
            scene = scene_map.get(img.scene_order)

            if not scene:
                return error_response(400, "REQUEST_001", "scene 정보가 없습니다.")

            input_path = generated_image_local_path(request.job_id, img.scene_order)
            output_path = rendered_image_local_path(request.job_id, img.scene_order)

            render_subtitle_image(
                input_path,
                output_path,
                scene.dialogue
            )

            uploaded = upload_local_file_to_r2(
                local_file_path=output_path,
                folder="rendered",
                filename=f"{request.job_id}_{img.scene_order}.png",
                content_type="image/png"
            )

            results.append({
                "scene_order": img.scene_order,
                "image_url": uploaded["url"]
            })

        job.status = "processing"
        job.progress = 60
        db.commit()

        return success_response(
            {
                "job_id": request.job_id,
                "subtitle_images": results
            },
            "자막 생성 성공"
        )

    except FileNotFoundError:
        job.status = "failed"
        db.commit()
        return error_response(404, "REQUEST_007", "이미지를 찾을 수 없습니다.")

    except Exception as e:
        job.status = "failed"
        db.commit()
        return error_response(500, "SERVER_001", str(e))
    

# 영상 생성 API
@router.post("/render/video")
def render_video(request: RenderVideoRequest, db: Session = Depends(get_db)):

    job = db.query(GenerationJob).filter(GenerationJob.id == request.job_id).first()
    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    try:
        job.status = "processing"
        job.progress = 80
        db.commit()

        sorted_images = sorted(request.subtitle_images, key=lambda x: x.scene_order)
        image_paths = [
            rendered_image_local_path(request.job_id, img.scene_order)
            for img in sorted_images
        ]

        output_path = video_local_path(request.job_id)

        create_video_from_images(image_paths, output_path)

        uploaded_video = upload_local_file_to_r2(
            local_file_path=output_path,
            folder="videos",
            filename=f"{request.job_id}.mp4",
            content_type="video/mp4"
        )

        video_url = uploaded_video["url"]

        job.video_url = video_url

        job.status = "completed"
        job.progress = 100

        existing_video = db.query(Video).filter(Video.job_id == job.id).first()

        if existing_video:
            existing_video.user_id = job.user_id
            existing_video.category_id = job.category_id
            existing_video.title = job.title
            existing_video.prompt = job.prompt
            existing_video.thumbnail_url = job.thumbnail_url
            existing_video.video_url = video_url
        else:
            new_video = Video(
                job_id=job.id,
                user_id=job.user_id,
                category_id=job.category_id,
                title=job.title,
                prompt=job.prompt,
                thumbnail_url=job.thumbnail_url,
                video_url=video_url
            )
            db.add(new_video)

        db.commit()

        return success_response(
            {
                "job_id": request.job_id,
                "status": job.status,
                "video_url": job.video_url
            },
            "영상 생성 성공"
        )

    except Exception as e:
        job.status = "failed"
        job.progress = 0
        db.commit()
        return error_response(500, "SERVER_001", str(e))
    

# 썸네일 선택 (사진 중에 선택) API
@router.post("/thumbnail/select")
def select_thumbnail(request: ThumbnailSelectRequest, db: Session = Depends(get_db)):
    try:

        job = db.query(GenerationJob).filter(GenerationJob.id == request.job_id).first()
        if not job:
            return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

        job.thumbnail_url = request.thumbnail_url

        video = db.query(Video).filter(Video.job_id == request.job_id).first()
        if video:
            video.thumbnail_url = request.thumbnail_url

        db.commit()

        return success_response(
            {
                "job_id": request.job_id,
                "thumbnail_url": request.thumbnail_url
            },
            "대표 이미지 선택 성공"
        )

    except Exception:
        return error_response(500, "SERVER_001", "대표 이미지 선택 중 오류가 발생했습니다.")


# 영상 생성 상태 조회 API
@router.get("/jobs/{job_id}")
def get_generation_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()

    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    return success_response(
        {
            "job_id": job.id,
            "status": job.status,
            "progress": job.progress
        },
        "영상 생성 상태 조회에 성공했습니다."
    )


# 영상 생성 결과 조회 API
@router.get("/jobs/{job_id}/result")
def get_generation_result(job_id: int, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()

    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    # 아직 생성 중이면 막음
    if job.status != "completed":
        return error_response(
            400,
            "REQUEST_001",
            "아직 영상 생성이 완료되지 않았습니다."
        )

    return success_response(
        {
            "job_id": job.id,
            "status": job.status,
            "video_url": job.video_url
        },
        "영상 정보 조회에 성공했습니다."
    )