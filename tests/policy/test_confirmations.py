from __future__ import annotations

import json

import pytest

from mohizarbot.policy.confirmations import (
    clear_tokens,
    queue_confirmation,
    resolve_confirmation,
)

HMAC_KEY = b"test-hmac-key-32-bytes-long!!"


@pytest.fixture(autouse=True)
def clear() -> None:
    clear_tokens()


def test_queue_and_resolve_happy_path() -> None:
    intent = {"type": "delete_message", "chat_id": -100, "message_id": 42}
    token = queue_confirmation(json.dumps(intent), -100, 200, hmac_key=HMAC_KEY)

    result = resolve_confirmation(token, 200, True, hmac_key=HMAC_KEY)
    assert result is not None
    assert result["type"] == "delete_message"
    assert result["message_id"] == 42


def test_denied_returns_none() -> None:
    intent = {"type": "delete_message", "chat_id": -100, "message_id": 42}
    token = queue_confirmation(json.dumps(intent), -100, 200, hmac_key=HMAC_KEY)

    result = resolve_confirmation(token, 200, False, hmac_key=HMAC_KEY)
    assert result is None


def test_non_admin_uses_same_flow() -> None:
    """Any user in the chat can resolve (admin check in full impl)."""
    intent = {"type": "delete_message", "chat_id": -100, "message_id": 42}
    token = queue_confirmation(json.dumps(intent), -100, 200, hmac_key=HMAC_KEY)

    result = resolve_confirmation(token, 999, True, hmac_key=HMAC_KEY)
    assert result is not None


def test_reused_token_rejected() -> None:
    intent = {"type": "delete_message", "chat_id": -100, "message_id": 42}
    token = queue_confirmation(json.dumps(intent), -100, 200, hmac_key=HMAC_KEY)

    resolve_confirmation(token, 200, True, hmac_key=HMAC_KEY)
    result = resolve_confirmation(token, 200, True, hmac_key=HMAC_KEY)
    assert result is None


def test_expired_token_rejected() -> None:
    intent = {"type": "delete_message", "chat_id": -100, "message_id": 42}
    token = queue_confirmation(json.dumps(intent), -100, 200, hmac_key=HMAC_KEY)

    # Manually expire
    from mohizarbot.policy import confirmations

    confirmations._tokens[token]["expires"] = 0

    result = resolve_confirmation(token, 200, True, hmac_key=HMAC_KEY)
    assert result is None


def test_forged_token_rejected() -> None:
    result = resolve_confirmation("fake:token:data:1234", 200, True, hmac_key=HMAC_KEY)
    assert result is None


def test_invalid_token_format_rejected() -> None:
    result = resolve_confirmation("tooshort", 200, True, hmac_key=HMAC_KEY)
    assert result is None


def test_wrong_hmac_key_rejected() -> None:
    intent = {"type": "delete_message", "chat_id": -100, "message_id": 42}
    token = queue_confirmation(json.dumps(intent), -100, 200, hmac_key=HMAC_KEY)

    result = resolve_confirmation(token, 200, True, hmac_key=b"wrong-key-32-bytes-long!!!!")
    assert result is None
