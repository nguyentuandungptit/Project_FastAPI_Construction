from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError

from .config import settings
from .exception import (
    JWTTokenDecodeError,
    JWTTokenError,
    JWTTokenExpiredError,
    UnauthorizedException,
)

pwd_hasher = PasswordHasher(encoding="utf-8", type=Type.ID)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_hasher.verify(hashed_password, plain_password)
    except VerifyMismatchError as err:
        raise UnauthorizedException("Invalid password") from err


def get_password_hash(password: str) -> str:
    return pwd_hasher.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAY
        )
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    return jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )


def verify_token(token: str, expected_type: str | None = None):
    try:
        payload = decode_token(token)
        if expected_type and payload.get("type") != expected_type:
            raise JWTTokenError("Invalid token type")
        return payload
    except jwt.exceptions.DecodeError as err:
        raise JWTTokenDecodeError("JWT token decode error") from err
    except jwt.exceptions.ExpiredSignatureError as err:
        raise JWTTokenExpiredError("JWT token has expired") from err
    except jwt.exceptions.InvalidTokenError as err:
        raise JWTTokenError("JWT token error") from err
    except jwt.exceptions.PyJWKError as err:
        raise JWTTokenError("JWT token error") from err
