import os
import sys

# Set environment variables for testing before importing application modules
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-construction-site-management-123456"
os.environ["DB_TYPE"] = "sqlite"
os.environ["DB_NAME"] = "test_construction"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from collections.abc import Generator

import app.models
import pytest
from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import create_access_token, create_refresh_token
from app.db.database import Base, get_db
from app.models.sites import ConstructionSiteModel
from app.models.users import UserModel
from app.models.work_items import WorkItemModel
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from tests.seed import seed_data

# Ensure settings have test key
settings.JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
settings.DB_TYPE = "sqlite"
settings.DB_NAME = "test_construction"


@pytest.fixture(scope="session", autouse=True)
def disable_limiter():
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture(scope="function")
def db_session() -> Generator[Session]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
    )
    session = TestingSessionLocal()
    seed_data(session)
    session.commit()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient]:
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(db_session: Session) -> UserModel:
    return (
        db_session.query(UserModel)
        .filter(UserModel.email == "admin@example.com")
        .first()
    )


@pytest.fixture(scope="function")
def user_1(db_session: Session) -> UserModel:
    return (
        db_session.query(UserModel)
        .filter(UserModel.email == "nguyenvana@example.com")
        .first()
    )


@pytest.fixture(scope="function")
def user_2(db_session: Session) -> UserModel:
    return (
        db_session.query(UserModel)
        .filter(UserModel.email == "tranthib@example.com")
        .first()
    )


@pytest.fixture(scope="function")
def site_1(db_session: Session) -> ConstructionSiteModel:
    return (
        db_session.query(ConstructionSiteModel)
        .filter(ConstructionSiteModel.name == "Tòa nhà văn phòng Hưng Phát")
        .first()
    )


@pytest.fixture(scope="function")
def site_2(db_session: Session) -> ConstructionSiteModel:
    return (
        db_session.query(ConstructionSiteModel)
        .filter(ConstructionSiteModel.name == "Khu dân cư Green City")
        .first()
    )


@pytest.fixture(scope="function")
def work_item_1(db_session: Session) -> WorkItemModel:
    return (
        db_session.query(WorkItemModel)
        .filter(WorkItemModel.title == "Đào móng tòa nhà")
        .first()
    )


@pytest.fixture(scope="function")
def work_item_2(db_session: Session) -> WorkItemModel:
    return (
        db_session.query(WorkItemModel)
        .filter(WorkItemModel.title == "Đổ bê tông sàn tầng 1")
        .first()
    )


@pytest.fixture(scope="function")
def work_item_3(db_session: Session) -> WorkItemModel:
    return (
        db_session.query(WorkItemModel)
        .filter(WorkItemModel.title == "Khảo sát địa hình")
        .first()
    )


@pytest.fixture(scope="function")
def admin_token(admin_user: UserModel) -> str:
    return create_access_token({"sub": str(admin_user.id)})


@pytest.fixture(scope="function")
def user1_token(user_1: UserModel) -> str:
    return create_access_token({"sub": str(user_1.id)})


@pytest.fixture(scope="function")
def user2_token(user_2: UserModel) -> str:
    return create_access_token({"sub": str(user_2.id)})


@pytest.fixture(scope="function")
def admin_refresh_token(admin_user: UserModel) -> str:
    return create_refresh_token({"sub": str(admin_user.id)})


@pytest.fixture(scope="function")
def user1_refresh_token(user_1: UserModel) -> str:
    return create_refresh_token({"sub": str(user_1.id)})


@pytest.fixture(scope="function")
def user2_refresh_token(user_2: UserModel) -> str:
    return create_refresh_token({"sub": str(user_2.id)})


@pytest.fixture(scope="function")
def admin_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def user1_headers(user1_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user1_token}"}


@pytest.fixture(scope="function")
def user2_headers(user2_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {user2_token}"}
