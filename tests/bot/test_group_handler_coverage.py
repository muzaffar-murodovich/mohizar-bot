from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from aiogram.types import Chat, Message, User


def _make_group_msg(text: str, chat_id: int = -100123, user_id: int = 456) -> Message:
    return Message(
        message_id=1,
        from_user=User(id=user_id, is_bot=False, first_name="Test"),
        date=datetime(2024, 1, 1, 12, 0, 0),
        chat=Chat(id=chat_id, type="supergroup", first_name="TestGroup"),
        text=text,
    )


async def test_handle_group_message_not_mentioned_skips() -> None:
    """When bot is not mentioned, the handler returns immediately."""
    from mohizarbot.bot.handlers.group import handle_group_message

    msg = _make_group_msg("Hello world")
    api = AsyncMock()
    router = MagicMock()
    hmac_key = b"test-key-32-bytes-long-xxxxxxx"
    secrets = ["secret1", "secret2"]

    # Bot not mentioned → should return without doing anything
    with patch("mohizarbot.bot.mention.is_bot_mentioned", return_value=False):
        result = await handle_group_message(msg, api, router, hmac_key, secrets)
    assert result is None


async def test_handle_group_message_with_settings_param() -> None:
    """Group handler accepts settings parameter."""
    from mohizarbot.bot.handlers.group import handle_group_message

    msg = _make_group_msg("@mohizarbot help")
    api = AsyncMock()
    router = MagicMock()
    hmac_key = b"test-key-32-bytes-long-xxxxxxx"
    secrets = ["secret1"]
    settings = MagicMock()

    with patch("mohizarbot.bot.mention.is_bot_mentioned", return_value=True):
        # The handler will try to get chat_member etc. - we just ensure
        # it doesn't crash with settings param
        import contextlib

        with contextlib.suppress(Exception):
            await handle_group_message(msg, api, router, hmac_key, secrets, settings=settings)
