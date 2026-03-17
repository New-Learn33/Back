import asyncio
import os
import random as _random

from app.db.database import SessionLocal
from app.models.generation_job import GenerationJob
from app.models.video import Video
from app.services.notification_service import create_notification, push_notification_to_user
from app.services.r2_service import upload_local_file_to_r2, add_storage_used
from app.services.websocket_manager import notification_ws_manager


def generated_image_local_path(job_id: int, scene_order: int):
    return f"app/static/generated/{job_id}_{scene_order}.png"


def video_clip_local_path(job_id: int, scene_order: int):
    return f"app/static/video_clips/{job_id}_{scene_order}.mp4"


def subtitle_clip_local_path(job_id: int, scene_order: int):
    return f"app/static/subtitle_clips/{job_id}_{scene_order}.mp4"


def final_video_local_path(job_id: int):
    return f"app/static/videos/{job_id}_svd.mp4"


def run_svd_video_generation_background(
    *,
    job_id: int,
    current_user_id: int,
    images: list,
    scenes: list,
    motion_intensity: str,
):
    from app.services.svd_service import generate_video_from_image
    from app.services.video_subtitle_service import burn_subtitle_to_video
    from app.services.video_concat_service import concat_video_clips

    db = SessionLocal()

    try:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            return

        job.status = "processing"
        job.progress = 50
        db.commit()

        asyncio.run(
            notification_ws_manager.send_to_user(
                current_user_id,
                {
                    "type": "job",
                    "event": "progress",
                    "job_id": job_id,
                    "status": job.status,
                    "progress": job.progress,
                },
            )
        )

        scene_map = {scene["scene_order"]: scene for scene in scenes}
        subtitle_clip_paths = []

        for img in sorted(images, key=lambda x: x["scene_order"]):
            scene_order = img["scene_order"]
            image_url = img["image_url"]
            scene = scene_map.get(scene_order)

            if not scene:
                raise ValueError(f"{scene_order}번 scene 정보가 없습니다.")
            if not image_url:
                raise ValueError(f"{scene_order}번 image_url이 없습니다.")

            clip_path = video_clip_local_path(job_id, scene_order)
            image_path = generated_image_local_path(job_id, scene_order)

            if not os.path.exists(image_path) and image_url.startswith("http"):
                import requests as req
                os.makedirs(os.path.dirname(image_path), exist_ok=True)
                dl = req.get(image_url)
                dl.raise_for_status()
                with open(image_path, "wb") as f:
                    f.write(dl.content)

            generate_video_from_image(
                image_path=image_path,
                output_path=clip_path,
                motion_intensity=motion_intensity,
            )

            subtitle_clip_path = subtitle_clip_local_path(job_id, scene_order)
            burn_subtitle_to_video(
                input_path=clip_path,
                output_path=subtitle_clip_path,
                subtitle=scene["dialogue"]
            )

            subtitle_clip_paths.append(subtitle_clip_path)

        job.progress = 85
        db.commit()

        asyncio.run(
            notification_ws_manager.send_to_user(
                current_user_id,
                {
                    "type": "job",
                    "event": "progress",
                    "job_id": job_id,
                    "status": job.status,
                    "progress": job.progress,
                },
            )
        )

        output_path = final_video_local_path(job_id)
        concat_video_clips(subtitle_clip_paths, output_path)

        uploaded_video = upload_local_file_to_r2(
            local_file_path=output_path,
            folder="videos",
            filename=f"{job_id}_svd.mp4",
            content_type="video/mp4"
        )
        add_storage_used(db, current_user_id, uploaded_video.get("size", 0))

        job.video_url = uploaded_video["url"]

        if not job.thumbnail_url and images:
            random_img = _random.choice(images)
            job.thumbnail_url = random_img["image_url"]

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

        notification = create_notification(
            db,
            recipient_user_id=current_user_id,
            actor_user_id=None,
            type="video_completed",
            title="영상 생성 완료",
            message="요청하신 영상 생성이 완료되었습니다.",
            job_id=job.id,
            video_id=existing_video.id if existing_video else None,
        )

        asyncio.run(push_notification_to_user(db, current_user_id, notification))

        asyncio.run(
            notification_ws_manager.send_to_user(
                current_user_id,
                {
                    "type": "job",
                    "event": "completed",
                    "job_id": job.id,
                    "status": job.status,
                    "progress": job.progress,
                    "video_url": job.video_url,
                },
            )
        )

    except Exception as e:
        try:
            job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.progress = 0
                db.commit()

            notification = create_notification(
                db,
                recipient_user_id=current_user_id,
                actor_user_id=None,
                type="video_failed",
                title="영상 생성 실패",
                message=f"영상 생성 중 오류가 발생했습니다: {str(e)}",
                job_id=job_id,
            )
            asyncio.run(push_notification_to_user(db, current_user_id, notification))

            asyncio.run(
                notification_ws_manager.send_to_user(
                    current_user_id,
                    {
                        "type": "job",
                        "event": "failed",
                        "job_id": job_id,
                        "status": "failed",
                        "progress": 0,
                        "message": str(e),
                    },
                )
            )
        except Exception:
            pass
    finally:
        db.close()