from datetime import datetime

from pydantic import BaseModel, ConfigDict

from ..models import ActivityActionEnum


class ActivityLogBase(BaseModel):
    action: ActivityActionEnum
    details: str | None = None


class ActivityLogCreate(ActivityLogBase):
    site_id: int
    user_id: int


class ActivityLogResponse(ActivityLogBase):
    id: int
    site_id: int
    user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
