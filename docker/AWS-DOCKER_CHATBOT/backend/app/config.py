from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    app_name: str = "AI Chatbot Service"
    app_env: str = "local"
    app_version: str = "1.0.0"
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-5.6-luna"
    max_output_tokens: int = Field(default=800, ge=64, le=4096)

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def has_openai_api_key(self) -> bool:
        """Return whether a non-empty API key was configured."""

        key = self.openai_api_key.get_secret_value().strip()
        return bool(key and not key.startswith("replace-with-"))


@lru_cache
def get_settings() -> Settings:
    """Create the settings object once per application process."""

    return Settings()
