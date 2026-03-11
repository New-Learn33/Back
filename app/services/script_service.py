import os
import json
from dotenv import load_dotenv
from fastapi import HTTPException
from openai import OpenAI

from app.schemas.generation_schema import GenerationRequest

load_dotenv(override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CATEGORY_STYLE = {
    1: "애니 스타일. 감정 표현이 풍부하고 과장된 리액션, 밝고 생동감 있는 분위기",
    2: "히어로 스타일. 정의감, 액션, 위기 해결, 강렬한 대사 중심",
    3: "게임 스타일. 퀘스트, 전투, 레벨업, 게임 UI 감성의 대사",
    4: "판타지 스타일. 마법, 왕국, 모험, 전설적인 분위기",
}


def validate_scenes(scenes: list):
    if len(scenes) != 3:
        raise HTTPException(status_code=500, detail="scene 개수가 3개가 아닙니다.")

    expected_orders = [1, 2, 3]
    actual_orders = [scene.get("scene_order") for scene in scenes]

    if actual_orders != expected_orders:
        raise HTTPException(status_code=500, detail="scene_order는 1,2,3 이어야 합니다.")

    for scene in scenes:
        if "dialogue" not in scene or "subtitle_text" not in scene:
            raise HTTPException(status_code=500, detail="scene 형식이 올바르지 않습니다.")


def generate_three_cut_script(request: GenerationRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY가 설정되지 않았습니다.")

    category_style = CATEGORY_STYLE.get(request.category_id, "일반 웹툰 스타일")

    system_prompt = f"""
너는 3컷 웹툰 대사를 생성하는 AI다.
카테고리 스타일: {category_style}

반드시 아래 JSON 형식으로만 답변해라.

{{
  "title": "영상 제목",
  "scenes": [
    {{
      "scene_order": 1,
      "dialogue": "대사",
      "subtitle_text": "장면 설명"
    }},
    {{
      "scene_order": 2,
      "dialogue": "대사",
      "subtitle_text": "장면 설명"
    }},
    {{
      "scene_order": 3,
      "dialogue": "대사",
      "subtitle_text": "장면 설명"
    }}
  ]
}}

규칙:
- 반드시 scene은 3개
- scene_order는 반드시 1, 2, 3
- dialogue는 짧고 자연스럽게
- subtitle_text는 해당 장면의 상황 설명
- title은 매력적이고 짧게
- JSON 외의 텍스트는 절대 출력하지 마라
"""

    user_prompt = f"""
다음 프롬프트를 바탕으로 3컷 웹툰 대사를 생성해라.

프롬프트:
{request.prompt}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.7,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        content = response.choices[0].message.content
        if not content:
            raise HTTPException(status_code=500, detail="OpenAI 응답이 비어 있습니다.")

        data = json.loads(content)

        scenes = data.get("scenes", [])
        validate_scenes(scenes)

        return {
            "title": data.get("title", "제목 없음"),
            "scenes": scenes,
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="OpenAI 응답 JSON 파싱 실패")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"대사 생성 실패: {str(e)}")