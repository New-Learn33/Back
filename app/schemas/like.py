from pydantic import BaseModel


class LikeData(BaseModel):
    video_id: int
    liked: bool
    like_count: int


class LikeResponse(BaseModel):
    success: bool = True
    message: str
    data: LikeData
