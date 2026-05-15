from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Bot

if TYPE_CHECKING:
    from mohizarbot.config import Settings


class BotApiWrapper:
    """Thin wrapper around aiogram Bot for Telegram API calls.

    In Sprint 1 this provides the send_message convenience method.
    Full Bot API 9.6 coverage arrives in Sprint 5.
    """

    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def send_message(
        self,
        chat_id: int,
        text: str,
    ) -> dict[str, object]:
        msg = await self._bot.send_message(chat_id=chat_id, text=text)
        return msg.model_dump()


def build_api_wrapper(settings: Settings) -> BotApiWrapper:
    bot = Bot(token=settings.bot_token)
    return BotApiWrapper(bot)
