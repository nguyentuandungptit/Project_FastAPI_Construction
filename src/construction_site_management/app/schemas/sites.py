from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ..models.sites import RoleSiteMemberEnum


class SiteMemberBase(BaseModel):
    site_id: int = Field(...)
    user_id: int = Field(...)
    role: RoleSiteMemberEnum = Field(default=RoleSiteMemberEnum.MEMBER)


class SiteMemberCreate(SiteMemberBase):
    pass


class SiteMemberUpdate(BaseModel):
    role: RoleSiteMemberEnum = Field(default=RoleSiteMemberEnum.MEMBER)


class SiteMemberResponse(SiteMemberBase):
    joined_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConstructionSiteBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=0, max_length=1000)
    owner_id: int = Field(...)


class ConstructionSiteCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=0, max_length=1000)


class ConstructionSiteUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=0, max_length=1000)

    is_deleted: bool | None = Field(default=None)
    deleted_at: datetime | None = Field(default=None)


class ConstructionSiteResponse(ConstructionSiteBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
