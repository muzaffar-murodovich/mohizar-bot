from __future__ import annotations

import json

from mohizarbot.bot.keyboard import (
    InlineButton,
    _sign_callback,
    build_inline_keyboard,
    verify_callback,
)


def test_keyboard_shape_single_row() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    kb = build_inline_keyboard(
        [[InlineButton(text="Click me", callback_data="action:hello")]],
        hmac_key=key,
    )
    assert "inline_keyboard" in kb
    rows = kb["inline_keyboard"]
    assert len(rows) == 1
    assert rows[0][0]["text"] == "Click me"
    assert "callback_data" in rows[0][0]


def test_keyboard_shape_multiple_rows() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    kb = build_inline_keyboard(
        [
            [InlineButton(text="A", callback_data="a"), InlineButton(text="B", callback_data="b")],
            [InlineButton(text="C", callback_data="c")],
        ],
        hmac_key=key,
    )
    assert len(kb["inline_keyboard"]) == 2
    assert len(kb["inline_keyboard"][0]) == 2
    assert len(kb["inline_keyboard"][1]) == 1


def test_callback_data_is_hmac_signed() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    kb = build_inline_keyboard(
        [[InlineButton(text="Go", callback_data="do_stuff")]],
        hmac_key=key,
    )
    signed = kb["inline_keyboard"][0][0]["callback_data"]
    assert isinstance(signed, str)
    # Format: <sig_hex>:<payload>
    parts = signed.split(":", 1)
    assert len(parts) == 2
    assert len(parts[0]) == 64  # SHA256 hex
    assert parts[1] == "do_stuff"


def test_verify_valid_callback() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    signed = _sign_callback("hello", key)
    result = verify_callback(signed, key)
    assert result == "hello"


def test_verify_tampered_callback() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    signed = _sign_callback("hello", key)
    # Tamper with payload
    parts = signed.split(":", 1)
    tampered = f"{parts[0]}:evil"
    result = verify_callback(tampered, key)
    assert result is None


def test_verify_tampered_signature() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    signed = _sign_callback("hello", key)
    parts = signed.split(":", 1)
    # Flip some bits in the signature
    bad_sig = "00" * 32
    tampered = f"{bad_sig}:{parts[1]}"
    result = verify_callback(tampered, key)
    assert result is None


def test_verify_wrong_key() -> None:
    key1 = b"test-key-32-bytes-long-xxxxxxx"
    key2 = b"other-key-32-bytes-long-yyyyyy"
    signed = _sign_callback("hello", key1)
    result = verify_callback(signed, key2)
    assert result is None


def test_verify_malformed_no_colon() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    result = verify_callback("no_colon_here", key)
    assert result is None


def test_url_button_no_callback_data() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    kb = build_inline_keyboard(
        [[InlineButton(text="Visit", callback_data="", url="https://example.com")]],
        hmac_key=key,
    )
    btn = kb["inline_keyboard"][0][0]
    assert btn["text"] == "Visit"
    assert btn["url"] == "https://example.com"
    # No callback_data for URL-only buttons
    assert "callback_data" not in btn


def test_payload_roundtrip_json() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    payload = json.dumps({"action": "vote", "option": "yes"})
    signed = _sign_callback(payload, key)
    result = verify_callback(signed, key)
    assert result == payload
    parsed = json.loads(result)
    assert parsed["action"] == "vote"
