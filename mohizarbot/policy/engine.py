from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aiogram import Bot

    from mohizarbot.policy.intents import IntentBatch

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    status: str  # executed, queued_for_confirmation, denied, blocked
    reason: str = ""
    telegram_response: dict[str, Any] | None = None


@dataclass
class PolicyContext:
    user_id: int
    chat_id: int
    bot: Bot | object  # aiogram Bot or mock
    hmac_key: bytes = b"default-test-key-32-bytes!"
    bot_id: int | None = None


class PolicyEngine:
    """Policy engine: validates intents, checks permissions and rate limits,
    then executes via the bot or queues for confirmation."""

    def __init__(self) -> None:
        pass

    async def execute(self, batch: IntentBatch, ctx: PolicyContext) -> list[ActionResult]:
        from mohizarbot.policy.confirmations import queue_confirmation
        from mohizarbot.policy.permissions import check_permission
        from mohizarbot.policy.rate_limits import check_rate_limits

        results: list[ActionResult] = []

        for intent in batch.actions:
            action_class = self._action_class(intent)

            # Permission check
            perm = await check_permission(
                intent,
                user_id=ctx.user_id,
                chat_id=ctx.chat_id,
                bot=ctx.bot if hasattr(ctx.bot, "get_chat_member") else None,  # type: ignore[arg-type]
                bot_id=ctx.bot_id,
            )
            if not perm.allowed:
                results.append(ActionResult(status="denied", reason=perm.reason))
                continue

            # Rate limit check
            rl = check_rate_limits(ctx.chat_id, ctx.user_id, action_class)
            if not rl.allowed:
                results.append(
                    ActionResult(
                        status="blocked",
                        reason=f"rate_limited:retry_after={rl.retry_after:.1f}",
                    )
                )
                continue

            # High-risk actions: queue for confirmation
            if action_class in ("delete_message",):
                intent_json = intent.model_dump_json()
                token = queue_confirmation(
                    intent_json,
                    ctx.chat_id,
                    ctx.user_id,
                    hmac_key=ctx.hmac_key,
                )
                results.append(
                    ActionResult(
                        status="queued_for_confirmation",
                        reason=f"confirmation_token={token}",
                    )
                )
                continue

            # Execute via Telegram
            try:
                resp = await self._execute_intent(intent, ctx)
                results.append(
                    ActionResult(
                        status="executed",
                        telegram_response=resp,
                    )
                )
            except Exception as e:
                logger.error("Intent execution failed: %s", e)
                results.append(ActionResult(status="blocked", reason=str(e)))

        return results

    @staticmethod
    def _action_class(intent: object) -> str:
        return getattr(intent, "type", "unknown")

    async def _execute_intent(self, intent: object, ctx: PolicyContext) -> dict[str, Any] | None:

        intent_type = getattr(intent, "type", "")
        bot = ctx.bot

        if intent_type == "send_message":
            text = getattr(intent, "text", "")
            chat_id = getattr(intent, "chat_id", ctx.chat_id)
            if hasattr(bot, "send_message"):
                msg = await bot.send_message(chat_id=chat_id, text=text)
                return msg.model_dump() if hasattr(msg, "model_dump") else {"ok": True}

        elif intent_type == "edit_message":
            text = getattr(intent, "text", "")
            chat_id = getattr(intent, "chat_id", ctx.chat_id)
            message_id = getattr(intent, "message_id", 0)
            if hasattr(bot, "edit_message_text"):
                msg = await bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id)
                return msg.model_dump() if hasattr(msg, "model_dump") else {"ok": True}

        elif intent_type == "delete_message":
            chat_id = getattr(intent, "chat_id", ctx.chat_id)
            message_id = getattr(intent, "message_id", 0)
            if hasattr(bot, "delete_message"):
                result = await bot.delete_message(chat_id=chat_id, message_id=message_id)
                return {"ok": bool(result)}

        elif intent_type == "forward_message":
            from_chat = getattr(intent, "from_chat_id", 0)
            msg_id = getattr(intent, "message_id", 0)
            to_chat = getattr(intent, "to_chat_id", 0)
            if hasattr(bot, "forward_message"):
                msg = await bot.forward_message(
                    chat_id=to_chat, from_chat_id=from_chat, message_id=msg_id
                )
                return msg.model_dump() if hasattr(msg, "model_dump") else {"ok": True}

        return None
