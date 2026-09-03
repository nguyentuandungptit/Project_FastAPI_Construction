from collections.abc import Generator

from sqlalchemy import Engine as SqlAlchemyEngine
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ..core.config import settings

engine: SqlAlchemyEngine = create_engine(
    settings.database_url,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False}
    if "sqlite" in settings.database_url
    else {},
)
Engine = engine  # Backward-compatibility alias

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
