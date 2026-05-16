from __future__ import annotations

from pydantic import field_validator
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
    admin_port: int = 8001
    admin_user_ids: list[int] = []

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: object) -> list[int]:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if not s:
                return []
            return [int(x.strip()) for x in s.split(",") if x.strip()]
        return []

    @property
    def secret_fields(self) -> set[str]:
        return {
            "bot_token",
            "webhook_secret",
            "database_url",
            "redis_url",
            "audit_hmac_key",
        }
