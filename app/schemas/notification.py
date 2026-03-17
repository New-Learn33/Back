from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class NotificationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient_user_id: int
    actor_user_id: Optional[int] = None
    type: str
    title: str
    message: str
    video_id: Optional[int] = None
    comment_id: Optional[int] = None
    job_id: Optional[int] = None
    is_read: bool


class NotificationListData(BaseModel):
    notifications: List[NotificationItem]
    unread_count: int


class NotificationListResponse(BaseModel):
    success: bool = True
    message: str = "알림 목록 조회 성공"
    data: NotificationListData


class NotificationReadData(BaseModel):
    notification_id: int


class NotificationReadResponse(BaseModel):
    success: bool = True
    message: str
    data: NotificationReadData


class NotificationReadAllData(BaseModel):
    updated_count: int


class NotificationReadAllResponse(BaseModel):
    success: bool = True
    message: str
    data: NotificationReadAllData