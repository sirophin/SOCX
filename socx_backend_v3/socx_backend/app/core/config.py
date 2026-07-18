"""
Application settings, loaded from environment variables / .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://socx:socx@localhost:5432/socx"
    SQL_ECHO: bool = False

    # Auth
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    JWT_ISSUER: str = "socx-api"

    # Uploads
    MAX_UPLOAD_SIZE_MB: int = 100
    UPLOAD_DIR: str = "uploads"

    # CORS
    FRONTEND_ORIGIN: str = "http://localhost:5173"


settings = Settings()
