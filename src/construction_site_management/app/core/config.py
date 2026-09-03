import os

from dotenv import load_dotenv


class SettingsError(Exception):
    pass


load_dotenv()


class Settings:
    def __init__(self):
        # Database
        self.DB_TYPE: str = os.getenv("DB_TYPE", "sqlite")
        self.DB_USER: str = os.getenv("DB_USER")
        self.DB_PASSWORD: str = os.getenv("DB_PASSWORD")
        self.DB_HOST: str = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        self.DB_PORT: int | None = int(db_port) if db_port else None
        self.DB_NAME: str = os.getenv("DB_NAME", "construction")
        # JWT
        self.JWT_SECRET_KEY: str = os.getenv(
            "JWT_SECRET_KEY", "default-jwt-secret-key-for-construction-site-management"
        )
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
        jwt_access = os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
        self.JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = (
            int(jwt_access) if jwt_access else 30
        )
        jwt_refresh = os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAY")
        self.JWT_REFRESH_TOKEN_EXPIRE_DAY: int = int(jwt_refresh) if jwt_refresh else 7
        # Server
        self.SV_HOST: str = os.getenv("SV_HOST") or "127.0.0.1"
        sv_port = os.getenv("SV_PORT")
        self.SV_PORT: int = int(sv_port) if sv_port else 8000
        # Other
        self.CORS_ORIGINS: list[str] = [
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "*").split(",")
            if origin.strip()
        ]
        self.DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    def validate(self):
        required_vars = ["DB_TYPE", "DB_NAME"]
        if self.DB_TYPE in ["mysql", "postgresql"]:
            required_vars.extend(["DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD"])

        missing_vars = [var for var in required_vars if not getattr(self, var)]
        if missing_vars:
            raise SettingsError(
                f"Missing required environment variables: {', '.join(missing_vars)}"
            )

    @property
    def database_url(self) -> str:
        if self.DB_TYPE == "sqlite":
            if self.DB_PASSWORD:
                return f"sqlite+pysqlcipher://:{self.DB_PASSWORD}@/{self.DB_NAME}.db"
            return f"sqlite+pysqlite:///./{self.DB_NAME}.db"
        if self.DB_TYPE == "mysql":
            return (
                f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        if self.DB_TYPE == "postgresql":
            return (
                f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
                f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        raise ValueError(f"Unsupported database type: {self.DB_TYPE}")


settings = Settings()
