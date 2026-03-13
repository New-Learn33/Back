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
#         "message": "6컷 생성 성공",
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
#         "message": "6컷 생성 성공",
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
import json
import asyncio
import replicate
from app.models.video import Video
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List

from app.schemas.generation_schema import GenerationRequest, GenerationResponse
from app.schemas.generation_schema import RenderSubtitleRequest, RenderVideoRequest
from app.schemas.generation_schema import ThumbnailSelectRequest
from app.services.script_service import generate_three_cut_script
from app.services.image_service import generate_three_cut_images, save_b64_image_to_file, build_image_prompt
from app.data.character_profiles_loader import pick_random_character
from app.services.subtitle_render_service import render_subtitle_image
from app.services.video_render_service import create_video_from_images
from app.utils.error_response import error_response
from app.utils.success_response import success_response
from sqlalchemy.orm import Session
from app.db.database import get_db, SessionLocal
from app.models.generation_job import GenerationJob
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

from app.services.r2_service import upload_local_file_to_r2

load_dotenv(override=True)


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
        "message": "6컷 생성 성공",
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


# 영상 다운로드 API
@router.get("/jobs/{job_id}/download")
def get_video_download(job_id: int, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()

    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    if job.status != "completed":
        return error_response(
            400,
            "REQUEST_001",
            "아직 영상 생성이 완료되지 않았습니다."
        )

    return success_response(
        {
            "job_id": job.id,
            "download_url": job.video_url
        },
        "다운로드 URL 조회 성공"
    )


# ──────────────────────────────────────
# SSE 스트리밍 엔드포인트
# ──────────────────────────────────────
@router.post("/stream")
async def generate_content_stream(request: Request):
    body = await request.json()
    category_id = body.get("category_id")
    prompt_text = body.get("prompt", "")

    from openai import OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def event(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    def generate():
        db = SessionLocal()
        try:
            # 1) 캐릭터 선택
            yield event({"type": "step", "step": "character", "message": "캐릭터를 선택하는 중..."})

            selected_character = pick_random_character(category_id)
            if not selected_character:
                yield event({"type": "error", "message": "유효하지 않은 카테고리입니다."})
                return

            # 2) 대사 생성
            yield event({"type": "step", "step": "script", "message": "대사를 생성하는 중..."})

            from app.schemas.generation_schema import GenerationRequest as GenReq
            req_obj = GenReq(category_id=category_id, prompt=prompt_text)
            script_result = generate_three_cut_script(req_obj)

            yield event({
                "type": "script",
                "title": script_result["title"],
                "scenes": script_result["scenes"],
            })

            # 3) DB에 job 생성
            job = GenerationJob(
                user_id=1,
                title=script_result["title"],
                prompt=prompt_text,
                category_id=category_id,
                status="pending",
                progress=0,
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            job_id = job.id

            yield event({"type": "step", "step": "image", "message": "이미지를 생성하는 중... (1/6)"})

            # 4) 이미지 한 장씩 생성하며 스트리밍
            uploaded_images = []
            for i, scene in enumerate(script_result["scenes"]):
                yield event({"type": "step", "step": "image", "message": f"이미지를 생성하는 중... ({i+1}/6)"})

                img_prompt = build_image_prompt(selected_character, scene)

                response = openai_client.images.generate(
                    model="gpt-image-1",
                    prompt=img_prompt,
                    size="1024x1024",
                    quality="medium",
                )

                if not response.data or not response.data[0].b64_json:
                    yield event({"type": "error", "message": f"이미지 {i+1} 생성 실패"})
                    return

                filename = f"{job_id}_{scene['scene_order']}.png"
                local_url = save_b64_image_to_file(response.data[0].b64_json, filename)

                # R2 업로드
                local_path = os.path.join("app", local_url.lstrip("/"))
                uploaded = upload_local_file_to_r2(
                    local_file_path=local_path,
                    folder="generated",
                    filename=filename,
                    content_type="image/png",
                )

                uploaded_images.append({
                    "scene_order": scene["scene_order"],
                    "image_url": uploaded["url"],
                })

                yield event({
                    "type": "image",
                    "scene_order": scene["scene_order"],
                    "image_url": uploaded["url"],
                })

            # 5) 완료
            job.status = "processing"
            job.progress = 30
            db.commit()

            yield event({
                "type": "done",
                "job_id": job_id,
                "title": script_result["title"],
                "category_id": category_id,
                "selected_template_image": {
                    "id": selected_character["id"],
                    "name": selected_character["name"],
                    "image_url": selected_character["image_url"],
                },
                "scenes": script_result["scenes"],
                "images": uploaded_images,
            })

        except Exception as e:
            yield event({"type": "error", "message": str(e)})
        finally:
            db.close()

    return StreamingResponse(generate(), media_type="text/event-stream")


# ──────────────────────────────────────
# SVD 기반 영상 생성 엔드포인트
# ──────────────────────────────────────
class SvdImageItem(BaseModel):
    scene_order: int
    image_url: str

class SvdSceneItem(BaseModel):
    scene_order: int
    dialogue: str

class SvdRenderRequest(BaseModel):
    job_id: int
    images: List[SvdImageItem]
    scenes: List[SvdSceneItem]


@router.post("/render/video/svd")
def render_video_svd(request: SvdRenderRequest, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == request.job_id).first()
    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    try:
        job.status = "processing"
        job.progress = 50
        db.commit()

        replicate_api_token = os.getenv("REPLICATE_API_TOKEN")
        if not replicate_api_token:
            return error_response(500, "SERVER_001", "REPLICATE_API_TOKEN이 설정되지 않았습니다.")

        os.environ["REPLICATE_API_TOKEN"] = replicate_api_token

        # 첫 번째 이미지로 SVD 영상 생성
        sorted_images = sorted(request.images, key=lambda x: x.scene_order)
        first_image_url = sorted_images[0].image_url

        # Replicate SVD 모델 실행
        output = replicate.run(
            "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
            input={
                "input_image": first_image_url,
                "video_length": "25_frames_with_svd_xt",
                "sizing_strategy": "maintain_aspect_ratio",
                "frames_per_second": 6,
                "motion_bucket_id": 127,
                "cond_aug": 0.02,
                "decoding_t": 7,
                "seed": 0,
            },
        )

        # output은 FileOutput URL
        video_url = str(output)

        job.video_url = video_url
        job.status = "completed"
        job.progress = 100

        # Video 레코드 생성/업데이트
        existing_video = db.query(Video).filter(Video.job_id == job.id).first()
        if existing_video:
            existing_video.video_url = video_url
        else:
            new_video = Video(
                job_id=job.id,
                user_id=job.user_id,
                category_id=job.category_id,
                title=job.title,
                prompt=job.prompt,
                thumbnail_url=job.thumbnail_url,
                video_url=video_url,
            )
            db.add(new_video)

        db.commit()

        return success_response(
            {
                "job_id": request.job_id,
                "status": "completed",
                "video_url": video_url,
            },
            "SVD 영상 생성 성공",
        )

    except Exception as e:
        job.status = "failed"
        job.progress = 0
        db.commit()
        return error_response(500, "SERVER_001", f"SVD 영상 생성 실패: {str(e)}")