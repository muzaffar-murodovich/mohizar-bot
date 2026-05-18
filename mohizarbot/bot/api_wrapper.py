from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
from aiogram import Bot

if TYPE_CHECKING:
    from mohizarbot.config import Settings


class BotApiWrapper:
    """Thin wrapper around aiogram Bot for Telegram API calls.

    In Sprint 1 this provides the send_message convenience method.
    Full Bot API 9.6 coverage arrives in Sprint 5.
    Multimedia file download added in Sprint 9.
    """

    def __init__(self, bot: Bot) -> None:
        self._bot = bot
        self._httpx_client: httpx.AsyncClient | None = None

    async def send_message(
        self,
        chat_id: int,
        text: str,
    ) -> dict[str, object]:
        msg = await self._bot.send_message(chat_id=chat_id, text=text)
        return msg.model_dump()

    async def download_file(self, file_id: str) -> tuple[bytes, str]:
        """Download a file from Telegram servers.

        Returns (file_bytes, mime_type). Uses httpx directly for the download
        portion after resolving the file path via aiogram.
        """
        bot = self._bot
        tg_file = await bot.get_file(file_id)
        file_path = tg_file.file_path or ""

        if self._httpx_client is None:
            self._httpx_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))

        token = getattr(bot, "token", "")
        url = f"https://api.telegram.org/file/bot{token}/{file_path}"
        resp = await self._httpx_client.get(url)
        resp.raise_for_status()

        content_type = resp.headers.get("content-type", "application/octet-stream")
        return resp.content, content_type


def build_api_wrapper(settings: Settings) -> BotApiWrapper:
    bot = Bot(token=settings.bot_token)
    return BotApiWrapper(bot)
