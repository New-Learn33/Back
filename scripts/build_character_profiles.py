# 처음 한 번 실행해서 app/data/character_profiles.json 생성하는 스크립트

import os
import json
import base64
import re
from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
APP_DIR = os.path.join(PROJECT_ROOT, "app")
TEMPLATES_DIR = os.path.join(APP_DIR, "static", "templates")
DATA_DIR = os.path.join(APP_DIR, "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "character_profiles.json")

CATEGORY_FOLDER_TO_ID = {
    "ani": 1,
    "hero": 2,
    "game": 3,
    "fantasy": 4,
}

CATEGORY_FOLDER_TO_HINT = {
    "ani": "anime style",
    "hero": "superhero style",
    "game": "game character style",
    "fantasy": "fantasy character style",
}


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


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


def build_image_url(folder_name: str, filename: str) -> str:
    return f"/static/templates/{folder_name}/{filename}"


def parse_json_text(text: str) -> dict:
    text = text.strip()

    # ```json ... ``` 제거
    if text.startswith("```"):
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    return json.loads(text)


def analyze_character(image_path: str, folder_name: str, filename: str) -> dict:
    image_b64 = encode_image_to_base64(image_path)
    category_hint = CATEGORY_FOLDER_TO_HINT[folder_name]
    character_name = sanitize_stem(filename)

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

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{image_b64}",
                    },
                ],
            }
        ],
    )

    text = response.output_text
    parsed = parse_json_text(text)

    profile = {
        "id": f"{folder_name}_{character_name}",
        "name": character_name,
        "image_url": build_image_url(folder_name, filename),
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

    return profile


def collect_images(folder_path: str) -> List[str]:
    allowed_ext = {".png", ".jpg", ".jpeg", ".webp"}
    files = []

    for filename in os.listdir(folder_path):
        ext = os.path.splitext(filename)[1].lower()
        if ext in allowed_ext:
            files.append(filename)

    files.sort()
    return files


def main():
    ensure_data_dir()

    result: Dict[str, List[dict]] = {
        "1": [],
        "2": [],
        "3": [],
        "4": [],
    }

    for folder_name, category_id in CATEGORY_FOLDER_TO_ID.items():
        folder_path = os.path.join(TEMPLATES_DIR, folder_name)

        if not os.path.exists(folder_path):
            print(f"[SKIP] 폴더 없음: {folder_path}")
            continue

        image_files = collect_images(folder_path)
        print(f"[INFO] {folder_name}: {len(image_files)}개 이미지 발견")

        for filename in image_files:
            image_path = os.path.join(folder_path, filename)
            print(f"[RUN ] 분석 중: {folder_name}/{filename}")

            try:
                profile = analyze_character(image_path, folder_name, filename)
                result[str(category_id)].append(profile)
                print(f"[DONE] {filename}")
            except Exception as e:
                print(f"[FAIL] {filename}: {e}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n[SAVED] character_profiles.json 생성 완료: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()