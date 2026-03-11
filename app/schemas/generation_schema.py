from pydantic import BaseModel, Field
from typing import List, Optional


class SceneScriptItem(BaseModel):
    scene_order: int = Field(..., example=1)
    dialogue: str = Field(..., example="오랜만이네. 진짜 너 맞구나?")
    subtitle_text: str = Field(..., example="예상치 못한 재회")


class GenerationRequest(BaseModel):
    category_id: int = Field(..., example=1)
    prompt: str = Field(..., example="세상이 멸망하는데 히어로가 늦잠을 잤다")


class ImageResultItem(BaseModel):
    scene_order: int = Field(..., example=1)
    image_url: str = Field(..., example="https://example.com/generated/1_1.png")


class SelectedTemplateImage(BaseModel):
    id: int = Field(..., example=101)
    name: str = Field(..., example="애니 캐릭터 1")
    image_url: str = Field(..., example="https://example.com/anime1.png")


class GenerationData(BaseModel):
    job_id: int
    title: str
    category_id: int
    selected_template_image: SelectedTemplateImage
    scenes: List[SceneScriptItem]
    images: List[ImageResultItem]


class GenerationResponse(BaseModel):
    success: bool = True
    message: str = "3컷 생성 성공"
    data: GenerationData


# API 요청 바디 검증 - 자막/영상 렌더링용 모델 추가

class ImageItem(BaseModel):
    scene_order: int
    image_url: str


class SceneItem(BaseModel):
    scene_order: int
    dialogue: str
    subtitle_text: Optional[str] = None


class RenderSubtitleRequest(BaseModel):
    job_id: int
    images: List[ImageItem]
    scenes: List[SceneItem]


class SubtitleImageItem(BaseModel):
    scene_order: int
    image_url: str
    duration: Optional[int] = 2


class RenderVideoRequest(BaseModel):
    job_id: int
    subtitle_images: List[SubtitleImageItem]