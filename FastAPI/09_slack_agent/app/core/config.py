from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed settings.

    Secrets are optional at import time so health checks and unit tests can run
    without external credentials. Feature factories validate the keys they need.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Slack Economic News Agent"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5.6-terra"
    tavily_api_key: SecretStr | None = None
    slack_bot_token: SecretStr | None = None
    slack_signing_secret: SecretStr | None = None

    checkpoint_db_path: Path = Path("./data/checkpoints.sqlite")
    run_database_url: str = "sqlite+aiosqlite:///./data/runs.sqlite"

    news_limit: int = Field(default=5, ge=1, le=20)
    news_days: int = Field(default=7, ge=1, le=365)
    search_max_attempts: int = Field(default=2, ge=1, le=5)
    log_level: str = "INFO"

    @field_validator(
        "openai_api_key",
        "tavily_api_key",
        "slack_bot_token",
        "slack_signing_secret",
        mode="before",
    )
    @classmethod
    def blank_secrets_are_unset(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    def missing_agent_settings(self) -> list[str]:
        missing: list[str] = []
        if self.openai_api_key is None:
            missing.append("OPENAI_API_KEY")
        if self.tavily_api_key is None:
            missing.append("TAVILY_API_KEY")
        return missing

    @property
    def slack_configured(self) -> bool:
        return self.slack_bot_token is not None and self.slack_signing_secret is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()
