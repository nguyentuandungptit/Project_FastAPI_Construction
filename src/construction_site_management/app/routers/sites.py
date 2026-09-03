from typing import Annotated

from fastapi import APIRouter, Depends, File, Path, Query, Request, UploadFile, status
from sqlalchemy.orm import Session

from ..core.limiter import limiter
from ..db.database import get_db
from ..dependencies.auth import (
    RoleSiteMemberChecker,
    WorkItemPermissionChecker,
    get_current_active_user,
)
from ..models import RoleSiteMemberEnum, SiteMemberModel, UserModel
from ..models.work_items import PriorityEnum, WorkStatusEnum
from ..schemas import (
    ActivityLogResponse,
    ConstructionSiteCreate,
    ConstructionSiteResponse,
    ConstructionSiteUpdate,
    SiteMemberCreate,
    SiteMemberResponse,
    WorkItemAttachmentResponse,
    WorkItemCommentCreate,
    WorkItemCommentResponse,
    WorkItemCreate,
    WorkItemResponse,
    WorkItemUpdate,
)
from ..services import ActivityLogService, ConstructionSiteService, WorkItemService

construction_sites_router = APIRouter(prefix="/construction-sites", tags=["Sites"])

work_items_router = APIRouter(prefix="/work-items", tags=["Work Items"])


@construction_sites_router.post(
    "",
    response_model=ConstructionSiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo công trình mới",
    description="Người dùng đăng nhập tạo công trình và tự động trở thành OWNER của công trình.",
)
@limiter.limit("5/minute")
def handle_create_construction_site(
    request: Request,
    construction_site: ConstructionSiteCreate,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return ConstructionSiteService.create_construction_site(
        db, construction_site, current_user
    )


@construction_sites_router.get(
    "",
    response_model=list[ConstructionSiteResponse],
    status_code=status.HTTP_200_OK,
    summary="Danh sách công trình của tôi",
    description="Lấy danh sách các công trình mà người dùng hiện tại là OWNER hoặc MEMBER. Hỗ trợ tìm kiếm theo tên và phân trang.",
)
@limiter.limit("5/minute")
def handle_get_all_construction_sites(
    request: Request,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
    search: Annotated[
        str | None, Query(description="Tìm kiếm theo tên công trình")
    ] = None,
    skip: Annotated[int, Query(ge=0, description="Số lượng bản ghi bỏ qua")] = 0,
    limit: Annotated[int, Query(gt=0, description="Số lượng bản ghi tối đa")] = 20,
    page: Annotated[int | None, Query(ge=1, description="Số thứ tự trang")] = None,
    size: Annotated[int | None, Query(gt=0, description="Kích thước trang")] = None,
):
    return ConstructionSiteService.get_construction_sites_by_user(
        db=db,
        user=current_user,
        skip=skip,
        limit=limit,
        page=page,
        size=size,
        search=search,
    )


@construction_sites_router.get(
    "/{site_id}",
    response_model=ConstructionSiteResponse,
    status_code=status.HTTP_200_OK,
    summary="Chi tiết công trình",
    description="Xem thông tin chi tiết của một công trình. Yêu cầu người dùng phải là thành viên (OWNER hoặc MEMBER) của công trình.",
)
@limiter.limit("5/minute")
def handle_get_construction_site(
    request: Request,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    site_id: Annotated[int, Path(..., description="ID của công trình")],
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(
            RoleSiteMemberChecker([RoleSiteMemberEnum.OWNER, RoleSiteMemberEnum.MEMBER])
        ),
    ],
):
    return ConstructionSiteService.get_construction_site(db, site_id)


@construction_sites_router.patch(
    "/{site_id}",
    response_model=ConstructionSiteResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật công trình",
    description="Cập nhật thông tin công trình (tên, mô tả). Chỉ người sở hữu (OWNER) mới có quyền thực hiện.",
)
@limiter.limit("5/minute")
def handle_update_construction_site(
    request: Request,
    site_id: Annotated[int, Path(..., description="ID của công trình")],
    site_data: ConstructionSiteUpdate,
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(RoleSiteMemberChecker([RoleSiteMemberEnum.OWNER])),
    ],
):
    return ConstructionSiteService.update_construction_site(
        db, site_id, site_data, site_member.user_id
    )


@construction_sites_router.delete(
    "/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa công trình (Soft delete)",
    description="Xóa mềm công trình (đánh dấu is_deleted=True và lưu deleted_at). Chỉ OWNER mới có quyền thực hiện.",
)
@limiter.limit("5/minute")
def handle_delete_construction_site(
    request: Request,
    site_id: Annotated[int, Path(..., description="ID của công trình")],
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(RoleSiteMemberChecker([RoleSiteMemberEnum.OWNER])),
    ],
):
    ConstructionSiteService.delete_construction_site(db, site_id, site_member.user_id)


# Members


@construction_sites_router.post(
    "/{site_id}/members",
    response_model=SiteMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm thành viên vào công trình",
    description="OWNER thêm người dùng khác vào công trình. Không cho phép thêm người dùng đã là thành viên.",
)
@limiter.limit("5/minute")
def handle_add_member(
    request: Request,
    site_id: Annotated[int, Path(..., description="ID của công trình")],
    member_data: SiteMemberCreate,
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(RoleSiteMemberChecker([RoleSiteMemberEnum.OWNER])),
    ],
):
    return ConstructionSiteService.add_member(
        db, site_id, member_data, site_member.user_id
    )


@construction_sites_router.get(
    "/{site_id}/members",
    response_model=list[SiteMemberResponse],
    status_code=status.HTTP_200_OK,
    summary="Danh sách thành viên công trình",
    description="Xem danh sách tất cả thành viên và vai trò trong công trình. Chỉ thành viên công trình mới có quyền xem.",
)
@limiter.limit("5/minute")
def handle_get_members(
    request: Request,
    site_id: Annotated[int, Path(..., description="ID của công trình")],
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(
            RoleSiteMemberChecker([RoleSiteMemberEnum.OWNER, RoleSiteMemberEnum.MEMBER])
        ),
    ],
):
    return ConstructionSiteService.get_members(db, site_id)


@construction_sites_router.delete(
    "/{site_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa thành viên khỏi công trình",
    description="OWNER xóa một thành viên khỏi công trình. Không được phép xóa OWNER khỏi công trình.",
)
@limiter.limit("5/minute")
def handle_remove_member(
    request: Request,
    site_id: Annotated[int, Path(..., description="ID của công trình")],
    user_id: Annotated[int, Path(..., description="ID của người dùng cần xóa")],
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(RoleSiteMemberChecker([RoleSiteMemberEnum.OWNER])),
    ],
):
    ConstructionSiteService.remove_member(db, site_id, user_id, site_member.user_id)


# Activity Logs


@construction_sites_router.get(
    "/{site_id}/activity-logs",
    response_model=list[ActivityLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Nhật ký hoạt động công trình",
    description="Xem lịch sử các thao tác quan trọng trong công trình (tạo/sửa công trình, thêm/xóa thành viên, tạo/sửa/xóa hạng mục thi công).",
)
@limiter.limit("10/minute")
def handle_get_activity_logs(
    request: Request,
    site_id: Annotated[int, Path(..., description="ID của công trình")],
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(
            RoleSiteMemberChecker([RoleSiteMemberEnum.OWNER, RoleSiteMemberEnum.MEMBER])
        ),
    ],
    skip: Annotated[int, Query(ge=0, description="Số lượng bản ghi bỏ qua")] = 0,
    limit: Annotated[int, Query(gt=0, description="Số lượng bản ghi tối đa")] = 20,
):
    return ActivityLogService.get_site_activities(db, site_id, skip, limit)


# Work Items


@construction_sites_router.post(
    "/{site_id}/work-items",
    response_model=WorkItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo hạng mục thi công mới",
    description="Thành viên công trình (OWNER hoặc MEMBER) tạo hạng mục thi công mới. Assignee nếu có phải là thành viên của công trình.",
)
@limiter.limit("5/minute")
def handle_create_work_item(
    request: Request,
    site_id: Annotated[int, Path(..., description="ID của công trình")],
    work_item_data: WorkItemCreate,
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(
            RoleSiteMemberChecker([RoleSiteMemberEnum.OWNER, RoleSiteMemberEnum.MEMBER])
        ),
    ],
):
    return WorkItemService.create_work_item(
        db, site_id, work_item_data, site_member.user_id
    )


@construction_sites_router.get(
    "/{site_id}/work-items",
    response_model=list[WorkItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Danh sách hạng mục thi công của công trình",
    description="Lấy danh sách hạng mục thi công thuộc công trình. Hỗ trợ lọc theo status, priority, assignee, tìm kiếm theo tiêu đề, sắp xếp và phân trang.",
)
@limiter.limit("30/minute")
def handle_get_work_items(
    request: Request,
    site_id: Annotated[int, Path(..., description="ID của công trình")],
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(
            RoleSiteMemberChecker([RoleSiteMemberEnum.OWNER, RoleSiteMemberEnum.MEMBER])
        ),
    ],
    skip: Annotated[int, Query(ge=0, description="Số lượng bản ghi bỏ qua")] = 0,
    limit: Annotated[int, Query(gt=0, description="Số lượng bản ghi tối đa")] = 20,
    page: Annotated[int | None, Query(ge=1, description="Số thứ tự trang")] = None,
    size: Annotated[int | None, Query(gt=0, description="Kích thước trang")] = None,
    item_status: Annotated[
        WorkStatusEnum | None,
        Query(
            alias="status", description="Lọc theo trạng thái (TODO, IN_PROGRESS, DONE)"
        ),
    ] = None,
    priority: Annotated[
        PriorityEnum | None,
        Query(description="Lọc theo mức độ ưu tiên (LOW, MEDIUM, HIGH)"),
    ] = None,
    search: Annotated[
        str | None, Query(description="Tìm kiếm theo tiêu đề hạng mục")
    ] = None,
    assignee_id: Annotated[
        int | None, Query(description="Lọc theo ID người được giao việc")
    ] = None,
    sort_by: Annotated[
        str,
        Query(
            description="Trường sắp xếp (created_at, due_date, id, title, priority, status)"
        ),
    ] = "created_at",
    order: Annotated[str, Query(description="Chiều sắp xếp (asc hoặc desc)")] = "desc",
):
    return WorkItemService.get_work_items(
        db=db,
        site_id=site_id,
        skip=skip,
        limit=limit,
        page=page,
        size=size,
        item_status=item_status,
        priority=priority,
        search=search,
        assignee_id=assignee_id,
        sort_by=sort_by,
        order=order,
    )


@work_items_router.get(
    "/{item_id}",
    response_model=WorkItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Chi tiết hạng mục thi công",
    description="Xem chi tiết một hạng mục thi công. Yêu cầu người dùng phải là thành viên của công trình sở hữu hạng mục đó.",
)
@limiter.limit("5/minute")
def handle_get_work_item(
    request: Request,
    item_id: Annotated[int, Path(..., description="ID hạng mục thi công")],
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(
            WorkItemPermissionChecker(
                [RoleSiteMemberEnum.OWNER, RoleSiteMemberEnum.MEMBER]
            )
        ),
    ],
):
    return WorkItemService.get_work_item(db, item_id)


@work_items_router.patch(
    "/{item_id}",
    response_model=WorkItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật hạng mục thi công",
    description="Cập nhật thông tin hạng mục thi công. OWNER được sửa tất cả các trường; Assignee (Member) chỉ được phép cập nhật trạng thái (status).",
)
@limiter.limit("5/minute")
def handle_update_work_item(
    request: Request,
    item_id: Annotated[int, Path(..., description="ID hạng mục thi công")],
    work_item_data: WorkItemUpdate,
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(
            WorkItemPermissionChecker(
                [RoleSiteMemberEnum.OWNER, RoleSiteMemberEnum.MEMBER]
            )
        ),
    ],
):
    return WorkItemService.update_work_item(
        db, item_id, work_item_data, site_member.user_id
    )


@work_items_router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa hạng mục thi công",
    description="Xóa hạng mục thi công. Chỉ OWNER của công trình mới có quyền xóa.",
)
@limiter.limit("5/minute")
def handle_delete_work_item(
    request: Request,
    item_id: Annotated[int, Path(..., description="ID hạng mục thi công")],
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(WorkItemPermissionChecker([RoleSiteMemberEnum.OWNER])),
    ],
):
    WorkItemService.delete_work_item(db, item_id, site_member.user_id)


@work_items_router.post(
    "/{item_id}/comments",
    response_model=WorkItemCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Thêm comment (ghi chú nhật ký thi công)",
    description="Thêm bình luận / ghi chú tiến độ cho hạng mục thi công. Chỉ thành viên công trình mới có quyền bình luận.",
)
@limiter.limit("5/minute")
def handle_create_work_item_comment(
    request: Request,
    item_id: Annotated[int, Path(..., description="ID hạng mục thi công")],
    comment_data: WorkItemCommentCreate,
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(
            WorkItemPermissionChecker(
                [RoleSiteMemberEnum.OWNER, RoleSiteMemberEnum.MEMBER]
            )
        ),
    ],
):
    return WorkItemService.create_work_item_comment(
        db, item_id, site_member.user_id, comment_data
    )


@work_items_router.get(
    "/{item_id}/comments",
    response_model=list[WorkItemCommentResponse],
    status_code=status.HTTP_200_OK,
    summary="Danh sách comment của hạng mục",
    description="Lấy danh sách các bình luận / ghi chú trong hạng mục thi công.",
)
@limiter.limit("5/minute")
def handle_get_work_item_comments(
    request: Request,
    item_id: Annotated[int, Path(..., description="ID hạng mục thi công")],
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(
            WorkItemPermissionChecker(
                [RoleSiteMemberEnum.OWNER, RoleSiteMemberEnum.MEMBER]
            )
        ),
    ],
    skip: Annotated[int, Query(ge=0, description="Số lượng bản ghi bỏ qua")] = 0,
    limit: Annotated[int, Query(gt=0, description="Số lượng bản ghi tối đa")] = 20,
):
    return WorkItemService.get_work_item_comments(db, item_id, skip, limit)


@work_items_router.post(
    "/{item_id}/attachments",
    response_model=WorkItemAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tải lên file đính kèm (hình ảnh/biên bản nghiệm thu)",
    description="Tải lên file đính kèm cho hạng mục thi công (JPEG, PNG, PDF; dung lượng tối đa 10MB). Chỉ thành viên công trình có quyền upload.",
)
@limiter.limit("5/minute")
def handle_upload_work_item_attachment(
    request: Request,
    item_id: Annotated[int, Path(..., description="ID hạng mục thi công")],
    file: Annotated[UploadFile, File(..., description="File đính kèm (JPG, PNG, PDF)")],
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(
            WorkItemPermissionChecker(
                [RoleSiteMemberEnum.OWNER, RoleSiteMemberEnum.MEMBER]
            )
        ),
    ],
):
    return WorkItemService.upload_work_item_attachment(
        db, item_id, site_member.user_id, file
    )


@work_items_router.get(
    "/{item_id}/attachments",
    response_model=list[WorkItemAttachmentResponse],
    status_code=status.HTTP_200_OK,
    summary="Danh sách file đính kèm của hạng mục",
    description="Xem danh sách tất cả các file đã upload đính kèm trong hạng mục thi công.",
)
@limiter.limit("5/minute")
def handle_get_work_item_attachments(
    request: Request,
    item_id: Annotated[int, Path(..., description="ID hạng mục thi công")],
    db: Annotated[Session, Depends(get_db)],
    site_member: Annotated[
        SiteMemberModel,
        Depends(
            WorkItemPermissionChecker(
                [RoleSiteMemberEnum.OWNER, RoleSiteMemberEnum.MEMBER]
            )
        ),
    ],
):
    return WorkItemService.get_work_item_attachments(db, item_id)
