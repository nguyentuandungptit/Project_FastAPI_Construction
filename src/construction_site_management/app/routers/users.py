from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from ..core.limiter import limiter
from ..db.database import get_db
from ..dependencies.auth import RoleUserChecker, get_current_active_user
from ..models import RoleUserEnum, UserModel
from ..schemas import UserResponse
from ..services import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Xem hồ sơ cá nhân",
    description="Trả về thông tin chi tiết của người dùng đang đăng nhập (không bao gồm password_hash).",
)
@limiter.limit("5/minute")
async def get_my_profile(
    request: Request,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return current_user


@router.get(
    "",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Danh sách người dùng (Admin)",
    description="Chỉ dành cho Admin. Hỗ trợ tìm kiếm theo họ tên hoặc email, lọc theo trạng thái kích hoạt và phân trang.",
)
@limiter.limit("5/minute")
async def get_all_users(
    request: Request,
    current_user: Annotated[UserModel, Depends(RoleUserChecker([RoleUserEnum.ADMIN]))],
    db: Annotated[Session, Depends(get_db)],
    user_id: Annotated[int | None, Query(description="ID người dùng cụ thể")] = None,
    search: Annotated[
        str | None, Query(description="Tìm kiếm theo họ tên hoặc email")
    ] = None,
    is_active: Annotated[
        bool | None, Query(description="Lọc theo trạng thái hoạt động")
    ] = None,
    skip: Annotated[int, Query(ge=0, description="Số lượng bản ghi bỏ qua")] = 0,
    limit: Annotated[int, Query(gt=0, description="Số lượng bản ghi tối đa")] = 20,
    page: Annotated[int | None, Query(ge=1, description="Số thứ tự trang")] = None,
    size: Annotated[int | None, Query(gt=0, description="Kích thước trang")] = None,
):
    if user_id:
        return [UserService.get_user_by_id(db, user_id)]
    return UserService.get_all_users(
        db=db,
        skip=skip,
        limit=limit,
        page=page,
        size=size,
        search=search,
        is_active=is_active,
    )

