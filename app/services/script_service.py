import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import HTTPException

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def validate_script_result(data: dict):
    if "title" not in data:
        raise HTTPException(status_code=500, detail="script 결과에 title이 없습니다.")

    if "scenes" not in data or not isinstance(data["scenes"], list):
        raise HTTPException(status_code=500, detail="script 결과에 scenes가 없습니다.")

    if len(data["scenes"]) != 6:
        raise HTTPException(status_code=500, detail="scenes는 반드시 6개여야 합니다.")

    expected_orders = [1, 2, 3, 4, 5, 6]
    actual_orders = [scene.get("scene_order") for scene in data["scenes"]]

    if actual_orders != expected_orders:
        raise HTTPException(status_code=500, detail="scene_order는 1~6 이어야 합니다.")

    for scene in data["scenes"]:
        if "dialogue" not in scene:
            raise HTTPException(status_code=500, detail="scene에 dialogue가 없습니다.")
        if "subtitle_text" not in scene:
            raise HTTPException(status_code=500, detail="scene에 subtitle_text가 없습니다.")


def generate_six_cut_script(request):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY가 설정되지 않았습니다.")

    system_prompt = """
You are a screenplay writer for a 6-cut webtoon style comic.

Return ONLY valid JSON.
Do not include markdown fences.
Do not include explanations.

JSON schema:
{
  "title": "string",
  "scenes": [
    {
      "scene_order": 1,
      "dialogue": "string",
      "subtitle_text": "string"
    },
    {
      "scene_order": 2,
      "dialogue": "string",
      "subtitle_text": "string"
    },
    {
      "scene_order": 3,
      "dialogue": "string",
      "subtitle_text": "string"
    },
    {
      "scene_order": 4,
      "dialogue": "string",
      "subtitle_text": "string"
    },
    {
      "scene_order": 5,
      "dialogue": "string",
      "subtitle_text": "string"
    },
    {
      "scene_order": 6,
      "dialogue": "string",
      "subtitle_text": "string"
    }
  ]
}

Rules:
- Make exactly 6 scenes.
- dialogue should be short and natural.
- subtitle_text should describe only situation, action, and emotion.
- Do NOT define or change appearance such as gender, hairstyle, outfit, accessories, body type, or colors.
- Character visual identity is managed separately by the system.
- Keep each scene visually distinct in action/emotion, but not in character identity.
"""

    user_prompt = f"""
카테고리 ID: {request.category_id}
사용자 프롬프트: {request.prompt}

위 정보를 바탕으로 6컷 만화 대사와 장면 설명을 생성해라.
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        text = response.output_text.strip()

        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        data = json.loads(text)
        validate_script_result(data)
        return data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대사 생성 실패: {str(e)}")