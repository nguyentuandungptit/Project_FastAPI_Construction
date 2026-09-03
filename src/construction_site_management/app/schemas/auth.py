from pydantic import BaseModel, EmailStr, Field


class UserLogin(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str
