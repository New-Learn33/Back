from typing import List

from pydantic import BaseModel


class VideoListItem(BaseModel):
    id: int
    title: str
    category_id: int
    thumbnail_url: str
    like_count: int
    comment_count: int
    liked: bool


class VideoDetailItem(VideoListItem):
    video_url: str
    view_count: int


class VideoSearchItem(BaseModel):
    id: int
    title: str
    category_id: int
    thumbnail_url: str
    like_count: int
    comment_count: int
    view_count: int


class VideoListData(BaseModel):
    videos: List[VideoListItem]


class VideoListResponse(BaseModel):
    success: bool = True
    message: str = "영상 목록 조회 성공"
    data: VideoListData


class VideoDetailData(BaseModel):
    videos: VideoDetailItem


class VideoDetailResponse(BaseModel):
    success: bool = True
    message: str = "영상 상세 조회 성공"
    data: VideoDetailData


class VideoSearchData(BaseModel):
    videos: List[VideoSearchItem]


class VideoSearchResponse(BaseModel):
    success: bool = True
    message: str = "영상 검색 성공"
    data: VideoSearchData
