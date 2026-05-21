from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

from aiogram.types import Chat, Message, User


def _make_admin_msg(text: str) -> Message:
    return Message(
        message_id=1,
        from_user=User(id=123, is_bot=False, first_name="Admin"),
        date=datetime(2024, 1, 1, 12, 0, 0),
        chat=Chat(id=123, type="private", first_name="AdminTest"),
        text=text,
    )


async def test_start_command() -> None:
    from mohizarbot.bot.handlers.admin import handle_admin_command

    msg = _make_admin_msg("/start")
    api = AsyncMock()
    api.send_message = AsyncMock()
    await handle_admin_command(msg, api)
    api.send_message.assert_awaited_once()
    call_text = api.send_message.call_args.kwargs["text"]
    assert "Welcome" in call_text


async def test_help_command() -> None:
    from mohizarbot.bot.handlers.admin import handle_admin_command

    msg = _make_admin_msg("/help")
    api = AsyncMock()
    api.send_message = AsyncMock()
    await handle_admin_command(msg, api)
    api.send_message.assert_awaited_once()


async def test_settings_command() -> None:
    from mohizarbot.bot.handlers.admin import handle_admin_command

    msg = _make_admin_msg("/settings")
    api = AsyncMock()
    api.send_message = AsyncMock()
    await handle_admin_command(msg, api)
    api.send_message.assert_awaited_once()
    call_text = api.send_message.call_args.kwargs["text"]
    assert "anthropic" in call_text


async def test_unknown_admin_command() -> None:
    from mohizarbot.bot.handlers.admin import handle_admin_command

    msg = _make_admin_msg("/some_unknown_cmd")
    api = AsyncMock()
    api.send_message = AsyncMock()
    await handle_admin_command(msg, api)
    # Unknown command — should not crash, no message sent
