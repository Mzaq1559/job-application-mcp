"""Application configuration, loaded from environment variables / .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/app.db",
        alias="DATABASE_URL",
    )
    mcp_host: str = Field(default="0.0.0.0", alias="MCP_HOST")
    mcp_port: int = Field(default=8000, alias="MCP_PORT")
    oauth_issuer_url: str = Field(default="", alias="OAUTH_ISSUER_URL")
    oauth_audience: str = Field(default="", alias="OAUTH_AUDIENCE")
    oauth_resource_url: str = Field(default="", alias="OAUTH_RESOURCE_URL")
    oauth_jwks_url: str = Field(default="", alias="OAUTH_JWKS_URL")
    oauth_required_scope: str = Field(
        default="mcp:access",
        alias="OAUTH_REQUIRED_SCOPE",
    )
    ai_provider: str = Field(default="anthropic", alias="AI_PROVIDER")
    ai_api_key: str = Field(default="", alias="AI_API_KEY")
    ai_model: str = Field(default="claude-sonnet-4-6", alias="AI_MODEL")
    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=10, alias="MAX_UPLOAD_SIZE_MB")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()