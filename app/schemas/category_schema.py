from pydantic import BaseModel, Field
from typing import List, Optional


class TemplateImageItem(BaseModel):
    id: int = Field(..., example=101)
    image_url: str = Field(..., example="https://example.com/template.png")
    name: Optional[str] = Field(None, example="기본 로맨스 템플릿")


class CategoryItem(BaseModel):
    id: int = Field(..., example=1)
    name: str = Field(..., example="로맨스")
    description: Optional[str] = Field(None, example="감성적인 대화 중심 카테고리")
    template_images: List[TemplateImageItem] = []


class CategoryListResponse(BaseModel):
    success: bool = True
    message: str = "카테고리 목록 조회 성공"
    data: List[CategoryItem]