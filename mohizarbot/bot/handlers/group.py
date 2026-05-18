from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message

    from mohizarbot.bot.api_wrapper import BotApiWrapper
    from mohizarbot.config import Settings
    from mohizarbot.llm.router import Router

logger = logging.getLogger(__name__)

_CONTEXT_COUNT = 10


async def handle_group_message(
    message: Message,
    api: BotApiWrapper,
    router: Router,
    hmac_key: bytes,
    secrets: list[str],
    bot_username: str = "mohizarbot",
    settings: Settings | None = None,
) -> None:
    """Handle a group message.

    Responds ONLY when the bot is @-mentioned, replied to, or addressed
    via /command@BotUsername. Other messages are silently logged for context.

    Supports multimodal: voice/audio transcription, image understanding,
    and document reading (Sprint 9).
    """
    from mohizarbot.bot.mention import is_bot_mentioned

    if not is_bot_mentioned(message, bot_username):
        logger.debug("Group message not addressed to bot, skipping")
        return

    from mohizarbot.bot.handlers.multimodal_helper import (
        process_message_multimodal,
    )
    from mohizarbot.llm.types import ChatMessage
    from mohizarbot.policy.engine import PolicyContext, PolicyEngine
    from mohizarbot.security.input_sanitizer import sanitize
    from mohizarbot.security.output_filter import filter_output
    from mohizarbot.security.untrusted import (
        generate_session_token,
        wrap_group_message,
    )

    if settings is None:
        from mohizarbot.config import Settings as _Settings

        settings = _Settings()  # type: ignore[call-arg]

    user_text = message.text or ""
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0
    username = (
        message.from_user.username if message.from_user and message.from_user.username else ""
    )

    # Detect reply parent
    reply_to = getattr(message, "reply_to_message", None)
    reply_user_id = str(getattr(getattr(reply_to, "from_user", None), "id", ""))
    is_reply_to_bot = getattr(getattr(reply_to, "from_user", None), "is_bot", False)

    # Forward provenance
    forward_origin = getattr(message, "forward_origin", None)
    forwarded_from_id = ""
    forwarded_from_chat_id = ""
    if forward_origin is not None:
        forwarded_from_id = str(getattr(forward_origin, "sender_user", {}))
        forwarded_from_chat_id = str(getattr(forward_origin, "chat", {}))

    # Admin check
    try:
        member = await api._bot.get_chat_member(chat_id, user_id)
        is_admin = str(getattr(member, "status", "") in ("creator", "administrator")).lower()
    except Exception:
        is_admin = "false"

    # 0. Process multimodal content
    processed_text, capability_hints = await process_message_multimodal(message, api, settings)
    has_multimodal = bool(capability_hints)

    if has_multimodal:
        user_text = processed_text

    # 1. Sanitize and wrap
    cleaned = sanitize(user_text)
    session_token = generate_session_token()
    ts = message.date.isoformat() if message.date else ""

    wrapped = wrap_group_message(
        cleaned,
        from_user_id=str(user_id),
        username=username,
        is_admin=is_admin,
        is_reply_to_bot=str(is_reply_to_bot).lower(),
        reply_to_user_id=reply_user_id,
        forwarded_from_id=forwarded_from_id,
        forwarded_from_chat_id=forwarded_from_chat_id,
        ts=ts,
    )

    # 2. Build messages with reply parent if present
    system_prompt = _build_group_system_prompt(session_token)
    messages: list[ChatMessage] = [ChatMessage(role="system", content=system_prompt)]

    # Add reply parent wrapped separately
    if reply_to is not None:
        reply_text = getattr(reply_to, "text", "") or ""
        reply_cleaned = sanitize(reply_text)
        reply_wrapped = wrap_group_message(
            reply_cleaned,
            from_user_id=str(getattr(getattr(reply_to, "from_user", None), "id", "")),
            username=getattr(getattr(reply_to, "from_user", None), "username", ""),
            is_admin=is_admin,
            is_reply_to_bot="false",
            reply_to_user_id="",
            forwarded_from_id="",
            forwarded_from_chat_id="",
            ts=reply_to.date.isoformat() if getattr(reply_to, "date", None) else "",
            is_reply_target="true",
        )
        messages.append(ChatMessage(role="assistant", content=reply_wrapped))

    messages.append(ChatMessage(role="user", content=wrapped))

    # 3. Route and call LLM (with vision hints for images)
    hints_arg = capability_hints if has_multimodal else None
    provider = router.select(messages, capability_hints=hints_arg)
    try:
        response = await provider.chat(messages)
    except Exception as e:
        logger.error("Group LLM call failed: %s", e)
        return

    # 4. Parse intents and run policy engine
    from mohizarbot.bot.handlers.private import _parse_intents_from_response

    intent_batch = _parse_intents_from_response(response)

    if intent_batch is None:
        filtered = filter_output(response.content, secrets=secrets)
        await api.send_message(chat_id=chat_id, text=filtered.text)
        return

    engine = PolicyEngine()
    ctx = PolicyContext(user_id=user_id, chat_id=chat_id, bot=api._bot, hmac_key=hmac_key)
    results = await engine.execute(intent_batch, ctx)  # type: ignore[arg-type]

    for result in results:
        if result.status == "executed":
            continue
        elif result.status == "queued_for_confirmation":
            await api.send_message(chat_id=chat_id, text="Action requires admin confirmation.")
        elif result.status in ("denied", "blocked"):
            await api.send_message(chat_id=chat_id, text=f"Cannot do that: {result.reason}")


def _build_group_system_prompt(session_token: str) -> str:
    import os

    prompt_path = os.path.join(os.path.dirname(__file__), "..", "..", "prompts", "system.md.tmpl")
    with open(prompt_path) as f:
        base = f.read()
    prompt = base.replace("{session_token}", session_token)
    return prompt
