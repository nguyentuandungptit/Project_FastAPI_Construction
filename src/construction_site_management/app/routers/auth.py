from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from ..core.limiter import limiter
from ..db.database import get_db
from ..schemas import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from ..services import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản",
    description="Đăng ký tài khoản người dùng mới với email, họ tên và mật khẩu hợp lệ (tối thiểu 8 ký tự, có chữ hoa, chữ thường, số và ký tự đặc biệt).",
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
):
    return await AuthService.register_handle(data, db)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập",
    description="Xác thực email và mật khẩu, trả về cặp JWT Access Token và Refresh Token.",
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: UserLogin,
    db: Annotated[Session, Depends(get_db)],
):
    return await AuthService.login(data, db)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Cấp lại access token",
    description="Sử dụng Refresh Token hợp lệ để lấy Access Token mới mà không cần đăng nhập lại.",
)
@limiter.limit("5/minute")
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    db: Annotated[Session, Depends(get_db)],
):
    return await AuthService.refresh_token(data.refresh_token, db)

