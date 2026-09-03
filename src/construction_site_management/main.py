from contextlib import asynccontextmanager

from app.core.config import settings  # type: ignore
from app.core.exception import (  # type: ignore
    AppException,
    TooManyRequestsException,
    app_exception_handler,
    starlette_http_exception_handler,
    validation_exception_handler,
)
from app.core.limiter import limiter  # type: ignore
from app.core.logger import setup_logger  # type: ignore
from app.core.middleware import LoggingMiddleware  # type: ignore
from app.db.database import Base, engine  # type: ignore
from app.models import (  # type: ignore  # noqa: F401 - Register models with Base.metadata for create_all
    ActivityLogModel,
    ConstructionSiteModel,
    SiteMemberModel,
    UserModel,
    WorkItemAttachmentModel,
    WorkItemCommentModel,
    WorkItemModel,
)
from app.routers import (  # type: ignore
    auth_router,
    construction_sites_router,
    users_router,
    work_items_router,
)
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")
    yield
    logger.info("Application shutdown")
    engine.dispose()
    logger.info("Database connection closed")


app = FastAPI(
    title="CONSTRUCTION SITE MANAGEMENT API",
    description="Hệ thống quản lý công trình xây dựng và phân công hạng mục thi công (FastAPI + SQLAlchemy + MySQL/SQLite).",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.add_exception_handler(TooManyRequestsException, _rate_limit_exceeded_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)


@app.get(
    "/health",
    tags=["Health"],
    summary="Kiểm tra trạng thái hệ thống",
    description="Endpoint kiểm tra tình trạng hoạt động của hệ thống (Health Check).",
)
def health_check():
    return {
        "status": "healthy",
        "service": "construction-site-management",
        "version": "1.0.0",
    }


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(construction_sites_router)
app.include_router(work_items_router)


def start():
    import uvicorn

    logger.info(f"Starting server in Address: {settings.SV_HOST}:{settings.SV_PORT}")
    uvicorn.run(
        "construction_site_management.main:app",
        host=settings.SV_HOST,
        port=settings.SV_PORT,
        reload=True,
        access_log=False,
        log_level="CRITICAL",
    )


if __name__ == "__main__":
    start()
