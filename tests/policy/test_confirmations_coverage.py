from __future__ import annotations

from mohizarbot.policy.confirmations import (
    TOKEN_TTL,
    clear_tokens,
    queue_confirmation,
    resolve_confirmation,
)


def test_resolve_already_used_token() -> None:
    clear_tokens()
    key = b"test-key-32-bytes-long-xxxxxxx"
    token = queue_confirmation(
        '{"type":"send_message","chat_id":1,"text":"hi"}',
        chat_id=1,
        user_id=1,
        hmac_key=key,
    )
    # Resolve once
    r1 = resolve_confirmation(token, 1, True, hmac_key=key)
    assert r1 is not None
    # Resolve again — should fail (already used)
    r2 = resolve_confirmation(token, 1, True, hmac_key=key)
    assert r2 is None


def test_resolve_bad_token_format() -> None:
    clear_tokens()
    key = b"test-key-32-bytes-long-xxxxxxx"
    r = resolve_confirmation("short", 1, True, hmac_key=key)
    assert r is None


def test_resolve_wrong_signature() -> None:
    clear_tokens()
    key = b"test-key-32-bytes-long-xxxxxxx"
    token = queue_confirmation(
        '{"type":"send_message","chat_id":1,"text":"hi"}',
        chat_id=1,
        user_id=1,
        hmac_key=key,
    )
    # Tamper with the HMAC signature
    parts = token.split(":", 3)
    tampered = f"deadbeef{'0' * 56}:{parts[1]}:{parts[2]}:{parts[3]}"
    r = resolve_confirmation(tampered, 1, True, hmac_key=key)
    assert r is None


def test_resolve_rejects_when_not_approved() -> None:
    clear_tokens()
    key = b"test-key-32-bytes-long-xxxxxxx"
    token = queue_confirmation(
        '{"type":"send_message","chat_id":1,"text":"hi"}',
        chat_id=1,
        user_id=1,
        hmac_key=key,
    )
    r = resolve_confirmation(token, 1, False, hmac_key=key)
    assert r is None


def test_queue_confirmation_creates_token() -> None:
    clear_tokens()
    key = b"test-key-32-bytes-long-xxxxxxx"
    token = queue_confirmation(
        '{"type":"send_message","chat_id":1,"text":"hi"}',
        chat_id=1,
        user_id=1,
        hmac_key=key,
    )
    assert isinstance(token, str)
    assert len(token) > 32


def test_token_ttl_is_positive() -> None:
    assert TOKEN_TTL > 0
