from typing import List

from pydantic import BaseModel, ConfigDict, Field, constr


class CommentCreateRequest(BaseModel):
    content: constr(strip_whitespace=True, min_length=1, max_length=1000) = Field(
        ...,
        example="너무 재밌어요!",
    )


class CommentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    comment_id: int
    video_id: int
    nickname: str
    content: str


class CommentCreateData(BaseModel):
    comment: CommentItem


class CommentCreateResponse(BaseModel):
    success: bool = True
    message: str = "댓글 작성 성공"
    data: CommentCreateData


class CommentListData(BaseModel):
    comments: List[CommentItem]


class CommentListResponse(BaseModel):
    success: bool = True
    message: str = "댓글 목록 조회 성공"
    data: CommentListData


class CommentDeleteData(BaseModel):
    comment_id: int


class CommentDeleteResponse(BaseModel):
    success: bool = True
    message: str = "댓글 삭제 성공"
    data: CommentDeleteData
