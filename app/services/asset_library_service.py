import os
import json
import base64
import re
import uuid
from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session

from app.models.asset import Asset

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # app/
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(STATIC_DIR, "templates")

CATEGORY_ID_TO_FOLDER = {
    1: "ani",
    2: "hero",
    3: "game",
    4: "fantasy",
}

CATEGORY_FOLDER_TO_HINT = {
    "ani": "anime style",
    "hero": "superhero style",
    "game": "game character style",
    "fantasy": "fantasy character style",
}

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def ensure_dirs():
    os.makedirs(TEMPLATES_DIR, exist_ok=True)
    for folder in CATEGORY_ID_TO_FOLDER.values():
        os.makedirs(os.path.join(TEMPLATES_DIR, folder), exist_ok=True)


def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def sanitize_stem(filename: str) -> str:
    stem = os.path.splitext(filename)[0]
    stem = stem.strip().lower()
    stem = re.sub(r"[()]+", "", stem)
    stem = re.sub(r"\s+", "_", stem)
    stem = re.sub(r"[^a-zA-Z0-9_가-힣-]", "", stem)
    return stem


def guess_mime_type(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".png":
        return "image/png"
    if ext in [".jpg", ".jpeg"]:
        return "image/jpeg"
    if ext == ".webp":
        return "image/webp"
    return "application/octet-stream"


def parse_json_text(text: str) -> dict:
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    return json.loads(text)


def analyze_character(image_path: str, folder_name: str, asset_name: str, image_url: str) -> dict:
    image_b64 = encode_image_to_base64(image_path)
    category_hint = CATEGORY_FOLDER_TO_HINT[folder_name]
    character_name = sanitize_stem(asset_name)

    prompt = f"""
You are analyzing a fictional character image for consistent image generation.

Return ONLY valid JSON.
Do not include markdown fences.
Do not include explanations.

The JSON schema must be:

{{
  "gender": "male/female/ambiguous",
  "appearance": {{
    "hair": "short concise phrase",
    "eyes": "short concise phrase",
    "skin": "short concise phrase",
    "body_type": "short concise phrase"
  }},
  "outfit": {{
    "top": "short concise phrase",
    "bottom": "short concise phrase",
    "shoes": "short concise phrase",
    "accessories": ["item1", "item2"]
  }},
  "style_keywords": ["keyword1", "keyword2", "keyword3"],
  "forbidden_changes": ["rule1", "rule2", "rule3"]
}}

Rules:
- Be objective and visually grounded.
- Keep each phrase short.
- Focus on stable visual identity.
- If something is unclear, use a conservative neutral description.
- accessories must be an array.
- style_keywords must be an array.
- forbidden_changes must be an array.
- category style is: {category_hint}
- character name is: {character_name}
"""

    mime_type = guess_mime_type(image_path)

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:{mime_type};base64,{image_b64}",
                    },
                ],
            }
        ],
    )

    parsed = parse_json_text(response.output_text)

    return {
        "id": f"{folder_name}_{character_name}_{uuid.uuid4().hex[:8]}",
        "name": asset_name,
        "image_url": image_url,
        "category_hint": category_hint,
        "character_name": character_name,
        "gender": parsed.get("gender", "ambiguous"),
        "appearance": parsed.get(
            "appearance",
            {"hair": "", "eyes": "", "skin": "", "body_type": ""},
        ),
        "outfit": parsed.get(
            "outfit",
            {"top": "", "bottom": "", "shoes": "", "accessories": []},
        ),
        "style_keywords": parsed.get("style_keywords", []),
        "forbidden_changes": parsed.get(
            "forbidden_changes",
            [
                "do not change gender",
                "do not change hairstyle",
                "do not change outfit design",
                "do not change outfit colors",
            ],
        ),
    }


def save_uploaded_file(file_bytes: bytes, original_filename: str, category_id: int) -> tuple[str, str]:
    ensure_dirs()

    folder_name = CATEGORY_ID_TO_FOLDER[category_id]
    ext = os.path.splitext(original_filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("지원하지 않는 이미지 형식입니다. png/jpg/jpeg/webp만 가능합니다.")

    safe_name = sanitize_stem(os.path.splitext(original_filename)[0])
    unique_filename = f"{safe_name}_{uuid.uuid4().hex[:8]}{ext}"

    save_dir = os.path.join(TEMPLATES_DIR, folder_name)
    save_path = os.path.join(save_dir, unique_filename)

    with open(save_path, "wb") as f:
        f.write(file_bytes)

    image_url = f"/static/templates/{folder_name}/{unique_filename}"
    return save_path, image_url


def asset_to_dict(asset: Asset) -> dict:
    """Asset DB 모델을 dict로 변환"""
    return {
        "id": asset.id,
        "name": asset.name,
        "image_url": asset.image_url,
        "category_id": str(asset.category_id),
        "category_hint": asset.category_hint,
        "character_name": asset.character_name,
        "gender": asset.gender,
        "appearance": asset.appearance,
        "outfit": asset.outfit,
        "style_keywords": asset.style_keywords,
        "forbidden_changes": asset.forbidden_changes,
        "custom_tags": asset.custom_tags or [],
    }


def create_asset_profile(
    db: Session,
    user_id: int,
    file_bytes: bytes,
    original_filename: str,
    category_id: int,
    asset_name: str | None = None,
) -> dict:
    if category_id not in CATEGORY_ID_TO_FOLDER:
        raise ValueError("유효하지 않은 category_id 입니다.")

    final_asset_name = asset_name or sanitize_stem(original_filename)

    saved_path, image_url = save_uploaded_file(file_bytes, original_filename, category_id)
    folder_name = CATEGORY_ID_TO_FOLDER[category_id]

    profile = analyze_character(
        image_path=saved_path,
        folder_name=folder_name,
        asset_name=final_asset_name,
        image_url=image_url,
    )

    # DB에 저장
    asset = Asset(
        id=profile["id"],
        user_id=user_id,
        category_id=category_id,
        name=profile["name"],
        image_url=profile["image_url"],
        category_hint=profile["category_hint"],
        character_name=profile["character_name"],
        gender=profile["gender"],
        appearance=profile["appearance"],
        outfit=profile["outfit"],
        style_keywords=profile["style_keywords"],
        forbidden_changes=profile["forbidden_changes"],
        file_size=len(file_bytes),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset_to_dict(asset)


def delete_asset_profile(db: Session, asset_id: str, user_id: int) -> bool:
    """에셋 프로필과 이미지 파일을 삭제합니다. 본인 에셋만 삭제 가능."""
    from app.models.user import User

    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.user_id == user_id).first()
    if not asset:
        return False

    file_size = asset.file_size or 0

    # 이미지 파일 삭제
    image_url = asset.image_url or ""
    if image_url.startswith("/static/"):
        image_path = os.path.join(BASE_DIR, image_url.lstrip("/"))
        if os.path.exists(image_path):
            os.remove(image_path)

    db.delete(asset)

    # storage_used 차감
    if file_size > 0:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.storage_used = max(0, (user.storage_used or 0) - file_size)

    db.commit()
    return True


def get_asset_profiles(db: Session, user_id: int, category_id: int | None = None) -> List[dict]:
    """유저의 에셋 목록 조회"""
    query = db.query(Asset).filter(Asset.user_id == user_id)
    if category_id is not None:
        query = query.filter(Asset.category_id == category_id)

    assets = query.order_by(Asset.created_at.desc()).all()
    return [asset_to_dict(a) for a in assets]
