from __future__ import annotations

import hashlib
import hmac
import time

from mohizarbot.admin.auth import TelegramLoginVerifier


def _make_auth_data(user_id: int, bot_token: str, age_seconds: int = 0) -> dict[str, str]:
    auth_date = int(time.time()) - age_seconds
    data = {
        "id": str(user_id),
        "first_name": "Test",
        "username": "testuser",
        "auth_date": str(auth_date),
    }
    check_pairs = sorted((k, v) for k, v in data.items())
    check_string = "\n".join(f"{k}={v}" for k, v in check_pairs)
    secret = hashlib.sha256(bot_token.encode()).digest()
    data["hash"] = hmac.digest(secret, check_string.encode(), hashlib.sha256).hex()
    return data


def test_valid_auth_accepted() -> None:
    verifier = TelegramLoginVerifier("test-bot-token")
    data = _make_auth_data(123, "test-bot-token")
    result = verifier.verify(data)
    assert result is not None
    assert result.user_id == 123


def test_tampered_hash_rejected() -> None:
    verifier = TelegramLoginVerifier("test-bot-token")
    data = _make_auth_data(123, "test-bot-token")
    data["id"] = "999"
    result = verifier.verify(data)
    assert result is None


def test_expired_auth_date_rejected() -> None:
    verifier = TelegramLoginVerifier("test-bot-token", max_age_seconds=60)
    data = _make_auth_data(123, "test-bot-token", age_seconds=120)
    result = verifier.verify(data)
    assert result is None


def test_missing_hash_rejected() -> None:
    verifier = TelegramLoginVerifier("test-bot-token")
    data = {"id": "123", "auth_date": str(int(time.time()))}
    result = verifier.verify(data)
    assert result is None


def test_wrong_bot_token_rejected() -> None:
    verifier = TelegramLoginVerifier("correct-token")
    data = _make_auth_data(123, "wrong-token")
    result = verifier.verify(data)
    assert result is None


def test_non_admin_user() -> None:
    verifier = TelegramLoginVerifier("token")
    data = _make_auth_data(99999, "token")
    result = verifier.verify(data)
    assert result is not None
    assert result.user_id == 99999
