import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from .logger import setup_logger

logger = setup_logger("LoggingMiddleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        # Request Log
        client_ip = request.client.host if request.client else "Unknown"
        logger.info(
            f"Incoming Request: {request.method} {request.url.path} from {client_ip}"
        )
        try:
            response = await call_next(request)
            # Response Log
            process_time = time.time() - start_time
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"- Status: {response.status_code} - Time: {process_time:.4f}s"
            )
            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request Failed: {request.method} {request.url.path} "
                f"- Exception: {e!s} - Time: {process_time:.4f}s"
            )
            raise
