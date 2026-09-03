import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from ..core.exception import ValidationException
from ..models.users import RoleUserEnum

PASSWORD_REGEX = (
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
)
PASSWORD_ERROR_MESSAGE = (
    "Password must contain at least one lowercase letter, "
    "one uppercase letter, one digit, and one special character"
)


class UserBase(BaseModel):
    email: EmailStr = Field(...)
    full_name: str = Field(..., min_length=1, max_length=100)
    role: RoleUserEnum = Field(default=RoleUserEnum.USER)
    is_active: bool = Field(default=True)


class UserCreate(BaseModel):
    email: EmailStr = Field(...)
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(PASSWORD_REGEX, v):
            raise ValidationException(PASSWORD_ERROR_MESSAGE)
        return v


class UserUpdate(BaseModel):
    email: EmailStr | None = Field(default=None)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    full_name: str | None = Field(default=None, min_length=1, max_length=100)
    role: RoleUserEnum | None = Field(default=None)
    is_active: bool | None = Field(default=None)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        if v is not None and not re.match(PASSWORD_REGEX, v):
            raise ValidationException(PASSWORD_ERROR_MESSAGE)
        return v


class UserResponse(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
