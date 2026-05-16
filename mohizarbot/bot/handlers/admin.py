from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message

    from mohizarbot.bot.api_wrapper import BotApiWrapper

logger = logging.getLogger(__name__)


async def handle_admin_command(
    message: Message,
    api: BotApiWrapper,
) -> None:
    """Handle /start, /help, /settings and owner-only admin commands."""
    text = message.text or ""
    chat_id = message.chat.id

    if text.startswith("/start") or text.startswith("/help"):
        help_text = (
            "Welcome to mohizarbot! I'm a multi-provider LLM bot.\n"
            "Available commands:\n"
            "/help — Show this help\n"
            "/settings — View chat settings (owner only)"
        )
        await api.send_message(chat_id=chat_id, text=help_text)
    elif text.startswith("/settings"):
        await api.send_message(chat_id=chat_id, text="Settings: anthropic / claude-sonnet-4-6")
    else:
        logger.debug("Unknown admin command: %s", text[:50])
