from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime, Enum, Integer, String, Text

from ..db.database import Base

if TYPE_CHECKING:
    from .sites import ConstructionSiteModel
    from .users import UserModel


class PriorityEnum(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class WorkStatusEnum(enum.Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class WorkItemModel(Base):
    __tablename__ = "work_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(Integer, ForeignKey("construction_sites.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignee_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    status: Mapped[WorkStatusEnum] = mapped_column(
        Enum(WorkStatusEnum), nullable=False, default=WorkStatusEnum.TODO
    )
    priority: Mapped[PriorityEnum] = mapped_column(
        Enum(PriorityEnum), nullable=False, default=PriorityEnum.MEDIUM
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    site: Mapped[ConstructionSiteModel] = relationship(back_populates="work_items")
    assignee: Mapped[UserModel] = relationship(back_populates="assigned_work")

    comments: Mapped[list[WorkItemCommentModel]] = relationship(
        back_populates="work_item", cascade="all, delete-orphan"
    )
    attachments: Mapped[list[WorkItemAttachmentModel]] = relationship(
        back_populates="work_item", cascade="all, delete-orphan"
    )


class WorkItemCommentModel(Base):
    __tablename__ = "work_item_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    work_item: Mapped[WorkItemModel] = relationship(back_populates="comments")
    user: Mapped[UserModel] = relationship()


class WorkItemAttachmentModel(Base):
    __tablename__ = "work_item_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    work_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False
    )
    uploader_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    work_item: Mapped[WorkItemModel] = relationship(back_populates="attachments")
    uploader: Mapped[UserModel] = relationship()
