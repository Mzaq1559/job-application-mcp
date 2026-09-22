"""Application configuration, loaded from environment variables / .env.

Nothing here is hard-coded personal data — profile/resume content lives in the
database, not in source control. See .env.example for every variable this
project reads.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/app.db", alias="DATABASE_URL"
    )

    mcp_host: str = Field(default="0.0.0.0", alias="MCP_HOST")
    mcp_port: int = Field(default=8000, alias="MCP_PORT")

    # Comma-separated bearer tokens accepted on the remote MCP endpoint.
    mcp_auth_tokens: str = Field(default="", alias="MCP_AUTH_TOKENS")

    ai_provider: str = Field(default="anthropic", alias="AI_PROVIDER")
    ai_api_key: str = Field(default="", alias="AI_API_KEY")
    ai_model: str = Field(default="claude-sonnet-4-6", alias="AI_MODEL")

    upload_dir: str = Field(default="./uploads", alias="UPLOAD_DIR")
    max_upload_size_mb: int = Field(default=10, alias="MAX_UPLOAD_SIZE_MB")

    @property
    def auth_tokens(self) -> set[str]:
        return {t.strip() for t in self.mcp_auth_tokens.split(",") if t.strip()}

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
