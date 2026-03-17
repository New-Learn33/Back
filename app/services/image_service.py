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

ART_STYLE_MAP = {
    "webtoon": "webtoon style illustration, clean bold outlines, flat cel-shaded colors, professional manhwa quality",
    "anime": "japanese anime style, detailed shading, vibrant colors, studio-quality key visual, sharp line art",
    "watercolor": "watercolor painting style, soft edges, pastel tones, delicate brush strokes, artistic illustration",
    "3d_render": "3D rendered character, Pixar-like quality, detailed lighting, smooth surfaces, professional CGI",
    "pixel": "pixel art style, retro game aesthetic, 16-bit, clean pixel boundaries, consistent palette",
    "realistic": "photorealistic digital art, cinematic lighting, detailed textures, 8K quality, sharp focus",
}

# 품질 강화 프롬프트 (모든 이미지에 공통 적용)
QUALITY_PROMPT = """
Quality requirements (CRITICAL — always apply):
- single character, centered composition, clean background
- symmetrical face, well-proportioned features, consistent eye size and shape
- anatomically correct hands with exactly five fingers on each hand
- sharp facial details, clear eyes, well-defined nose and mouth
- high quality, professional illustration, masterpiece quality
- clean composition with clear focal point on the character
"""

# 네거티브 프롬프트 (하지 말아야 할 것들)
NEGATIVE_PROMPT = """
NEVER include any of these in the image:
- extra fingers, missing fingers, fused fingers, deformed hands, malformed hands
- distorted face, asymmetrical eyes, broken facial features, ugly face
- extra limbs, missing limbs, floating limbs, disconnected body parts
- blurry, low quality, pixelated, jpeg artifacts, noise
- multiple characters unless explicitly requested
- cropped character, cut off body parts at frame edge
- text, watermark, signature, logo, caption, speech bubble, UI element
- nudity, revealing clothes, sexualized pose, suggestive content
"""


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
Create a safe, non-explicit, fully clothed, high-quality character illustration.

Fixed character identity (MUST remain identical across all 6 scenes):
- category style: {character_profile.get("category_hint", "")}
- gender presentation: {gender}
- hair style and color: {hair}
- eye color and shape: {eyes}
- outfit top: {top}
- outfit bottom: {bottom}
- shoes: {shoes}
- accessories: {accessories}
- visual style keywords: {style_text}
{f"- user-defined character traits: {custom_tags_text}" if custom_tags_text else ""}

Character consistency rules (CRITICAL):
- This is the SAME character in every scene — same face, same hairstyle, same hair color, same eye color
- Same outfit in every scene — same clothing colors, same design, same accessories
- Maintain consistent body proportions and character height across all scenes
- Character should be recognizable as the same person in every frame
- keep the character fully clothed
- no sexualized pose, no revealing clothes, no body emphasis, no nudity, no suggestive content
- {forbidden_text}

Composition rules:
- Focus on upper body or medium shot (waist-up preferred)
- Keep hands behind back, at sides, or out of frame when possible
- Avoid detailed hand poses — if hands must appear, show them simply (fist, palm flat, etc.)
- Character should be the clear focal point of the image
"""
    return anchor_prompt.strip()


def build_image_prompt(character_profile: dict | None, scene: dict, art_style: str = "webtoon") -> str:
    character_anchor = build_character_anchor(character_profile) if character_profile else ""
    style_desc = ART_STYLE_MAP.get(art_style, ART_STYLE_MAP["webtoon"])

    scene_prompt = f"""
Scene instructions:
- scene order: {scene["scene_order"]} of 6
- scene situation: {scene["subtitle_text"]}
- emotional tone / dialogue context: {scene["dialogue"]}

Image style:
- {style_desc}
- cinematic composition, professional quality
- character-focused scene with clean background
- safe for general audience
"""

    full_prompt = f"{character_anchor}\n\n{scene_prompt}\n\n{QUALITY_PROMPT}\n\n{NEGATIVE_PROMPT}"
    return full_prompt.strip()


def generate_six_cut_images(job_id: int, character_profile: dict, scenes: list, art_style: str = "webtoon", image_quality: str = "high"):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY가 설정되지 않았습니다.")

    results = []

    for scene in scenes:
        prompt = build_image_prompt(character_profile, scene, art_style)

        try:
            current_prompt = prompt
            for attempt in range(2):
                try:
                    response = client.images.generate(
                        model="gpt-image-1.5",
                        prompt=current_prompt,
                        size="1024x1536",
                        quality=image_quality,
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


def generate_single_image(job_id: int, character_profile: dict, scene: dict, art_style: str = "webtoon", image_quality: str = "high"):
    """이미지 1장만 생성 (SSE 스트리밍용). 모더레이션 차단 시 안전한 프롬프트로 재시도."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OPENAI_API_KEY가 설정되지 않았습니다.")

    prompt = build_image_prompt(character_profile, scene, art_style)

    for attempt in range(2):
        try:
            response = client.images.generate(
                model="gpt-image-1.5",
                prompt=prompt,
                size="1024x1536",
                quality=image_quality,
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