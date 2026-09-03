from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ..models.work_items import PriorityEnum, WorkStatusEnum


class WorkItemBase(BaseModel):
    site_id: int | None = Field(default=None)
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    assignee_id: int | None = Field(default=None)
    status: WorkStatusEnum = Field(default=WorkStatusEnum.TODO)
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    due_date: datetime | None = Field(default=None)


class WorkItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    assignee_id: int | None = Field(default=None)
    status: WorkStatusEnum = Field(default=WorkStatusEnum.TODO)
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    due_date: datetime | None = Field(default=None)


class WorkItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    assignee_id: int | None = Field(default=None)
    status: WorkStatusEnum | None = Field(default=None)
    priority: PriorityEnum | None = Field(default=None)
    due_date: datetime | None = Field(default=None)


class WorkItemResponse(BaseModel):
    id: int
    site_id: int
    title: str
    description: str | None = None
    assignee_id: int | None = None
    status: WorkStatusEnum
    priority: PriorityEnum
    due_date: datetime | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class WorkItemCommentCreate(BaseModel):
    content: str = Field(..., min_length=1)


class WorkItemCommentResponse(BaseModel):
    id: int
    work_item_id: int
    user_id: int
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkItemAttachmentResponse(BaseModel):
    id: int
    work_item_id: int
    uploader_id: int
    file_name: str
    file_path: str
    file_type: str
    file_size: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
