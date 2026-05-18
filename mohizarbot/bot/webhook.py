from __future__ import annotations

import hmac
from typing import TYPE_CHECKING

from aiogram.types import Update
from fastapi import APIRouter, Header, Request, Response

from mohizarbot.bot.api_wrapper import build_api_wrapper
from mohizarbot.bot.handlers.callbacks import handle_callback
from mohizarbot.bot.handlers.private import handle_private_message
from mohizarbot.config import Settings

if TYPE_CHECKING:
    from mohizarbot.llm.base import LLMProvider
    from mohizarbot.llm.router import Router

router = APIRouter()


def _get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def _verify_secret(settings: Settings, header_value: str) -> bool:
    return hmac.compare_digest(settings.webhook_secret, header_value)


def _build_router() -> Router:
    from mohizarbot.llm.providers.anthropic_ import AnthropicProvider
    from mohizarbot.llm.providers.deepseek_ import DeepSeekProvider
    from mohizarbot.llm.providers.openai_ import OpenAIProvider
    from mohizarbot.llm.router import Router

    providers: list[LLMProvider] = [
        AnthropicProvider(api_key="stub"),  # type: ignore[list-item]
        OpenAIProvider(api_key="stub"),  # type: ignore[list-item]
        DeepSeekProvider(api_key="stub"),  # type: ignore[list-item]
    ]
    return Router(providers, default="anthropic")


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
    router = _build_router()
    hmac_key = settings.audit_hmac_key.encode()
    secrets_list = [
        settings.bot_token,
        settings.webhook_secret,
        settings.audit_hmac_key,
        settings.database_url,
        settings.redis_url,
    ]

    if update.callback_query is not None:
        await handle_callback(update.callback_query, api, hmac_key)
    elif update.message is not None:
        chat_type = update.message.chat.type
        if chat_type == "private":
            await handle_private_message(
                update.message, api, router, hmac_key, secrets_list, settings=settings
            )
        elif chat_type in ("group", "supergroup"):
            from mohizarbot.bot.handlers.group import handle_group_message

            await handle_group_message(
                update.message, api, router, hmac_key, secrets_list, settings=settings
            )
        else:
            # channel → no-op (Sprint 9+)
            pass

    return Response(status_code=200)
