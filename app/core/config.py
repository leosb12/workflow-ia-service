from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    app_name: str = Field(default="ia-service", validation_alias="APP_NAME")
    app_env: str = Field(default="local", validation_alias="APP_ENV")

    deepseek_api_key: str = Field(default="", validation_alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        validation_alias="DEEPSEEK_BASE_URL",
    )
    deepseek_model: str = Field(default="deepseek-chat", validation_alias="DEEPSEEK_MODEL")
    deepseek_user_guide_model: str = Field(
        default="deepseek-v4-flash",
        validation_alias="DEEPSEEK_USER_GUIDE_MODEL",
    )
    deepseek_max_tokens: int = Field(default=0, validation_alias="DEEPSEEK_MAX_TOKENS")
    deepseek_temperature: float = Field(default=0.2, validation_alias="DEEPSEEK_TEMPERATURE")
    deepseek_timeout_seconds: float = Field(default=0.0, validation_alias="DEEPSEEK_TIMEOUT_SECONDS")
    ia_deep_learning_service_url: str = Field(
        default="http://localhost:8010",
        validation_alias="IA_DEEP_LEARNING_SERVICE_URL",
    )

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def deepseek_chat_completions_url(self) -> str:
        return f"{self.deepseek_base_url.strip().rstrip('/')}/chat/completions"


@lru_cache
def get_settings() -> Settings:
    return Settings()
