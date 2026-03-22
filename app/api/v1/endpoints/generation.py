import os
import json
import random as _random
import threading
from app.services.background_video_generation_service import run_svd_video_generation_background
from app.models.video import Video
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.generation_schema import GenerationRequest, GenerationResponse
from app.schemas.generation_schema import RenderSubtitleRequest, RenderVideoRequest
from app.schemas.generation_schema import ThumbnailSelectRequest

# from app.services.script_service import generate_three_cut_script
# from app.services.image_service import generate_three_cut_images
from app.services.image_service import generate_single_image
from app.services.script_service import generate_six_cut_script
from app.services.image_service import generate_six_cut_images
from app.services.subtitle_render_service import render_subtitle_image
from app.services.video_render_service import create_video_from_images

from app.data.character_profiles_loader import pick_random_character
from app.utils.error_response import error_response
from app.utils.success_response import success_response
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.generation_job import GenerationJob

from app.services.r2_service import upload_local_file_to_r2, add_storage_used
from app.schemas.generation_schema import StabilityRenderVideoRequest

from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from fastapi.responses import JSONResponse

from app.schemas.generation_schema import GenerationTextUpdateRequest
from app.models.generation_scene import GenerationScene
from app.services.asset_library_service import normalize_tags

from datetime import datetime, timedelta
from sqlalchemy import func as sqlfunc

DAILY_GENERATION_LIMIT = 5

router = APIRouter()


def _request_tags(request: GenerationRequest) -> list[str]:
    return normalize_tags(getattr(request, "tags", []) or [])


def _resolve_category_id(selected_character: dict | None, fallback: int | None) -> int:
    if selected_character:
        raw = selected_character.get("category_id")
        try:
            return int(raw)
        except (TypeError, ValueError):
            pass
    return fallback or 0


def check_daily_limit(db: Session, user_id: int):
    """오늘 생성한 영상 횟수가 제한을 초과했는지 확인"""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    count = db.query(sqlfunc.count(GenerationJob.id)).filter(
        GenerationJob.user_id == user_id,
        GenerationJob.created_at >= today_start,
    ).scalar()
    return count

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
def generate_content(
    request: GenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if isinstance(current_user, JSONResponse):
        return current_user

    # 일일 생성 횟수 제한 체크
    today_count = check_daily_limit(db, current_user.id)
    if today_count >= DAILY_GENERATION_LIMIT:
        return error_response(
            429, "LIMIT_001",
            f"하루 영상 생성 횟수({DAILY_GENERATION_LIMIT}회)를 초과했습니다. 내일 다시 시도해주세요."
        )

    request_tags = _request_tags(request)
    selected_character = pick_random_character(
        user_id=current_user.id,
        db=db,
        tags=request_tags,
        category_id=request.category_id,
    )
    resolved_category_id = _resolve_category_id(selected_character, request.category_id)
    # 에셋이 없으면 None → 프롬프트만으로 이미지 생성

    script_result = generate_six_cut_script(request, genre=request.genre)

    job = GenerationJob(
        user_id=current_user.id,
        title=script_result["title"],
        prompt=request.prompt,
        category_id=resolved_category_id,
        status="pending",
        progress=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    job_id = job.id

    # DB 저장 안 쓰면 임시 job_id
    # job_id = random.randint(100000, 999999)

    # scenes DB 저장
    for scene in script_result["scenes"]:
        db.add(
            GenerationScene(
                job_id=job_id,
                scene_order=scene["scene_order"],
                dialogue=scene.get("dialogue"),
                subtitle_text=scene.get("subtitle_text")
            )
        )
    db.commit()

    image_results = generate_six_cut_images(
        job_id=job_id,
        character_profile=selected_character,
        scenes=script_result["scenes"],
        art_style=request.art_style,
        image_quality=request.image_quality,
    )

    uploaded_images = []
    total_uploaded_size = 0

    for img in image_results:
        scene_order = img["scene_order"]
        local_path = local_url_to_file_path(img["image_url"])

        try:
            uploaded = upload_local_file_to_r2(
                local_file_path=local_path,
                folder="generated",
                filename=f"{job_id}_{scene_order}.png",
                content_type="image/png"
            )
            final_url = uploaded["url"]
            total_uploaded_size += uploaded.get("size", 0)
        except Exception as r2_err:
            pass  # R2 업로드 실패 시 로컬 URL 사용
            final_url = img["image_url"]

        uploaded_images.append({
            "scene_order": scene_order,
            "image_url": final_url,
        })

    # storage_used 업데이트
    if total_uploaded_size > 0:
        add_storage_used(db, current_user.id, total_uploaded_size)

    job.status = "processing"
    job.progress = 30
    db.commit()

    return {
        "success": True,
        "message": f"{len(script_result['scenes'])}컷 생성 성공",
        "data": {
            "job_id": job_id,
            "title": script_result["title"],
            "tags": request_tags,
            "category_id": resolved_category_id,
            "selected_template_image": {
                "id": selected_character["id"],
                "name": selected_character["name"],
                "image_url": selected_character["image_url"],
            } if selected_character else None,
            "scenes": script_result["scenes"],
            "images": uploaded_images
        },
    }


# SSE 스트리밍 생성 API - 이미지가 1장씩 생성될 때마다 프론트로 push
@router.post("/stream")
def generate_content_stream(
    request: GenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if isinstance(current_user, JSONResponse):
        return current_user

    # 일일 생성 횟수 제한 체크
    today_count = check_daily_limit(db, current_user.id)
    if today_count >= DAILY_GENERATION_LIMIT:
        return error_response(
            429, "LIMIT_001",
            f"하루 영상 생성 횟수({DAILY_GENERATION_LIMIT}회)를 초과했습니다. 내일 다시 시도해주세요."
        )

    # 제너레이터 밖에서 미리 값 추출 (제너레이터 안에서 request 접근 시 문제 방지)
    request_tags = _request_tags(request)
    category_id = request.category_id or 0
    prompt_text = request.prompt
    art_style = request.art_style
    genre = request.genre
    image_quality = request.image_quality

    selected_character = pick_random_character(
        user_id=current_user.id,
        db=db,
        tags=request_tags,
        category_id=request.category_id,
    )
    category_id = _resolve_category_id(selected_character, request.category_id)
    # 에셋이 없으면 None → 프롬프트만으로 이미지 생성

    # request 데이터를 단순 객체로 복사
    class SimpleRequest:
        def __init__(self, prompt, tags):
            self.prompt = prompt
            self.tags = tags

    req_copy = SimpleRequest(prompt_text, request_tags)

    def event_stream():
        try:
            # 1단계: 대사 생성
            yield f"data: {json.dumps({'type': 'step', 'step': 'script', 'message': 'AI가 대사를 생성하고 있습니다...'}, ensure_ascii=False)}\n\n"

            script_result = generate_six_cut_script(req_copy, genre=genre)

            # DB에 job 저장
            from app.db.database import SessionLocal
            db_session = SessionLocal()
            try:
                job = GenerationJob(
                    user_id=current_user.id,
                    title=script_result["title"],
                    prompt=prompt_text,
                    category_id=category_id,
                    status="pending",
                    progress=0
                )
                db_session.add(job)
                db_session.commit()
                db_session.refresh(job)
                job_id = job.id

                for scene in script_result["scenes"]:
                    db_session.add(
                        GenerationScene(
                            job_id=job_id,
                            scene_order=scene["scene_order"],
                            dialogue=scene.get("dialogue"),
                            subtitle_text=scene.get("subtitle_text")
                        )
                    )
                db_session.commit()

            except Exception:
                db_session.rollback()
                raise
            finally:
                db_session.close()

            # 대사 결과 전송
            yield f"data: {json.dumps({'type': 'script', 'job_id': job_id, 'title': script_result['title'], 'tags': request_tags, 'category_id': category_id, 'scenes': script_result['scenes']}, ensure_ascii=False)}\n\n"


            total_count = len(script_result["scenes"])

            # 2단계: 이미지 1장씩 생성하며 push
            uploaded_images = []
            stream_upload_size = 0
            for i, scene in enumerate(script_result["scenes"]):
                step_data = {
                    "type": "step",
                    "step": f"image_{i+1}",
                    "message": f"{i+1}번째 이미지를 생성하고 있습니다... ({i+1}/{total_count})",
                }
                yield f"data: {json.dumps(step_data, ensure_ascii=False)}\n\n"

                img_result = generate_single_image(
                    job_id=job_id,
                    character_profile=selected_character,
                    scene=scene,
                    art_style=art_style,
                    image_quality=image_quality,
                )

                # R2 업로드 (실패 시 로컬 URL 폴백)
                local_path = local_url_to_file_path(img_result["image_url"])
                try:
                    uploaded = upload_local_file_to_r2(
                        local_file_path=local_path,
                        folder="generated",
                        filename=f"{job_id}_{scene['scene_order']}.png",
                        content_type="image/png"
                    )
                    final_url = uploaded["url"]
                    stream_upload_size += uploaded.get("size", 0)
                except Exception as r2_err:
                    pass  # R2 업로드 실패 시 로컬 URL 사용
                    final_url = img_result["image_url"]

                image_data = {
                    "scene_order": scene["scene_order"],
                    "image_url": final_url,
                }
                uploaded_images.append(image_data)

                # 이미지 1장 완성 → 프론트에 즉시 push
                yield f"data: {json.dumps({'type': 'image', 'scene_order': scene['scene_order'], 'image_url': final_url}, ensure_ascii=False)}\n\n"

            # storage_used 업데이트
            if stream_upload_size > 0:
                try:
                    from app.db.database import SessionLocal as _SL
                    _db = _SL()
                    try:
                        from app.models.user import User as _U
                        _user = _db.query(_U).filter(_U.id == current_user.id).first()
                        if _user:
                            _user.storage_used = (_user.storage_used or 0) + stream_upload_size
                            _db.commit()
                    finally:
                        _db.close()
                except Exception:
                    pass

            # 그림 생성 완료 알림
            try:
                from app.db.database import SessionLocal as _SL2
                from app.services.notification_service import create_notification, push_notification_to_user
                import asyncio as _asyncio
                _db2 = _SL2()
                try:
                    _notif = create_notification(
                        _db2,
                        recipient_user_id=current_user.id,
                        actor_user_id=None,
                        type="image_completed",
                        title="이미지 생성 완료",
                        message=f"'{script_result['title']}' 이미지 6장 생성이 완료되었습니다.",
                        job_id=job_id,
                    )
                    _asyncio.run(push_notification_to_user(_db2, current_user.id, _notif))
                finally:
                    _db2.close()
            except Exception:
                pass

            # 완료
            template_image = {'id': selected_character['id'], 'name': selected_character['name'], 'image_url': selected_character['image_url']} if selected_character else None
            yield f"data: {json.dumps({'type': 'done', 'job_id': job_id, 'title': script_result['title'], 'tags': request_tags, 'category_id': category_id, 'selected_template_image': template_image, 'scenes': script_result['scenes'], 'images': uploaded_images}, ensure_ascii=False)}\n\n"

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# 자막 합성 API
@router.post("/render/subtitles")
def render_subtitles(
    request: RenderSubtitleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if isinstance(current_user, JSONResponse):
        return current_user

    job = db.query(GenerationJob).filter(GenerationJob.id == request.job_id).first()
    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    if job.user_id != current_user.id:
        return error_response(403, "REQUEST_006", "권한이 없는 유저의 접근입니다.")

    try:
        scene_map = {scene.scene_order: scene for scene in request.scenes}
        results = []
        render_total_size = 0

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

            try:
                uploaded = upload_local_file_to_r2(
                    local_file_path=output_path,
                    folder="rendered",
                    filename=f"{request.job_id}_{img.scene_order}.png",
                    content_type="image/png"
                )
                final_url = uploaded["url"]
                render_total_size += uploaded.get("size", 0)
            except Exception as r2_err:
                pass  # R2 업로드 실패 시 로컬 URL 사용
                final_url = f"/static/rendered/{request.job_id}_{img.scene_order}.png"

            results.append({
                "scene_order": img.scene_order,
                "image_url": final_url
            })

        if render_total_size > 0:
            add_storage_used(db, current_user.id, render_total_size)

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
def render_video(
    request: RenderVideoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if isinstance(current_user, JSONResponse):
        return current_user

    job = db.query(GenerationJob).filter(GenerationJob.id == request.job_id).first()
    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    if job.user_id != current_user.id:
        return error_response(403, "REQUEST_006", "권한이 없는 유저의 접근입니다.")

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

        try:
            uploaded_video = upload_local_file_to_r2(
                local_file_path=output_path,
                folder="videos",
                filename=f"{request.job_id}.mp4",
                content_type="video/mp4"
            )
            video_url = uploaded_video["url"]
            add_storage_used(db, current_user.id, uploaded_video.get("size", 0))
        except Exception as r2_err:
            pass  # R2 업로드 실패 시 로컬 URL 사용
            video_url = f"/static/videos/{request.job_id}.mp4"

        job.video_url = video_url

        # 썸네일이 없으면 자막 합성 이미지 중 랜덤으로 지정 (실제 URL 사용)
        if not job.thumbnail_url and request.subtitle_images:
            random_img = _random.choice(request.subtitle_images)
            job.thumbnail_url = random_img.image_url

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
def select_thumbnail(
    request: ThumbnailSelectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if isinstance(current_user, JSONResponse):
        return current_user

    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == request.job_id).first()
        if not job:
            return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

        if job.user_id != current_user.id:
            return error_response(403, "REQUEST_006", "권한이 없는 유저의 접근입니다.")

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
def get_generation_status(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if isinstance(current_user, JSONResponse):
        return current_user

    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()

    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    if job.user_id != current_user.id:
        return error_response(403, "REQUEST_006", "권한이 없는 유저의 접근입니다.")

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
def get_generation_result(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if isinstance(current_user, JSONResponse):
        return current_user

    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()

    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    if job.user_id != current_user.id:
        return error_response(403, "REQUEST_006", "권한이 없는 유저의 접근입니다.")

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
def get_video_download(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if isinstance(current_user, JSONResponse):
        return current_user

    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()

    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    if job.user_id != current_user.id:
        return error_response(403, "REQUEST_006", "권한이 없는 유저의 접근입니다.")

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


# SVD 생성 영상 로컬 저장 경로
def video_clip_local_path(job_id: int, scene_order: int):
    return f"app/static/video_clips/{job_id}_{scene_order}.mp4"

def subtitle_clip_local_path(job_id: int, scene_order: int):
    return f"app/static/subtitle_clips/{job_id}_{scene_order}.mp4"

def final_video_local_path(job_id: int):
    return f"app/static/videos/{job_id}_svd.mp4"

# SVD 영상 생성 API
@router.post("/render/video/svd")
def render_video_with_svd(
    request: StabilityRenderVideoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services.svd_service import generate_video_from_image
    from app.services.video_subtitle_service import burn_subtitle_to_video
    from app.services.video_concat_service import concat_video_clips

    if isinstance(current_user, JSONResponse):
        return current_user


    job = db.query(GenerationJob).filter(GenerationJob.id == request.job_id).first()
    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    if job.user_id != current_user.id:
        return error_response(403, "REQUEST_006", "권한이 없는 유저의 접근입니다.")

    try:
        job.status = "processing"
        job.progress = 50
        db.commit()

        scene_map = {scene.scene_order: scene for scene in request.scenes}
        subtitle_clip_paths = []

        for img in sorted(request.images, key=lambda x: x.scene_order):
            scene_order = img.scene_order
            scene = scene_map.get(scene_order)

            if not scene:
                return error_response(400, "REQUEST_001", f"{scene_order}번 scene 정보가 없습니다.")

            if not img.image_url:
                return error_response(400, "REQUEST_001", f"{scene_order}번 image_url이 없습니다.")

            # SVD 영상 생성
            clip_path = video_clip_local_path(request.job_id, scene_order)

            # 로컬 파일이 있으면 사용, 없으면 R2 URL에서 다운로드
            image_path = generated_image_local_path(request.job_id, scene_order)
            if not os.path.exists(image_path) and img.image_url.startswith("http"):
                import requests as req
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                dl = req.get(img.image_url)
                dl.raise_for_status()
                with open(image_path, "wb") as f:
                    f.write(dl.content)

            generate_video_from_image(
                image_path=image_path,
                output_path=clip_path,
                motion_intensity=request.motion_intensity,
            )

            # 자막 합성
            subtitle_clip_path = subtitle_clip_local_path(request.job_id, scene_order)
            burn_subtitle_to_video(
                input_path=clip_path,
                output_path=subtitle_clip_path,
                subtitle=scene.dialogue
            )

            subtitle_clip_paths.append(subtitle_clip_path)

        job.progress = 85
        db.commit()

        # 영상 이어붙이기
        output_path = final_video_local_path(request.job_id)
        concat_video_clips(subtitle_clip_paths, output_path)

        uploaded_video = upload_local_file_to_r2(
            local_file_path=output_path,
            folder="videos",
            filename=f"{request.job_id}_svd.mp4",
            content_type="video/mp4"
        )
        add_storage_used(db, current_user.id, uploaded_video.get("size", 0))

        job.video_url = uploaded_video["url"]

        # 썸네일이 없으면 생성된 이미지 중 랜덤으로 지정 (generated/ 폴더의 실제 URL 사용)
        if not job.thumbnail_url and request.images:
            random_img = _random.choice(request.images)
            if random_img.image_url:
                job.thumbnail_url = random_img.image_url
            else:
                r2_base = os.getenv("R2_PUBLIC_BASE_URL", "")
                if r2_base:
                    job.thumbnail_url = f"{r2_base}/generated/{request.job_id}_{random_img.scene_order}.png"
                else:
                    job.thumbnail_url = f"/static/generated/{request.job_id}_{random_img.scene_order}.png"

        job.status = "completed"
        job.progress = 100

        existing_video = db.query(Video).filter(Video.job_id == job.id).first()
        if existing_video:
            existing_video.user_id = job.user_id
            existing_video.category_id = job.category_id
            existing_video.title = job.title
            existing_video.prompt = job.prompt
            existing_video.thumbnail_url = job.thumbnail_url
            existing_video.video_url = job.video_url
        else:
            db.add(Video(
                job_id=job.id,
                user_id=job.user_id,
                category_id=job.category_id,
                title=job.title,
                prompt=job.prompt,
                thumbnail_url=job.thumbnail_url,
                video_url=job.video_url
            ))

        db.commit()

        return success_response(
            {
                "job_id": request.job_id,
                "status": job.status,
                "video_url": job.video_url
            },
            "SVD 기반 영상 생성 성공"
        )

    except Exception:
        job.status = "failed"
        job.progress = 0
        db.commit()
        return error_response(500, "SERVER_001", str(e))


# 수정 API
@router.patch("/jobs/{job_id}/text")
def update_generation_text(
    job_id: int,
    request: GenerationTextUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if isinstance(current_user, JSONResponse):
        return current_user

    if request.title is None and not request.scenes:
        return error_response(400, "REQUEST_001", "수정할 title 또는 scenes 값이 필요합니다.")

    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    if job.user_id != current_user.id:
        return error_response(403, "REQUEST_006", "권한이 없는 유저의 접근입니다.")

    try:
        # title 수정
        if request.title is not None:
            job.title = request.title

        # scenes 수정
        if request.scenes:
            for scene_req in request.scenes:
                scene = db.query(GenerationScene).filter(
                    GenerationScene.job_id == job_id,
                    GenerationScene.scene_order == scene_req.scene_order
                ).first()

                if not scene:
                    return error_response(
                        404,
                        "REQUEST_007",
                        f"{scene_req.scene_order}번 scene을 찾을 수 없습니다."
                    )

                if scene_req.dialogue is not None:
                    scene.dialogue = scene_req.dialogue

                if scene_req.subtitle_text is not None:
                    scene.subtitle_text = scene_req.subtitle_text

        db.commit()
        db.refresh(job)

        updated_scenes = db.query(GenerationScene).filter(
            GenerationScene.job_id == job_id
        ).order_by(GenerationScene.scene_order.asc()).all()

        return success_response(
            {
                "job_id": job.id,
                "title": job.title,
                "scenes": [
                    {
                        "scene_order": scene.scene_order,
                        "dialogue": scene.dialogue,
                        "subtitle_text": scene.subtitle_text
                    }
                    for scene in updated_scenes
                ]
            },
            "텍스트 수정 성공"
        )

    except Exception as e:
        db.rollback()
        return error_response(500, "SERVER_001", str(e))
    
# SVD 영상 생성 API (백그라운드 작업) - 프론트에서 영상 생성 요청 시 바로 응답하고, 실제 생성 작업은 백그라운드에서 처리
@router.post("/render/video/svd/background")
def render_video_with_svd_background(
    request: StabilityRenderVideoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if isinstance(current_user, JSONResponse):
        return current_user

    job = db.query(GenerationJob).filter(GenerationJob.id == request.job_id).first()
    if not job:
        return error_response(404, "REQUEST_007", "job을 찾을 수 없습니다.")

    if job.user_id != current_user.id:
        return error_response(403, "REQUEST_006", "권한이 없는 유저의 접근입니다.")

    try:
        job.status = "processing"
        if job.progress < 40:
            job.progress = 40
        db.commit()

        worker = threading.Thread(
            target=run_svd_video_generation_background,
            kwargs={
                "job_id": request.job_id,
                "current_user_id": current_user.id,
                "images": [img.model_dump() for img in request.images],
                "scenes": [scene.model_dump() for scene in request.scenes],
                "motion_intensity": request.motion_intensity,
            },
            daemon=True,
        )
        worker.start()

        return success_response(
            data={
                "job_id": request.job_id,
                "status": "processing",
                "progress": job.progress,
            },
            message="백그라운드 영상 생성 작업이 시작되었습니다.",
        )

    except Exception as e:
        db.rollback()
        return error_response(500, "SERVER_001", str(e))


# 오늘 남은 생성 횟수 조회 API
@router.get("/daily-limit")
def get_daily_limit(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if isinstance(current_user, JSONResponse):
        return current_user

    today_count = check_daily_limit(db, current_user.id)
    remaining = max(0, DAILY_GENERATION_LIMIT - today_count)

    return success_response(
        {
            "daily_limit": DAILY_GENERATION_LIMIT,
            "used_today": today_count,
            "remaining": remaining,
        },
        "일일 생성 횟수 조회 성공"
    )