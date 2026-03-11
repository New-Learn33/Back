from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, constr


class UserProfileItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nickname: str
    profile_image_url: Optional[str] = None


class UserProfileData(BaseModel):
    user: UserProfileItem


class UserProfileResponse(BaseModel):
    success: bool = True
    message: str
    data: UserProfileData


class UserProfileUpdateRequest(BaseModel):
    nickname: Optional[constr(strip_whitespace=True, min_length=1, max_length=100)] = Field(
        default=None,
        example="히히",
    )
    profile_image_url: Optional[str] = None


class UserVideoItem(BaseModel):
    id: int
    title: str
    category_id: int
    thumbnail_url: str
    video_url: str
    like_count: int
    comment_count: int
    view_count: int


class UserVideoListData(BaseModel):
    videos: List[UserVideoItem]


class UserVideoListResponse(BaseModel):
    success: bool = True
    message: str
    data: UserVideoListData


class UserCommentItem(BaseModel):
    id: int
    video_id: int
    content: str


class UserCommentListData(BaseModel):
    comments: List[UserCommentItem]


class UserCommentListResponse(BaseModel):
    success: bool = True
    message: str
    data: UserCommentListData
