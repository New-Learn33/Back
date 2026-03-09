from pydantic import BaseModel, Field
from typing import List


class SceneScriptItem(BaseModel):
    scene_order: int = Field(..., example=1)
    dialogue: str = Field(..., example="오랜만이네. 진짜 너 맞구나?")
    subtitle_text: str = Field(..., example="예상치 못한 재회")


class ScriptGenerateRequest(BaseModel):
    category_id: int = Field(..., example=1)
    prompt: str = Field(..., example="지하철에서 우연히 다시 만난 두 사람의 어색한 재회")


class ScriptGenerateData(BaseModel):
    job_id: int = Field(..., example=1)
    scenes: List[SceneScriptItem]


class ScriptGenerateResponse(BaseModel):
    success: bool = True
    message: str = "3컷 대사 생성 성공"
    data: ScriptGenerateData


class ImageGenerateRequest(BaseModel):
    job_id: int = Field(..., example=1)
    template_image_id: int = Field(..., example=101)
    scenes: List[SceneScriptItem]


class ImageResultItem(BaseModel):
    scene_order: int = Field(..., example=1)
    image_url: str = Field(..., example="https://example.com/image1.png")


class ImageGenerateData(BaseModel):
    job_id: int = Field(..., example=1)
    images: List[ImageResultItem]


class ImageGenerateResponse(BaseModel):
    success: bool = True
    message: str = "3컷 이미지 생성 성공"
    data: ImageGenerateData