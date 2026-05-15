from __future__ import annotations

import hmac

from aiogram.types import Update
from fastapi import APIRouter, Header, Request, Response

from mohizarbot.bot.api_wrapper import build_api_wrapper
from mohizarbot.bot.handlers.private import handle_private_message
from mohizarbot.config import Settings

router = APIRouter()


def _get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def _verify_secret(settings: Settings, header_value: str) -> bool:
    return hmac.compare_digest(settings.webhook_secret, header_value)


@router.post("/webhook")
async def webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(default=""),
) -> Response:
    settings = _get_settings()

    if not x_telegram_bot_api_secret_token or not _verify_secret(
        settings, x_telegram_bot_api_secret_token
    ):
        return Response(status_code=401)

    body = await request.json()
    update = Update.model_validate(body)
    api = build_api_wrapper(settings)

    if update.message is not None and update.message.chat.type == "private":
        await handle_private_message(update.message, api)

    return Response(status_code=200)
