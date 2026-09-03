import os
import shutil
import uuid
from datetime import UTC, datetime

from fastapi import UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..core.exception import (
    AppException,
    BadRequestException,
    ForbiddenException,
    InternalServerErrorException,
    NotFoundException,
)
from ..models import (
    ConstructionSiteModel,
    RoleSiteMemberEnum,
    SiteMemberModel,
    UserModel,
    WorkItemAttachmentModel,
    WorkItemCommentModel,
    WorkItemModel,
)
from ..models.activity_logs import ActivityActionEnum
from ..models.work_items import PriorityEnum, WorkStatusEnum
from ..schemas import (
    ConstructionSiteCreate,
    ConstructionSiteUpdate,
    SiteMemberCreate,
    WorkItemCommentCreate,
    WorkItemCreate,
    WorkItemUpdate,
)
from .activity_logs import ActivityLogService


class ConstructionSiteService:
    @staticmethod
    def get_construction_sites_by_user(
        db: Session,
        user: UserModel,
        skip: int = 0,
        limit: int = 100,
        page: int | None = None,
        size: int | None = None,
        search: str | None = None,
    ) -> list[ConstructionSiteModel]:
        try:
            if page is not None:
                if page < 1:
                    raise BadRequestException("Page must be greater than or equal to 1")
                page_size = size if size is not None else limit
                if page_size <= 0:
                    raise BadRequestException("Size must be greater than 0")
                skip = (page - 1) * page_size
                limit = page_size
            elif size is not None:
                if size <= 0:
                    raise BadRequestException("Size must be greater than 0")
                limit = size

            if skip < 0:
                raise BadRequestException("Skip must be non-negative")
            if limit <= 0:
                raise BadRequestException("Limit must be greater than 0")

            query = db.query(ConstructionSiteModel).filter(
                ConstructionSiteModel.is_deleted.is_(False),
                or_(
                    ConstructionSiteModel.owner_id == user.id,
                    ConstructionSiteModel.members.any(
                        SiteMemberModel.user_id == user.id
                    ),
                ),
            )

            if search is not None and search.strip():
                query = query.filter(
                    ConstructionSiteModel.name.ilike(f"%{search.strip()}%")
                )

            return (
                query.order_by(ConstructionSiteModel.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except AppException:
            raise
        except Exception as e:
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def create_construction_site(
        db: Session, construction_site: ConstructionSiteCreate, user: UserModel
    ) -> ConstructionSiteModel:
        try:
            db_construction_site = ConstructionSiteModel(
                **construction_site.model_dump()
            )
            db_construction_site.owner_id = user.id
            db.add(db_construction_site)
            db.commit()
            db.refresh(db_construction_site)

            member = SiteMemberModel(
                site_id=db_construction_site.id,
                user_id=user.id,
                role=RoleSiteMemberEnum.OWNER,
            )
            db.add(member)
            db.commit()

            ActivityLogService.log_activity(
                db=db,
                site_id=db_construction_site.id,
                user_id=user.id,
                action=ActivityActionEnum.CREATE_SITE,
                details=f"Created site {db_construction_site.name}",
            )

            return db_construction_site
        except AppException:
            raise
        except Exception as e:
            db.rollback()
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def get_construction_site(db: Session, site_id: int) -> ConstructionSiteModel:
        try:
            site = (
                db.query(ConstructionSiteModel)
                .filter(
                    ConstructionSiteModel.id == site_id,
                    ConstructionSiteModel.is_deleted.is_(False),
                )
                .first()
            )
            if not site:
                raise NotFoundException("Site not found")
            return site
        except AppException:
            raise
        except Exception as e:
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def update_construction_site(
        db: Session, site_id: int, site_data: ConstructionSiteUpdate, actor_id: int
    ) -> ConstructionSiteModel:
        try:
            site = ConstructionSiteService.get_construction_site(db, site_id)
            update_data = site_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(site, key, value)

            db.commit()
            db.refresh(site)

            ActivityLogService.log_activity(
                db=db,
                site_id=site.id,
                user_id=actor_id,
                action=ActivityActionEnum.UPDATE_SITE,
                details=f"Updated site properties: {', '.join(update_data.keys())}",
            )

            return site
        except AppException:
            raise
        except Exception as e:
            db.rollback()
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def delete_construction_site(
        db: Session, site_id: int, actor_id: int
    ) -> dict[str, str]:
        try:
            site = ConstructionSiteService.get_construction_site(db, site_id)
            site.is_deleted = True
            site.deleted_at = datetime.now(UTC)
            db.commit()

            ActivityLogService.log_activity(
                db=db,
                site_id=site_id,
                user_id=actor_id,
                action=ActivityActionEnum.DELETE_SITE,
                details=f"Deleted site: {site.name}",
            )
            return {"detail": "Site deleted"}
        except AppException:
            raise
        except Exception as e:
            db.rollback()
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def add_member(
        db: Session, site_id: int, member_data: SiteMemberCreate, actor_id: int
    ) -> SiteMemberModel:
        try:
            user = (
                db.query(UserModel).filter(UserModel.id == member_data.user_id).first()
            )
            if not user:
                raise NotFoundException("User not found")
            existing = (
                db.query(SiteMemberModel)
                .filter(
                    SiteMemberModel.site_id == site_id,
                    SiteMemberModel.user_id == member_data.user_id,
                )
                .first()
            )
            if existing:
                raise BadRequestException("User is already a member of this site")
            member = SiteMemberModel(**member_data.model_dump(exclude={"site_id"}))
            member.site_id = site_id
            db.add(member)
            db.commit()
            db.refresh(member)

            role_val = member_data.role.value
            ActivityLogService.log_activity(
                db=db,
                site_id=site_id,
                user_id=actor_id,
                action=ActivityActionEnum.ADD_MEMBER,
                details=f"Added user_id {member_data.user_id} as {role_val}",
            )

            return member
        except AppException:
            raise
        except Exception as e:
            db.rollback()
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def get_members(db: Session, site_id: int) -> list[SiteMemberModel]:
        try:
            return (
                db.query(SiteMemberModel)
                .filter(SiteMemberModel.site_id == site_id)
                .all()
            )
        except AppException:
            raise
        except Exception as e:
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def remove_member(
        db: Session, site_id: int, user_id: int, actor_id: int
    ) -> dict[str, str]:
        try:
            member = (
                db.query(SiteMemberModel)
                .filter(
                    SiteMemberModel.site_id == site_id,
                    SiteMemberModel.user_id == user_id,
                )
                .first()
            )
            if not member:
                raise NotFoundException("Member not found")
            if member.role == RoleSiteMemberEnum.OWNER:
                raise BadRequestException("Cannot remove the owner from the site")
            db.delete(member)
            db.commit()

            ActivityLogService.log_activity(
                db=db,
                site_id=site_id,
                user_id=actor_id,
                action=ActivityActionEnum.REMOVE_MEMBER,
                details=f"Removed user_id {user_id} from site",
            )

            return {"detail": "Member removed"}
        except AppException:
            raise
        except Exception as e:
            db.rollback()
            raise InternalServerErrorException(str(e)) from e


class WorkItemService:
    @staticmethod
    def create_work_item(
        db: Session, site_id: int, work_item_data: WorkItemCreate, actor_id: int
    ) -> WorkItemModel:
        try:
            ConstructionSiteService.get_construction_site(db, site_id)
            if work_item_data.assignee_id is not None:
                member = (
                    db.query(SiteMemberModel)
                    .filter(
                        SiteMemberModel.site_id == site_id,
                        SiteMemberModel.user_id == work_item_data.assignee_id,
                    )
                    .first()
                )
                if not member:
                    raise BadRequestException(
                        "Assignee must be a member of this construction site"
                    )

            work_item_dict = work_item_data.model_dump(exclude={"site_id"})
            work_item = WorkItemModel(**work_item_dict)
            work_item.site_id = site_id
            db.add(work_item)
            db.commit()
            db.refresh(work_item)

            ActivityLogService.log_activity(
                db=db,
                site_id=site_id,
                user_id=actor_id,
                action=ActivityActionEnum.CREATE_WORK_ITEM,
                details=f"Created work item: {work_item.title}",
            )
            return work_item
        except AppException:
            raise
        except Exception as e:
            db.rollback()
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def get_work_items(
        db: Session,
        site_id: int,
        skip: int = 0,
        limit: int = 20,
        page: int | None = None,
        size: int | None = None,
        item_status: WorkStatusEnum | None = None,
        priority: PriorityEnum | None = None,
        search: str | None = None,
        assignee_id: int | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> list[WorkItemModel]:
        try:
            ConstructionSiteService.get_construction_site(db, site_id)

            if page is not None:
                if page < 1:
                    raise BadRequestException("Page must be greater than or equal to 1")
                page_size = size if size is not None else limit
                if page_size <= 0:
                    raise BadRequestException("Size must be greater than 0")
                skip = (page - 1) * page_size
                limit = page_size
            elif size is not None:
                if size <= 0:
                    raise BadRequestException("Size must be greater than 0")
                limit = size

            if skip < 0:
                raise BadRequestException("Skip must be non-negative")
            if limit <= 0:
                raise BadRequestException("Limit must be greater than 0")

            query = db.query(WorkItemModel).filter(WorkItemModel.site_id == site_id)

            if item_status is not None:
                query = query.filter(WorkItemModel.status == item_status)
            if priority is not None:
                query = query.filter(WorkItemModel.priority == priority)
            if assignee_id is not None:
                query = query.filter(WorkItemModel.assignee_id == assignee_id)
            if search is not None and search.strip():
                query = query.filter(WorkItemModel.title.ilike(f"%{search.strip()}%"))

            allowed_sort_fields = {
                "created_at": WorkItemModel.created_at,
                "due_date": WorkItemModel.due_date,
                "id": WorkItemModel.id,
                "title": WorkItemModel.title,
                "priority": WorkItemModel.priority,
                "status": WorkItemModel.status,
            }

            sort_by_lower = sort_by.lower()
            if sort_by_lower not in allowed_sort_fields:
                raise BadRequestException(
                    f"Invalid sort_by field: {sort_by}. Allowed: {list(allowed_sort_fields.keys())}"
                )

            order_lower = order.lower()
            if order_lower not in ["asc", "desc"]:
                raise BadRequestException("Order must be 'asc' or 'desc'")

            sort_column = allowed_sort_fields[sort_by_lower]
            if sort_by_lower == "due_date":
                if order_lower == "asc":
                    query = query.order_by(sort_column.asc().nulls_last())
                else:
                    query = query.order_by(sort_column.desc().nulls_last())
            else:
                if order_lower == "asc":
                    query = query.order_by(sort_column.asc())
                else:
                    query = query.order_by(sort_column.desc())

            return query.offset(skip).limit(limit).all()
        except AppException:
            raise
        except Exception as e:
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def get_work_item(db: Session, item_id: int) -> WorkItemModel:
        try:
            work_item = (
                db.query(WorkItemModel).filter(WorkItemModel.id == item_id).first()
            )
            if not work_item:
                raise NotFoundException("Work item not found")
            ConstructionSiteService.get_construction_site(db, work_item.site_id)
            return work_item
        except AppException:
            raise
        except Exception as e:
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def update_work_item(
        db: Session, item_id: int, work_item_data: WorkItemUpdate, actor_id: int
    ) -> WorkItemModel:
        try:
            work_item = WorkItemService.get_work_item(db, item_id)

            site_member = (
                db.query(SiteMemberModel)
                .filter(
                    SiteMemberModel.site_id == work_item.site_id,
                    SiteMemberModel.user_id == actor_id,
                )
                .first()
            )
            if not site_member:
                raise ForbiddenException("User is not a member of this site")

            update_data = work_item_data.model_dump(
                exclude_unset=True, exclude={"site_id"}
            )
            if not update_data:
                return work_item

            if site_member.role == RoleSiteMemberEnum.OWNER:
                if (
                    "assignee_id" in update_data
                    and update_data["assignee_id"] is not None
                ):
                    assignee_member = (
                        db.query(SiteMemberModel)
                        .filter(
                            SiteMemberModel.site_id == work_item.site_id,
                            SiteMemberModel.user_id == update_data["assignee_id"],
                        )
                        .first()
                    )
                    if not assignee_member:
                        raise BadRequestException(
                            "Assignee must be a member of this construction site"
                        )
            elif site_member.role == RoleSiteMemberEnum.MEMBER:
                if work_item.assignee_id != actor_id:
                    raise ForbiddenException(
                        "You do not have permission to update this work item"
                    )

                disallowed_fields = [k for k in update_data if k != "status"]
                if disallowed_fields:
                    raise ForbiddenException(
                        "Assignee is only permitted to update work item status"
                    )
            else:
                raise ForbiddenException("Operation not permitted for this site role")

            for key, value in update_data.items():
                setattr(work_item, key, value)

            db.commit()
            db.refresh(work_item)

            updated_props = ", ".join(update_data.keys())
            ActivityLogService.log_activity(
                db=db,
                site_id=work_item.site_id,
                user_id=actor_id,
                action=ActivityActionEnum.UPDATE_WORK_ITEM,
                details=f"Updated work item properties: {updated_props}",
            )
            return work_item
        except AppException:
            raise
        except Exception as e:
            db.rollback()
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def delete_work_item(db: Session, item_id: int, actor_id: int) -> dict[str, str]:
        try:
            work_item = WorkItemService.get_work_item(db, item_id)
            site_member = (
                db.query(SiteMemberModel)
                .filter(
                    SiteMemberModel.site_id == work_item.site_id,
                    SiteMemberModel.user_id == actor_id,
                )
                .first()
            )
            if not site_member or site_member.role != RoleSiteMemberEnum.OWNER:
                raise ForbiddenException("Only the site owner can delete work items")

            site_id = work_item.site_id
            db.delete(work_item)
            db.commit()

            ActivityLogService.log_activity(
                db=db,
                site_id=site_id,
                user_id=actor_id,
                action=ActivityActionEnum.DELETE_WORK_ITEM,
                details=f"Deleted work item {item_id}",
            )
            return {"detail": "Work item deleted"}
        except AppException:
            raise
        except Exception as e:
            db.rollback()
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def create_work_item_comment(
        db: Session, item_id: int, user_id: int, comment_data: WorkItemCommentCreate
    ) -> WorkItemCommentModel:
        try:
            work_item = WorkItemService.get_work_item(db, item_id)
            comment = WorkItemCommentModel(
                work_item_id=work_item.id, user_id=user_id, content=comment_data.content
            )
            db.add(comment)
            db.commit()
            db.refresh(comment)
            return comment
        except AppException:
            raise
        except Exception as e:
            db.rollback()
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def get_work_item_comments(
        db: Session, item_id: int, skip: int = 0, limit: int = 100
    ) -> list[WorkItemCommentModel]:
        try:
            WorkItemService.get_work_item(db, item_id)
            return (
                db.query(WorkItemCommentModel)
                .filter(WorkItemCommentModel.work_item_id == item_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except AppException:
            raise
        except Exception as e:
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def upload_work_item_attachment(
        db: Session, item_id: int, uploader_id: int, file: UploadFile
    ) -> WorkItemAttachmentModel:
        try:
            work_item = WorkItemService.get_work_item(db, item_id)
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)

            if file_size > 10 * 1024 * 1024:
                raise BadRequestException("File size exceeds 10MB limit")

            allowed_types = ["image/jpeg", "image/png", "application/pdf"]
            if file.content_type not in allowed_types:
                raise BadRequestException(
                    "Invalid file type. Only JPEG, PNG, and PDF are allowed."
                )

            upload_dir = "uploads/attachments"
            os.makedirs(upload_dir, exist_ok=True)

            ext = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{ext}"
            file_path = os.path.join(upload_dir, unique_filename)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            attachment = WorkItemAttachmentModel(
                work_item_id=work_item.id,
                uploader_id=uploader_id,
                file_name=file.filename,
                file_path=file_path,
                file_type=file.content_type,
                file_size=file_size,
            )
            db.add(attachment)
            db.commit()
            db.refresh(attachment)
            return attachment
        except AppException:
            raise
        except Exception as e:
            db.rollback()
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def get_work_item_attachments(
        db: Session, item_id: int
    ) -> list[WorkItemAttachmentModel]:
        try:
            WorkItemService.get_work_item(db, item_id)
            return (
                db.query(WorkItemAttachmentModel)
                .filter(WorkItemAttachmentModel.work_item_id == item_id)
                .all()
            )
        except AppException:
            raise
        except Exception as e:
            raise InternalServerErrorException(str(e)) from e
