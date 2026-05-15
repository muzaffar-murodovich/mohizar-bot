from __future__ import annotations

import os

import pytest

# Ensure no real .env file leaks into tests
os.environ.setdefault("BOT_TOKEN", "111:test")
os.environ.setdefault("WEBHOOK_SECRET", "test-webhook-secret-32-chars-min")
os.environ.setdefault("AUDIT_HMAC_KEY", "aa" * 32)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def sample_settings_dict() -> dict[str, str]:
    return {
        "BOT_TOKEN": "123:abc",
        "WEBHOOK_SECRET": "super-secret-at-least-32-bytes-long",
        "WEBHOOK_URL": "https://example.com/webhook",
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/db",
        "REDIS_URL": "redis://localhost:6379/0",
        "AUDIT_HMAC_KEY": "bb" * 32,
        "LOG_LEVEL": "DEBUG",
    }
