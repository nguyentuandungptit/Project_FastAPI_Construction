from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Boolean, DateTime, Enum, Integer, String, Text

from ..db.database import Base

if TYPE_CHECKING:
    from .users import UserModel
    from .work_items import WorkItemModel


class RoleSiteMemberEnum(enum.Enum):
    OWNER = "owner"
    MEMBER = "member"


class SiteMemberModel(Base):
    __tablename__ = "site_members"

    site_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("construction_sites.id"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), primary_key=True
    )
    role: Mapped[RoleSiteMemberEnum] = mapped_column(
        Enum(RoleSiteMemberEnum), nullable=False, default=RoleSiteMemberEnum.MEMBER
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    site: Mapped[ConstructionSiteModel] = relationship(back_populates="members")
    user: Mapped[UserModel] = relationship(back_populates="site_memberships")


class ConstructionSiteModel(Base):
    __tablename__ = "construction_sites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    owner: Mapped[UserModel] = relationship(back_populates="owned_sites")

    members: Mapped[list[SiteMemberModel]] = relationship(
        back_populates="site", cascade="all, delete-orphan"
    )
    work_items: Mapped[list[WorkItemModel]] = relationship(
        back_populates="site", cascade="all, delete-orphan"
    )
