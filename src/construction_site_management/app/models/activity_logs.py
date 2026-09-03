from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime, Enum, Integer, Text

from ..db.database import Base

if TYPE_CHECKING:
    from .sites import ConstructionSiteModel
    from .users import UserModel


class ActivityActionEnum(enum.Enum):
    CREATE_SITE = "CREATE_SITE"
    UPDATE_SITE = "UPDATE_SITE"
    DELETE_SITE = "DELETE_SITE"
    ADD_MEMBER = "ADD_MEMBER"
    UPDATE_MEMBER = "UPDATE_MEMBER"
    REMOVE_MEMBER = "REMOVE_MEMBER"
    CREATE_WORK_ITEM = "CREATE_WORK_ITEM"
    UPDATE_WORK_ITEM = "UPDATE_WORK_ITEM"
    DELETE_WORK_ITEM = "DELETE_WORK_ITEM"


class ActivityLogModel(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("construction_sites.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[ActivityActionEnum] = mapped_column(
        Enum(ActivityActionEnum), nullable=False
    )
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    site: Mapped[ConstructionSiteModel] = relationship()
    user: Mapped[UserModel] = relationship()
