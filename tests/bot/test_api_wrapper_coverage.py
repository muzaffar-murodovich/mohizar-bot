from __future__ import annotations

from unittest.mock import AsyncMock

from mohizarbot.bot.api_wrapper import BotApiWrapper


async def test_bot_api_wrapper_send_message() -> None:
    bot = AsyncMock()
    msg = AsyncMock()
    msg.model_dump = lambda: {"ok": True, "result": {"message_id": 1}}
    bot.send_message = AsyncMock(return_value=msg)

    wrapper = BotApiWrapper(bot)
    result = await wrapper.send_message(chat_id=123, text="Hello")
    assert result["ok"] is True
    bot.send_message.assert_awaited_once_with(chat_id=123, text="Hello")


async def test_bot_api_wrapper_bot_accessible() -> None:
    bot = AsyncMock()
    bot.token = "test-token"
    wrapper = BotApiWrapper(bot)
    assert wrapper._bot is bot
