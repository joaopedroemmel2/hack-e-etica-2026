from functools import lru_cache
from typing import Annotated

from pydantic import Field, model_validator, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "FlowLog AI API"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 3000
    api_prefix: str = "/api"
    database_url: str = (
        "postgresql+asyncpg://flowlog:flowlog_dev_password@localhost:5432/flowlog_db"
    )
    jwt_secret_key: str = Field(default="development-only-secret-change-me-32-chars", min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3001"]
    allowed_hosts: Annotated[list[str], NoDecode] = ["localhost", "127.0.0.1", "testserver"]
    max_body_bytes: int = 1_048_576
    initial_admin_name: str | None = None
    initial_admin_email: str | None = None
    initial_admin_password: str | None = None
    rate_limit_default: str = "100/minute"
    workload_attention_percent: float = 85
    workload_overloaded_percent: float = 100
    workload_critical_percent: float = 130

    @field_validator("api_prefix")
    @classmethod
    def prefix_slash(cls, value: str) -> str:
        return "/" + value.strip("/")

    @field_validator("cors_origins", "allowed_hosts", mode="before")
    @classmethod
    def comma_list(cls, value: object) -> object:
        if isinstance(value, str) and not value.lstrip().startswith("["):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value

    @model_validator(mode="after")
    def secure_runtime_configuration(self) -> "Settings":
        if self.jwt_algorithm != "HS256":
            raise ValueError("JWT_ALGORITHM must be HS256")
        if self.access_token_expire_minutes <= 0 or self.refresh_token_expire_days <= 0:
            raise ValueError("Token expiration values must be positive")
        if not (
            0
            <= self.workload_attention_percent
            < self.workload_overloaded_percent
            < self.workload_critical_percent
        ):
            raise ValueError("Workload thresholds must be strictly increasing")
        if self.app_env.lower() == "production" and self.jwt_secret_key.startswith(
            "development-only-"
        ):
            raise ValueError("JWT_SECRET_KEY must be explicitly configured in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
