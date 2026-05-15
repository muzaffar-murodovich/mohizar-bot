from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message

    from mohizarbot.bot.api_wrapper import BotApiWrapper

from mohizarbot.security.delimiters import (
    escape_user_content,
    generate_session_token,
    wrap_untrusted_content,
)
from mohizarbot.security.spotlighting import spotlight


async def handle_private_message(
    message: Message,
    api: BotApiWrapper,
) -> None:
    """Echo handler: wraps the user's text per Layers 1+2 and sends it back.

    This does NOT call any LLM — it is a mechanical wrap+spotlight operation
    that proves the delimiters and spotlighting plumbing works end-to-end.
    """
    user_text = message.text or ""
    escaped = escape_user_content(user_text)
    session_token = generate_session_token()
    wrapped = wrap_untrusted_content(
        escaped,
        "user_message",
        session_token=session_token,
        from_user_id=message.from_user.id if message.from_user else 0,
        chat_id=message.chat.id,
        ts=message.date.isoformat(),
    )
    spotlighted = spotlight(wrapped)

    await api.send_message(chat_id=message.chat.id, text=spotlighted)
