from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..core.exception import (
    AppException,
    BadRequestException,
    InternalServerErrorException,
)
from ..models import UserModel


class UserService:
    @staticmethod
    def get_all_users(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        page: int | None = None,
        size: int | None = None,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> list[UserModel]:
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

            query = db.query(UserModel)
            if search is not None and search.strip():
                term = f"%{search.strip()}%"
                query = query.filter(
                    or_(UserModel.full_name.ilike(term), UserModel.email.ilike(term))
                )
            if is_active is not None:
                query = query.filter(UserModel.is_active == is_active)

            return query.offset(skip).limit(limit).all()
        except AppException:
            raise
        except Exception as err:
            raise InternalServerErrorException("Internal server error") from err

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> UserModel:
        try:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if not user:
                raise BadRequestException("User not found")
            return user
        except AppException:
            raise
        except Exception as err:
            raise InternalServerErrorException("Internal server error") from err
