from sqlalchemy.orm import Session

from ..core.exception import InternalServerErrorException
from ..models import ActivityActionEnum, ActivityLogModel


class ActivityLogService:
    @staticmethod
    def log_activity(
        db: Session,
        site_id: int,
        user_id: int,
        action: ActivityActionEnum,
        details: str | None = None,
    ) -> ActivityLogModel:
        try:
            log = ActivityLogModel(
                site_id=site_id, user_id=user_id, action=action, details=details
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            return log
        except Exception as e:
            db.rollback()
            raise InternalServerErrorException(str(e)) from e

    @staticmethod
    def get_site_activities(
        db: Session, site_id: int, skip: int = 0, limit: int = 100
    ) -> list[ActivityLogModel]:
        try:
            return (
                db.query(ActivityLogModel)
                .filter(ActivityLogModel.site_id == site_id)
                .order_by(ActivityLogModel.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            raise InternalServerErrorException(str(e)) from e
