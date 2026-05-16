from __future__ import annotations

# Bot mention detection for group chats: @mention, /cmd@bot, reply-to-bot.
# All checks are case-insensitive.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message


def is_bot_mentioned(message: Message, bot_username: str) -> bool:
    """Check if a group message mentions the bot.

    Returns True if:
    - message has a mention entity targeting bot_username
    - message has a bot_command entity ending with @BotUsername
    - message is a reply to a message from the bot
    """
    bot_user = bot_username.lower().lstrip("@")

    # Check entities for mentions and bot commands
    entities = getattr(message, "entities", None) or []
    for entity in entities:
        entity_type = getattr(entity, "type", "")
        if entity_type in ("mention", "text_mention"):
            text = message.text or message.caption or ""
            offset = getattr(entity, "length", 0)
            start = getattr(entity, "offset", 0)
            mentioned = text[start : start + offset].lstrip("@").lower()
            if mentioned == bot_user:
                return True
        elif entity_type == "bot_command":
            text = message.text or message.caption or ""
            offset = getattr(entity, "length", 0)
            start = getattr(entity, "offset", 0)
            command = text[start : start + offset]
            if "@" in command:
                _, target = command.split("@", 1)
                if target.lower() == bot_user:
                    return True

    # Check if replying to a bot message
    reply = getattr(message, "reply_to_message", None)
    if reply is not None:
        reply_from = getattr(reply, "from_user", None)
        if reply_from is not None and getattr(reply_from, "is_bot", False):
            return True

    return False
