from __future__ import annotations

import re
from datetime import datetime
from unittest.mock import AsyncMock

from aiogram.types import Chat, Message, User

from mohizarbot.bot.api_wrapper import BotApiWrapper
from mohizarbot.security.delimiters import (
    escape_user_content,
    generate_session_token,
    wrap_untrusted_content,
)
from mohizarbot.security.spotlighting import spotlight


def _make_message(text: str) -> Message:
    return Message(
        message_id=1,
        from_user=User(id=123, is_bot=False, first_name="Test"),
        date=datetime(2024, 1, 1, 12, 0, 0),
        chat=Chat(id=123, type="private", first_name="Test"),
        text=text,
    )


def _echo_wrap(text: str, msg: Message) -> str:
    """Mechanical echo: wraps the user's text per Layers 1+2 (Sprint 1)."""
    escaped = escape_user_content(text)
    session_token = generate_session_token()
    wrapped = wrap_untrusted_content(
        escaped,
        "user_message",
        session_token=session_token,
        from_user_id=msg.from_user.id if msg.from_user else 0,
        chat_id=msg.chat.id,
        ts=msg.date.isoformat(),
    )
    return spotlight(wrapped)


def test_echo_contains_spotlight_char() -> None:
    msg = _make_message("hello world")
    text = _echo_wrap(msg.text or "", msg)
    assert "‹" in text


def test_echo_contains_wrapped_user_message() -> None:
    msg = _make_message("hello")
    text = _echo_wrap(msg.text or "", msg)
    assert "<user_message" in text
    assert "</user_message>" in text


def test_echo_has_session_token_attr() -> None:
    msg = _make_message("test")
    text = _echo_wrap(msg.text or "", msg)
    match = re.search(r'session_token="([a-f0-9]+)"', text)
    assert match is not None
    token = match.group(1)
    assert len(token) >= 16


def test_echo_contains_from_user_id_attr() -> None:
    msg = _make_message("hi")
    text = _echo_wrap(msg.text or "", msg)
    assert 'from_user_id="123"' in text


def test_echo_contains_chat_id_attr() -> None:
    msg = _make_message("hi")
    text = _echo_wrap(msg.text or "", msg)
    assert 'chat_id="123"' in text


def test_echo_with_empty_text() -> None:
    msg = _make_message("")
    text = _echo_wrap(msg.text or "", msg)
    assert "<user_message" in text
    assert "</user_message>" in text
