from __future__ import annotations

import json
from unittest.mock import AsyncMock

from mohizarbot.bot.keyboard import _sign_callback, verify_callback


def _make_callback(
    data: str,
    user_id: int = 123,
    chat_id: int = 456,
    message_id: int = 1,
) -> AsyncMock:
    callback = AsyncMock()
    callback.data = data
    callback.from_user = AsyncMock()
    callback.from_user.id = user_id
    callback.message = AsyncMock()
    callback.message.chat = AsyncMock()
    callback.message.chat.id = chat_id
    callback.message.message_id = message_id
    callback.answer = AsyncMock()
    callback.message.edit_text = AsyncMock()
    return callback


async def test_signed_callback_handled() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    payload = json.dumps({"action": "answer", "text": "Thanks!", "show_alert": False})
    signed = _sign_callback(payload, key)
    callback = _make_callback(signed)
    api = AsyncMock()

    from mohizarbot.bot.handlers.callbacks import handle_callback

    await handle_callback(callback, api, key)
    callback.answer.assert_awaited_once()
    call_kwargs = callback.answer.call_args.kwargs
    assert call_kwargs.get("text") == "Thanks!"


async def test_unsigned_callback_dropped() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    callback = _make_callback("unsigned_nonsense")
    api = AsyncMock()

    from mohizarbot.bot.handlers.callbacks import handle_callback

    await handle_callback(callback, api, key)
    # Unsigned callbacks are silently dropped — no answer, no crash
    # (verify_callback returns None, audit entry logged)


async def test_tampered_callback_silently_dropped() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    payload = json.dumps({"action": "answer", "text": "Hi"})
    signed = _sign_callback(payload, key)
    # Tamper with payload
    parts = signed.split(":", 1)
    tampered = f"{parts[0]}:evil_payload"
    callback = _make_callback(tampered)
    api = AsyncMock()

    from mohizarbot.bot.handlers.callbacks import handle_callback

    await handle_callback(callback, api, key)
    # Silently dropped — verify_callback returns None


async def test_answer_callback_query_called() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    payload = json.dumps({"action": "answer", "text": "Done!", "show_alert": True})
    signed = _sign_callback(payload, key)
    callback = _make_callback(signed)
    api = AsyncMock()

    from mohizarbot.bot.handlers.callbacks import handle_callback

    await handle_callback(callback, api, key)
    callback.answer.assert_awaited_once()
    call_kwargs = callback.answer.call_args.kwargs
    assert call_kwargs.get("show_alert") is True


async def test_dismiss_callback() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    payload = json.dumps({"action": "dismiss"})
    signed = _sign_callback(payload, key)
    callback = _make_callback(signed)
    api = AsyncMock()

    from mohizarbot.bot.handlers.callbacks import handle_callback

    await handle_callback(callback, api, key)
    callback.answer.assert_awaited_once()


async def test_confirm_callback_still_works() -> None:
    """Ensure Sprint 4 confirmation flow is not broken."""
    key = b"test-key-32-bytes-long-xxxxxxx"
    callback = _make_callback("confirm:test_token:approve")
    api = AsyncMock()
    api._bot = AsyncMock()

    from mohizarbot.bot.handlers.callbacks import handle_callback

    await handle_callback(callback, api, key)
    # Should reach the confirm handler — token is fake so it'll answer
    # "Invalid or expired confirmation token"
    callback.answer.assert_awaited_once()


async def test_empty_callback_data() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    callback = _make_callback("")
    api = AsyncMock()

    from mohizarbot.bot.handlers.callbacks import handle_callback

    await handle_callback(callback, api, key)
    # Empty data is silently dropped


async def test_verify_callback_roundtrip() -> None:
    key = b"test-key-32-bytes-long-xxxxxxx"
    original = "arbitrary_string_payload"
    signed = _sign_callback(original, key)
    result = verify_callback(signed, key)
    assert result == original
