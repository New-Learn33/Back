import os
import json
import base64
import re
import uuid
from typing import Dict, List
from dotenv import load_dotenv
from openai import OpenAI

from app.data.character_profiles_loader import load_character_profiles

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # app/
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(STATIC_DIR, "templates")
DATA_DIR = os.path.join(BASE_DIR, "data")
PROFILE_PATH = os.path.join(DATA_DIR, "character_profiles.json")

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
    os.makedirs(DATA_DIR, exist_ok=True)
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
        model="gpt-4.1-mini",
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
            {
                "hair": "",
                "eyes": "",
                "skin": "",
                "body_type": "",
            },
        ),
        "outfit": parsed.get(
            "outfit",
            {
                "top": "",
                "bottom": "",
                "shoes": "",
                "accessories": [],
            },
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


def append_profile_to_json(category_id: int, profile: dict) -> None:
    ensure_dirs()

    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"1": [], "2": [], "3": [], "4": []}

    key = str(category_id)
    if key not in data:
        data[key] = []

    data[key].append(profile)

    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_asset_profile(file_bytes: bytes, original_filename: str, category_id: int, asset_name: str | None = None) -> dict:
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

    append_profile_to_json(category_id, profile)
    load_character_profiles(force_reload=True)

    return profile


def get_asset_profiles(category_id: int | None = None) -> Dict[str, List[dict]] | List[dict]:
    profiles = load_character_profiles(force_reload=True)
    if category_id is None:
        return profiles
    return profiles.get(str(category_id), [])