from __future__ import annotations

import hmac

from aiogram.types import Update
from fastapi import APIRouter, Header, Request, Response

from mohizarbot.bot.api_wrapper import build_api_wrapper
from mohizarbot.bot.handlers.callbacks import handle_callback
from mohizarbot.bot.handlers.private import handle_private_message
from mohizarbot.config import Settings

router = APIRouter()


def _get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def _verify_secret(settings: Settings, header_value: str) -> bool:
    return hmac.compare_digest(settings.webhook_secret, header_value)


def _build_router() -> object:
    from mohizarbot.llm.providers.anthropic_ import AnthropicProvider
    from mohizarbot.llm.providers.deepseek_ import DeepSeekProvider
    from mohizarbot.llm.providers.openai_ import OpenAIProvider
    from mohizarbot.llm.router import Router

    # Sprint 4: stub providers with no keys (real keys come from env in prod)
    providers: list[object] = [
        AnthropicProvider(api_key="stub"),
        OpenAIProvider(api_key="stub"),
        DeepSeekProvider(api_key="stub"),
    ]
    return Router(providers, default="anthropic")  # type: ignore[arg-type]


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
    elif update.message is not None and update.message.chat.type == "private":
        await handle_private_message(update.message, api, router, hmac_key, secrets_list)  # type: ignore[arg-type]

    return Response(status_code=200)
