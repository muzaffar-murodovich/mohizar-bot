from __future__ import annotations

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from mohizarbot.config import Settings


def test_loads_from_sample_env(sample_settings_dict: dict[str, str]) -> None:
    with patch.dict(os.environ, sample_settings_dict, clear=True):
        s = Settings()
        assert s.bot_token == "123:abc"
        assert s.webhook_secret == "super-secret-at-least-32-bytes-long"
        assert s.webhook_url == "https://example.com/webhook"
        assert s.audit_hmac_key == "bb" * 32
        assert s.log_level == "DEBUG"


def test_rejects_missing_bot_token() -> None:
    env = {
        "WEBHOOK_SECRET": "secret-32-bytes-long-at-least",
        "AUDIT_HMAC_KEY": "cc" * 32,
    }
    with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
        Settings()


def test_rejects_missing_webhook_secret() -> None:
    env = {
        "BOT_TOKEN": "123:abc",
        "AUDIT_HMAC_KEY": "cc" * 32,
    }
    with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
        Settings()


def test_rejects_missing_audit_hmac_key() -> None:
    env = {
        "BOT_TOKEN": "123:abc",
        "WEBHOOK_SECRET": "secret-32-bytes-long-at-least",
    }
    with patch.dict(os.environ, env, clear=True), pytest.raises(ValidationError):
        Settings()


def test_secret_fields_contains_all_secrets() -> None:
    env = {
        "BOT_TOKEN": "123:abc",
        "WEBHOOK_SECRET": "secret-32-bytes-long-at-least",
        "AUDIT_HMAC_KEY": "cc" * 32,
    }
    with patch.dict(os.environ, env, clear=True):
        s = Settings()
        secrets = s.secret_fields
        assert "bot_token" in secrets
        assert "webhook_secret" in secrets
        assert "database_url" in secrets
        assert "redis_url" in secrets
        assert "audit_hmac_key" in secrets
