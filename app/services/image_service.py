import os
import base64
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import HTTPException

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
GENERATED_DIR = os.path.join(STATIC_DIR, "generated")

os.makedirs(GENERATED_DIR, exist_ok=True)


def save_b64_image_to_file(b64_data: str, filename: str) -> str:
    file_path = os.path.join(GENERATED_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(base64.b64decode(b64_data))

    return f"/static/generated/{filename}"


def build_character_anchor(character_profile: dict) -> str:
    appearance = character_profile.get("appearance", {})
    outfit = character_profile.get("outfit", {})
    style_keywords = character_profile.get("style_keywords", [])
    forbidden_changes = character_profile.get("forbidden_changes", [])
    custom_tags = character_profile.get("custom_tags", [])

    accessories = ", ".join(outfit.get("accessories", []))
    style_text = ", ".join(style_keywords)
    forbidden_text = ", ".join(forbidden_changes)
    custom_tags_text = ", ".join(custom_tags) if custom_tags else ""

    gender = character_profile.get("gender", "ambiguous")
    hair = appearance.get("hair", "")
    eyes = appearance.get("eyes", "")

    top = outfit.get("top", "")
    bottom = outfit.get("bottom", "")
    shoes = outfit.get("shoes", "")

    anchor_prompt = f"""
Create a safe, non-explicit, fully clothed character illustration.

Fixed character identity:
- category style: {character_profile.get("category_hint", "")}
- gender presentation: {gender}
- hair: {hair}
- eyes: {eyes}
- outfit top: {top}
- outfit bottom: {bottom}
- shoes: {shoes}
- accessories: {accessories}
- style keywords: {style_text}
{f"- user-defined character traits: {custom_tags_text}" if custom_tags_text else ""}

Consistency rules:
- same exact character identity in all 6 scenes
- same hairstyle, same outfit, same outfit colors, same accessories
- keep the character fully clothed
- no sexualized pose
- no revealing clothes
- no body emphasis
- no nudity
- no suggestive content
- {forbidden_text}
"""
    return anchor_prompt.strip()


def build_image_prompt(character_profile: dict, scene: dict) -> str:
    character_anchor = build_character_anchor(character_profile)

    scene_prompt = f"""
Scene instructions:
- scene order: {scene["scene_order"]}
- scene situation: {scene["subtitle_text"]}
- emotional tone: {scene["dialogue"]}

Image style rules:
- webtoon style illustration
- cinematic composition
- character-focused scene
- no text
- no speech bubbles
- no captions
- no watermark
- no UI elements
- safe for general audience
"""

    return f"{character_anchor}\n\n{scene_prompt}".strip()


def generate_six_cut_images(job_id: int, character_profile: dict, scenes: list):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY가 설정되지 않았습니다.")

    results = []

    for scene in scenes:
        prompt = build_image_prompt(character_profile, scene)

        try:
            current_prompt = prompt
            for attempt in range(2):
                try:
                    response = client.images.generate(
                        model="gpt-image-1",
                        prompt=current_prompt,
                        size="1024x1024",
                        quality="medium",
                    )
                    break
                except Exception as e:
                    if ("moderation_blocked" in str(e) or "safety" in str(e).lower()) and attempt == 0:
                        current_prompt = f"""Create a safe, family-friendly cartoon illustration.
Scene: {scene.get('subtitle_text', 'A character in a simple scene')}
Style: Clean webtoon style, fully clothed character, no text, no speech bubbles, safe for all ages."""
                        continue
                    raise

            if not response.data or not response.data[0].b64_json:
                raise HTTPException(status_code=500, detail="이미지 생성 응답이 비어 있습니다.")

            filename = f"{job_id}_{scene['scene_order']}.png"
            image_url = save_b64_image_to_file(response.data[0].b64_json, filename)

            results.append(
                {
                    "scene_order": scene["scene_order"],
                    "image_url": image_url,
                    "prompt_used": current_prompt,
                }
            )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"이미지 생성 실패: {str(e)}")

    return results


def generate_single_image(job_id: int, character_profile: dict, scene: dict):
    """이미지 1장만 생성 (SSE 스트리밍용). 모더레이션 차단 시 안전한 프롬프트로 재시도."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OPENAI_API_KEY가 설정되지 않았습니다.")

    prompt = build_image_prompt(character_profile, scene)

    for attempt in range(2):
        try:
            response = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1024",
                quality="medium",
            )
            break
        except Exception as e:
            if "moderation_blocked" in str(e) or "safety" in str(e).lower():
                if attempt == 0:
                    # 안전한 프롬프트로 재시도
                    prompt = f"""Create a safe, family-friendly cartoon illustration.
Scene: {scene.get('subtitle_text', 'A character in a simple scene')}
Style: Clean webtoon style, fully clothed character, no text, no speech bubbles, safe for all ages."""
                    continue
                else:
                    raise Exception("이미지 생성이 안전 정책에 의해 차단되었습니다. 다른 프롬프트를 시도해주세요.")
            raise

    if not response.data or not response.data[0].b64_json:
        raise Exception("이미지 생성 응답이 비어 있습니다.")

    filename = f"{job_id}_{scene['scene_order']}.png"
    image_url = save_b64_image_to_file(response.data[0].b64_json, filename)

    return {
        "scene_order": scene["scene_order"],
        "image_url": image_url,
        "prompt_used": prompt,
    }