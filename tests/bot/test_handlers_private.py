from __future__ import annotations

import re
from datetime import datetime
from unittest.mock import AsyncMock

from aiogram.types import Chat, Message, User

from mohizarbot.bot.api_wrapper import BotApiWrapper
from mohizarbot.bot.handlers.private import handle_private_message


def _make_message(text: str) -> Message:
    return Message(
        message_id=1,
        from_user=User(id=123, is_bot=False, first_name="Test"),
        date=datetime(2024, 1, 1, 12, 0, 0),
        chat=Chat(id=123, type="private", first_name="Test"),
        text=text,
    )


async def test_echo_contains_spotlight_char() -> None:
    mock_api = AsyncMock(spec=BotApiWrapper)
    msg = _make_message("hello world")
    await handle_private_message(msg, mock_api)

    mock_api.send_message.assert_awaited_once()
    call_kwargs = mock_api.send_message.call_args.kwargs
    text: str = call_kwargs["text"]
    assert "‹" in text  # Spotlight char U+2039


async def test_echo_contains_wrapped_user_message() -> None:
    mock_api = AsyncMock(spec=BotApiWrapper)
    msg = _make_message("hello")
    await handle_private_message(msg, mock_api)

    mock_api.send_message.assert_awaited_once()
    call_kwargs = mock_api.send_message.call_args.kwargs
    text: str = call_kwargs["text"]
    assert "<user_message" in text
    assert "</user_message>" in text


async def test_echo_has_session_token_attr() -> None:
    mock_api = AsyncMock(spec=BotApiWrapper)
    msg = _make_message("test")
    await handle_private_message(msg, mock_api)

    mock_api.send_message.assert_awaited_once()
    call_kwargs = mock_api.send_message.call_args.kwargs
    text: str = call_kwargs["text"]
    match = re.search(r'session_token="([a-f0-9]+)"', text)
    assert match is not None, "session_token attribute missing"
    token = match.group(1)
    assert len(token) >= 16, f"session_token too short: {len(token)} hex chars"


async def test_echo_contains_from_user_id_attr() -> None:
    mock_api = AsyncMock(spec=BotApiWrapper)
    msg = _make_message("hi")
    await handle_private_message(msg, mock_api)

    mock_api.send_message.assert_awaited_once()
    call_kwargs = mock_api.send_message.call_args.kwargs
    text: str = call_kwargs["text"]
    assert 'from_user_id="123"' in text


async def test_echo_contains_chat_id_attr() -> None:
    mock_api = AsyncMock(spec=BotApiWrapper)
    msg = _make_message("hi")
    await handle_private_message(msg, mock_api)

    mock_api.send_message.assert_awaited_once()
    call_kwargs = mock_api.send_message.call_args.kwargs
    text: str = call_kwargs["text"]
    assert 'chat_id="123"' in text


async def test_echo_with_empty_text() -> None:
    mock_api = AsyncMock(spec=BotApiWrapper)
    msg = _make_message("")
    await handle_private_message(msg, mock_api)

    mock_api.send_message.assert_awaited_once()
    call_kwargs = mock_api.send_message.call_args.kwargs
    text: str = call_kwargs["text"]
    # Empty content still gets wrapped
    assert "<user_message" in text
    assert "</user_message>" in text
