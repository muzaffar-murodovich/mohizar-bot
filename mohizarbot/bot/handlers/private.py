from __future__ import annotations

import logging
import os as _os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message

    from mohizarbot.bot.api_wrapper import BotApiWrapper
    from mohizarbot.config import Settings
    from mohizarbot.llm.router import Router

logger = logging.getLogger(__name__)

_prompt_path = _os.path.join(_os.path.dirname(__file__), "..", "..", "prompts", "system.md.tmpl")
with open(_prompt_path) as f:
    _SYSTEM_TEMPLATE = f.read()


def _build_emit_intents_tool(enabled_tools: list[str] | None = None) -> dict[str, object]:
    """Inline emit_intents schema builder — avoids circular imports.

    Only emit_intents is exposed to the LLM. No other functions.
    """
    return {
        "type": "function",
        "function": {
            "name": "emit_intents",
            "description": "Emit structured intents for the policy engine to execute.",
            "parameters": {
                "type": "object",
                "properties": {
                    "thought": {"type": "string", "description": "Reasoning about the intents"},
                    "actions": {
                        "type": "array",
                        "items": {
                            "anyOf": [
                                {
                                    "type": "object",
                                    "properties": {
                                        "type": {"const": "send_message"},
                                        "chat_id": {"type": "integer"},
                                        "text": {"type": "string"},
                                    },
                                    "required": ["type", "chat_id", "text"],
                                },
                            ]
                        },
                    },
                },
                "required": ["actions"],
            },
        },
    }


async def handle_private_message(
    message: Message,
    api: BotApiWrapper,
    router: Router,
    hmac_key: bytes,
    secrets: list[str],
    settings: Settings | None = None,
) -> None:
    """Full pipeline: sanitize → wrap → LLM → intents → policy → output → send.

    Supports multimodal: voice/audio transcription, image understanding,
    and document reading (Sprint 9).
    """
    from mohizarbot.bot.handlers.multimodal_helper import (
        process_message_multimodal,
    )
    from mohizarbot.llm.types import ChatMessage, ToolSpec
    from mohizarbot.policy.engine import PolicyContext, PolicyEngine
    from mohizarbot.security.input_sanitizer import sanitize
    from mohizarbot.security.output_filter import filter_output
    from mohizarbot.security.untrusted import generate_session_token, wrap_untrusted

    if settings is None:
        from mohizarbot.config import Settings as _Settings

        settings = _Settings()  # type: ignore[call-arg]

    user_text = message.text or ""
    chat_id = message.chat.id
    user_id = message.from_user.id if message.from_user else 0

    # 0. Process multimodal content
    processed_text, capability_hints = await process_message_multimodal(message, api, settings)
    has_multimodal = bool(capability_hints)

    if has_multimodal:
        user_text = processed_text

    # 1. Sanitize and wrap
    cleaned = sanitize(user_text)
    session_token = generate_session_token()
    wrapped = wrap_untrusted(
        "user_message", cleaned, session_token=session_token, from_user_id=user_id, chat_id=chat_id
    )

    # 2. Build LLM messages
    system_prompt = _SYSTEM_TEMPLATE.replace("{session_token}", session_token)
    messages = [
        ChatMessage(role="system", content=system_prompt),
        ChatMessage(role="user", content=wrapped),
    ]

    # 3. Route and call LLM (with vision hints for images)
    hints_arg = capability_hints if has_multimodal else None
    provider = router.select(messages, capability_hints=hints_arg)
    tool_schema = _build_emit_intents_tool()
    fn_schema: dict[str, object] = tool_schema.get("function", {})  # type: ignore[assignment]
    raw_params = fn_schema.get("parameters", {})
    params: dict[str, object] = raw_params if isinstance(raw_params, dict) else {}
    tool_spec = ToolSpec(
        name="emit_intents",
        description=str(fn_schema.get("description", "")),
        parameters=params,
    )

    try:
        response = await provider.chat(messages, tools=[tool_spec])
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        await api.send_message(chat_id=chat_id, text="Sorry, something went wrong.")
        return

    # 4. Parse intent batch from LLM response
    intent_batch = _parse_intents_from_response(response)
    if intent_batch is None:
        filtered = filter_output(response.content, secrets=secrets)
        await api.send_message(chat_id=chat_id, text=filtered.text)
        return

    # 5. Run policy engine
    engine = PolicyEngine()
    ctx = PolicyContext(
        user_id=user_id,
        chat_id=chat_id,
        bot=api._bot,
        hmac_key=hmac_key,
        bot_id=(await api._bot.get_me()).id if hasattr(api._bot, "get_me") else None,
    )

    results = await engine.execute(intent_batch, ctx)  # type: ignore[arg-type]

    # 6. Send results back
    for result in results:
        if result.status == "executed":
            if result.telegram_response:
                continue
        elif result.status == "queued_for_confirmation":
            await api.send_message(
                chat_id=chat_id,
                text=f"Action requires confirmation. Token: {result.reason.split('=')[-1][:16]}...",
            )
        elif result.status in ("denied", "blocked"):
            await api.send_message(
                chat_id=chat_id,
                text=f"Cannot perform action: {result.reason}",
            )


def _parse_intents_from_response(response: object) -> object:
    """Extract IntentBatch from LLM response tool calls."""
    from mohizarbot.policy.intents import IntentBatch

    if hasattr(response, "tool_calls") and response.tool_calls:
        for tc in response.tool_calls:
            name = getattr(tc, "name", "")
            if name == "emit_intents":
                args = getattr(tc, "arguments", None)
                if isinstance(args, dict):
                    return IntentBatch.model_validate(args)
    return None
