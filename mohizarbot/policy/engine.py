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
    redis: object | None = None  # Redis client for scheduler


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
            from mohizarbot.policy.risk import is_high_risk

            if is_high_risk(action_class):
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

        # ── Sprint 10: inline keyboards ──
        elif intent_type == "send_message_with_keyboard":
            chat_id = getattr(intent, "chat_id", ctx.chat_id)
            text = getattr(intent, "text", "")
            buttons = getattr(intent, "buttons", [])
            kwargs: dict[str, Any] = {"chat_id": chat_id, "text": text}
            if buttons:
                kwargs["reply_markup"] = {"inline_keyboard": buttons}
            if hasattr(bot, "send_message"):
                msg = await bot.send_message(**kwargs)
                return msg.model_dump() if hasattr(msg, "model_dump") else {"ok": True}

        elif intent_type == "edit_reply_markup":
            chat_id = getattr(intent, "chat_id", ctx.chat_id)
            message_id = getattr(intent, "message_id", 0)
            buttons = getattr(intent, "buttons", [])
            if hasattr(bot, "edit_message_reply_markup"):
                result = await bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup={"inline_keyboard": buttons},
                )
                return {"ok": bool(result)}

        # ── Sprint 10: media groups ──
        elif intent_type == "send_media_group":
            chat_id = getattr(intent, "chat_id", ctx.chat_id)
            media = getattr(intent, "media", [])
            if hasattr(bot, "send_media_group"):
                media_list: list[Any] = []
                for item in media:
                    media_dict: dict[str, Any] = {
                        "type": getattr(item, "type", "photo"),
                        "media": getattr(item, "file_id_or_url", ""),
                    }
                    caption = getattr(item, "caption", None)
                    # Only first item gets caption
                    if caption and not media_list:
                        media_dict["caption"] = caption
                    media_list.append(media_dict)
                msg = await bot.send_media_group(chat_id=chat_id, media=media_list)
                return msg[0].model_dump() if hasattr(msg[0], "model_dump") else {"ok": True}

        # ── Sprint 10: channel posts ──
        elif intent_type == "post_to_channel":
            channel_id = getattr(intent, "channel_id", 0)
            text = getattr(intent, "text", "")
            buttons = getattr(intent, "buttons", None)
            schedule_ts = getattr(intent, "schedule_ts", None)

            # If scheduled, create a Redis job instead of posting immediately
            if schedule_ts is not None and ctx.redis is not None:
                import json as _json

                from mohizarbot.bot.scheduler import create_job

                buttons_json = _json.dumps(buttons) if buttons else ""
                job_id = f"post_{channel_id}_{schedule_ts}_{ctx.user_id}"
                await create_job(
                    ctx.redis, job_id, channel_id, text, schedule_ts, buttons_json, ctx.user_id
                )
                return {"ok": True, "job_id": job_id, "scheduled": True}

            from mohizarbot.bot.channel import ChannelManager

            mgr = ChannelManager(bot)  # type: ignore[arg-type]
            result = await mgr.post_to_channel(channel_id, text, buttons)
            if result.status == "denied":
                raise RuntimeError(result.reason)
            return result.telegram_response

        elif intent_type == "cancel_scheduled_post":
            job_id = getattr(intent, "job_id", "")
            if ctx.redis is not None:
                from mohizarbot.bot.scheduler import cancel_job

                cancelled = await cancel_job(ctx.redis, job_id)
                return {"ok": cancelled}
            return {"ok": False, "reason": "no_redis"}

        elif intent_type == "edit_channel_post":
            channel_id = getattr(intent, "channel_id", 0)
            message_id = getattr(intent, "message_id", 0)
            text = getattr(intent, "text", "")
            buttons = getattr(intent, "buttons", None)
            from mohizarbot.bot.channel import ChannelManager

            mgr = ChannelManager(bot)  # type: ignore[arg-type]
            result = await mgr.edit_channel_post(channel_id, message_id, text, buttons)
            if result.status == "denied":
                raise RuntimeError(result.reason)
            return result.telegram_response

        # ── Sprint 10: callback response ──
        elif intent_type == "callback_response":
            callback_query_id = getattr(intent, "callback_query_id", "")
            text = getattr(intent, "text", None)
            show_alert = getattr(intent, "show_alert", False)
            if hasattr(bot, "answer_callback_query"):
                await bot.answer_callback_query(
                    callback_query_id=callback_query_id,
                    text=text,
                    show_alert=show_alert,
                )
                return {"ok": True}

        return None
