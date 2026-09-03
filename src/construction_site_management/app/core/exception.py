from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .logger import setup_logger


class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        details: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        super().__init__(status_code=status_code, detail=message, headers=headers)
        self.error_code = error_code
        self.message = message
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        response = {
            "status_code": self.status_code,
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.details is not None:
            response["details"] = self.details
        return response


class BadRequestException(AppException):
    """400 - Bad Request: Request không hợp lệ hoặc sai định dạng."""

    def __init__(self, message: str = "Bad Request", details: Any | None = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BAD_REQUEST",
            message=message,
            details=details,
        )


class UnauthorizedException(AppException):
    """401 - Unauthorized: Thiếu hoặc sai token xác thực."""

    def __init__(
        self,
        message: str = "Unauthorized",
        details: Any | None = None,
        headers: dict[str, str] | None = None,
    ):
        if headers is None:
            headers = {"WWW-Authenticate": "Bearer"}
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            message=message,
            details=details,
            headers=headers,
        )


class ForbiddenException(AppException):
    """403 - Forbidden: Đã xác thực nhưng không có quyền truy cập."""

    def __init__(self, message: str = "Forbidden", details: Any | None = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN",
            message=message,
            details=details,
        )


class NotFoundException(AppException):
    """404 - Not Found: Không tìm thấy tài nguyên."""

    def __init__(self, message: str = "Resource Not Found", details: Any | None = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="NOT_FOUND",
            message=message,
            details=details,
        )


class MethodNotAllowedException(AppException):
    """405 - Method Not Allowed: HTTP Method không được hỗ trợ cho route này."""

    def __init__(self, message: str = "Method Not Allowed", details: Any | None = None):
        super().__init__(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            error_code="METHOD_NOT_ALLOWED",
            message=message,
            details=details,
        )


class ConflictException(AppException):
    """409 - Conflict: Xung đột dữ liệu (ví dụ: duplicate unique key)."""

    def __init__(self, message: str = "Resource Conflict", details: Any | None = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT",
            message=message,
            details=details,
        )


class ValidationException(AppException):
    """422 - Unprocessable Entity: Dữ liệu gửi lên đúng định dạng nhưng sai logic."""

    def __init__(self, message: str = "Validation Error", details: Any | None = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            error_code="VALIDATION_ERROR",
            message=message,
            details=details,
        )


class TooManyRequestsException(AppException):
    """429 - Too Many Requests: Request vượt quá giới hạn (Rate limiting)."""

    def __init__(self, message: str = "Too Many Requests", details: Any | None = None):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="TOO_MANY_REQUESTS",
            message=message,
            details=details,
        )


class InternalServerErrorException(AppException):
    """500 - Internal Server Error: Lỗi không mong muốn trong quá trình xử lý."""

    def __init__(
        self, message: str = "Internal Server Error", details: Any | None = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERNAL_SERVER_ERROR",
            message=message,
            details=details,
        )


class ServiceUnavailableException(AppException):
    """503 - Service Unavailable: Máy chủ tạm thời không thể xử lý yêu cầu."""

    def __init__(
        self, message: str = "Service Unavailable", details: Any | None = None
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code="SERVICE_UNAVAILABLE",
            message=message,
            details=details,
        )


logger = setup_logger("ExceptionHandler")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    logger.warning(
        f"AppException: {exc.error_code} - {exc.message} - Path: {request.url.path}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    logger.warning(f"ValidationException on path {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "error_code": "VALIDATION_ERROR",
            "message": "Dữ liệu không hợp lệ",
            "details": jsonable_encoder(exc.errors()),
        },
    )


async def starlette_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    logger.error(
        f"StarletteHTTPException: Status {exc.status_code} - {exc.detail} "
        f"- Path: {request.url.path}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error_code": "HTTP_ERROR",
            "message": exc.detail,
        },
        headers=getattr(exc, "headers", None),
    )


class JWTTokenError(UnauthorizedException):
    def __init__(self, message: str = "JWT token error", details: Any | None = None):
        super().__init__(message=message, details=details)


class JWTTokenDecodeError(JWTTokenError):
    def __init__(
        self, message: str = "JWT token decode error", details: Any | None = None
    ):
        super().__init__(message=message, details=details)


class JWTTokenExpiredError(JWTTokenError):
    def __init__(
        self, message: str = "JWT token has expired", details: Any | None = None
    ):
        super().__init__(message=message, details=details)
