import os
import base64
from uuid import uuid4
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import HTTPException

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
GENERATED_DIR = os.path.join(STATIC_DIR, "generated")

os.makedirs(GENERATED_DIR, exist_ok=True)


def build_image_prompt(category_hint: str, character_name: str, scene_order: int, dialogue: str, subtitle_text: str) -> str:
    return (
        f"{category_hint}, same character consistency, "
        f"main character: {character_name}, "
        f"webtoon style, scene {scene_order}, "
        f"{subtitle_text}, emotion based on dialogue: {dialogue}"
    )


def save_b64_image_to_file(b64_data: str, filename: str) -> str:
    file_path = os.path.join(GENERATED_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(base64.b64decode(b64_data))

    return f"/static/generated/{filename}"


def generate_three_cut_images(job_id: int, template_info: dict, scenes: list):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY가 설정되지 않았습니다.")

    results = []

    for scene in scenes:
        prompt = build_image_prompt(
            category_hint=template_info["category_hint"],
            character_name=template_info["character_name"],
            scene_order=scene["scene_order"],
            dialogue=scene["dialogue"],
            subtitle_text=scene["subtitle_text"],
        )

        try:
            response = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1024",
                quality="medium",
            )

            if not response.data or not response.data[0].b64_json:
                raise HTTPException(status_code=500, detail="이미지 생성 응답이 비어 있습니다.")

            filename = f"{job_id}_{scene['scene_order']}_{uuid4().hex}.png"
            image_url = save_b64_image_to_file(response.data[0].b64_json, filename)

            results.append(
                {
                    "scene_order": scene["scene_order"],
                    "image_url": image_url,
                    "prompt_used": prompt,
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"이미지 생성 실패: {str(e)}")

    return results