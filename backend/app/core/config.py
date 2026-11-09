"""Application settings, read from environment variables (or a local .env file)."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app import __version__


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "InfraDesk"
    app_version: str = __version__
    # development | production | test
    environment: str = "development"

    # SQLite file by default. The path is relative to the working directory.
    database_url: str = "sqlite:///./data/infradesk.db"

    # Must be provided through the environment. There is deliberately no default.
    secret_key: str = Field(min_length=32)
    access_token_minutes: int = Field(default=60, ge=5, le=1440)
    cookie_name: str = "infradesk_session"
    # Set to true only when the site is served over HTTPS.
    cookie_secure: bool = False

    # Comma separated list of browser origins allowed to call the API with credentials.
    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    @field_validator("secret_key")
    @classmethod
    def _secret_not_placeholder(cls, value: str) -> str:
        if value.lower().startswith("change-me"):
            raise ValueError("SECRET_KEY still has the placeholder value; generate a real one")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
