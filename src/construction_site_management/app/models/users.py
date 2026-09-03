from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Boolean, DateTime, Enum, Integer, String

from ..db.database import Base

if TYPE_CHECKING:
    from .sites import ConstructionSiteModel, SiteMemberModel
    from .work_items import WorkItemModel


class RoleUserEnum(enum.Enum):
    USER = "user"
    ADMIN = "admin"
    # DEVELOPER = "dev"


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[RoleUserEnum] = mapped_column(
        Enum(RoleUserEnum), default=RoleUserEnum.USER
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    owned_sites: Mapped[list[ConstructionSiteModel]] = relationship(
        back_populates="owner"
    )
    site_memberships: Mapped[list[SiteMemberModel]] = relationship(
        back_populates="user"
    )
    assigned_work: Mapped[list[WorkItemModel]] = relationship(
        back_populates="assignee"
    )
