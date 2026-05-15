from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    bot_token: str
    webhook_secret: str
    webhook_url: str = ""
    database_url: str = "postgresql+asyncpg://mohizar:mohizar@localhost:5432/mohizarbot"
    redis_url: str = "redis://localhost:6379/0"
    audit_hmac_key: str
    log_level: str = "INFO"

    @property
    def secret_fields(self) -> set[str]:
        return {
            "bot_token",
            "webhook_secret",
            "database_url",
            "redis_url",
            "audit_hmac_key",
        }
