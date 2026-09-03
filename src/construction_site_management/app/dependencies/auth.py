from typing import Annotated

from fastapi import Depends, Path
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ..core.exception import (
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
)
from ..core.security import verify_token
from ..db.database import get_db
from ..models import (
    ConstructionSiteModel,
    RoleSiteMemberEnum,
    RoleUserEnum,
    SiteMemberModel,
    UserModel,
    WorkItemModel,
)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(HTTPBearer())],
    db: Annotated[Session, Depends(get_db)],
) -> UserModel:
    try:
        token = credentials.credentials
        payload = verify_token(token, expected_type="access")
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise UnauthorizedException("Could not validate credentials")

        user_id = int(user_id_str)
    except Exception as e:
        raise UnauthorizedException(f"Could not validate credentials: {e!s}") from e

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        raise UnauthorizedException("User not found")

    if not user.is_active:
        raise UnauthorizedException("Inactive user")

    return user


def get_current_active_user(
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> UserModel:
    if not current_user.is_active:
        raise UnauthorizedException("Inactive user")
    return current_user


class RoleUserChecker:
    def __init__(self, allowed_roles: list[RoleUserEnum]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        user: Annotated[UserModel, Depends(get_current_user)],
    ) -> None:
        if user.role not in self.allowed_roles:
            raise ForbiddenException("Operation not permitted")


class RoleSiteMemberChecker:
    def __init__(self, allowed_roles: list[RoleSiteMemberEnum]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        site_id: Annotated[int, Path(...)],
        user: Annotated[UserModel, Depends(get_current_active_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> SiteMemberModel:
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

        site_member = (
            db.query(SiteMemberModel)
            .filter(
                SiteMemberModel.site_id == site_id, SiteMemberModel.user_id == user.id
            )
            .first()
        )

        if not site_member:
            raise ForbiddenException("User is not a member of this site")

        if site_member.role not in self.allowed_roles:
            raise ForbiddenException("Operation not permitted for this site role")

        return site_member


class WorkItemPermissionChecker:
    def __init__(self, allowed_roles: list[RoleSiteMemberEnum]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        item_id: Annotated[int, Path(...)],
        user: Annotated[UserModel, Depends(get_current_active_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> SiteMemberModel:
        work_item = db.query(WorkItemModel).filter(WorkItemModel.id == item_id).first()
        if not work_item:
            raise NotFoundException("Work item not found")

        site = (
            db.query(ConstructionSiteModel)
            .filter(
                ConstructionSiteModel.id == work_item.site_id,
                ConstructionSiteModel.is_deleted.is_(False),
            )
            .first()
        )
        if not site:
            raise NotFoundException("Site not found")

        site_member = (
            db.query(SiteMemberModel)
            .filter(
                SiteMemberModel.site_id == work_item.site_id,
                SiteMemberModel.user_id == user.id,
            )
            .first()
        )

        if not site_member:
            raise ForbiddenException("User is not a member of this site")

        if site_member.role not in self.allowed_roles:
            raise ForbiddenException("Operation not permitted for this site role")

        return site_member
