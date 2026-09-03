from sqlalchemy.orm import Session

from ..core.exception import (
    AppException,
    BadRequestException,
    InternalServerErrorException,
    UnauthorizedException,
)
from ..core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from ..models import UserModel
from ..schemas import TokenResponse, UserCreate, UserLogin, UserResponse


class AuthService:
    @staticmethod
    async def register_handle(data: UserCreate, db: Session) -> UserResponse:
        try:
            db_user = db.query(UserModel).filter(UserModel.email == data.email).first()
            if db_user:
                raise BadRequestException("Email already exists")

            new_user = UserModel(
                full_name=data.full_name,
                email=data.email,
                password_hash=get_password_hash(data.password),
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return UserResponse.model_validate(new_user)
        except AppException:
            raise
        except Exception as err:
            raise InternalServerErrorException("Internal server error") from err

    @staticmethod
    async def login(data: UserLogin, db: Session) -> TokenResponse:
        try:
            db_user = db.query(UserModel).filter(UserModel.email == data.email).first()
            if not db_user:
                raise BadRequestException("Email not found")

            if not verify_password(data.password, db_user.password_hash):
                raise BadRequestException("Invalid password")

            payload = {"sub": str(db_user.id)}
            access_token = create_access_token(payload)
            refresh_token = create_refresh_token(payload)

            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
            )
        except AppException:
            raise
        except Exception as err:
            raise InternalServerErrorException("Internal server error") from err

    @staticmethod
    async def refresh_token(refresh_token: str, db: Session) -> TokenResponse:
        try:
            payload = verify_token(refresh_token, expected_type="refresh")
            user_id_str: str | None = payload.get("sub")
            if user_id_str is None:
                raise UnauthorizedException("Could not validate credentials")

            user_id = int(user_id_str)
            db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if db_user is None or not db_user.is_active:
                raise UnauthorizedException("User not found or inactive")

            new_payload = {"sub": str(db_user.id)}
            return TokenResponse(
                access_token=create_access_token(new_payload),
                refresh_token=create_refresh_token(new_payload),
                token_type="bearer",
            )
        except AppException:
            raise
        except Exception as e:
            raise UnauthorizedException(f"Could not validate credentials: {e!s}") from e
