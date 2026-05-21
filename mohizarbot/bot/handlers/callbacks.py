from __future__ import annotations

import contextlib
import json
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery

    from mohizarbot.bot.api_wrapper import BotApiWrapper

logger = logging.getLogger(__name__)


async def handle_callback(
    callback: CallbackQuery,
    api: BotApiWrapper,
    hmac_key: bytes,
) -> None:
    """Handle all callback queries: confirmations and arbitrary signed callbacks.

    Two flows:
    1. ``confirm:<token>:<decision>`` — Sprint 4 confirmation flow.
    2. ``<hmac_sig>:<json_payload>`` — Sprint 10 arbitrary signed callbacks.
       Payload is JSON with at minimum a ``"type"`` field.

    Unsigned or tampered callbacks are silently dropped and logged to audit.
    """
    data = callback.data or ""

    # Flow 1: confirmation tokens
    if data.startswith("confirm:"):
        await _handle_confirmation(callback, api, hmac_key, data)
        return

    # Flow 2: arbitrary signed callbacks
    await _handle_signed_callback(callback, api, hmac_key, data)


async def _handle_confirmation(
    callback: CallbackQuery,
    api: BotApiWrapper,
    hmac_key: bytes,
    data: str,
) -> None:
    """Handle Sprint 4 confirmation flow."""
    from mohizarbot.policy.confirmations import resolve_confirmation
    from mohizarbot.policy.engine import PolicyContext, PolicyEngine

    parts = data.split(":", 2)
    if len(parts) != 3:
        await callback.answer("Invalid callback data")
        return

    _, token, decision = parts
    approved = decision == "approve"
    user_id = callback.from_user.id

    result = resolve_confirmation(token, user_id, approved, hmac_key=hmac_key)

    if result is None:
        if not approved and callback.message is not None:
            await callback.answer("Action cancelled")
            await callback.message.edit_text("Action cancelled.")  # type: ignore[union-attr]
        else:
            await callback.answer("Invalid or expired confirmation token")
        return

    engine = PolicyEngine()
    intent_type = str(result.get("type", ""))

    if intent_type == "delete_message":
        ctx = PolicyContext(
            user_id=user_id,
            chat_id=int(str(result.get("chat_id", 0))),
            bot=api._bot,
            hmac_key=hmac_key,
        )
        from mohizarbot.policy.intents import DeleteMessageIntent, IntentBatch

        intent = DeleteMessageIntent(
            chat_id=int(str(result.get("chat_id", 0))),
            message_id=int(str(result.get("message_id", 0))),
        )
        batch = IntentBatch(actions=[intent], thought="confirmed")
        actions = await engine.execute(batch, ctx)

        if actions and actions[0].status == "executed":
            await callback.answer("Action executed")
            if callback.message is not None:
                with contextlib.suppress(Exception):
                    await callback.message.edit_text("✓ Action completed.")  # type: ignore[union-attr]
        else:
            await callback.answer(f"Failed: {actions[0].reason if actions else 'unknown'}")
    else:
        await callback.answer("Confirmation resolved but action not supported yet")


async def _handle_signed_callback(
    callback: CallbackQuery,
    api: BotApiWrapper,
    hmac_key: bytes,
    data: str,
) -> None:
    """Handle Sprint 10 arbitrary signed callback_data.

    Verifies the HMAC signature. If valid, parses the JSON payload and acts.
    If invalid, silently drops and writes an audit log entry.
    """
    from mohizarbot.audit.log import create_entry, genesis_hmac
    from mohizarbot.bot.keyboard import verify_callback

    payload = verify_callback(data, hmac_key)
    if payload is None:
        # Unsigned/tampered — silently drop + audit
        chat_id = callback.message.chat.id if callback.message else 0
        user_id = callback.from_user.id
        try:
            create_entry(
                hmac_key,
                previous_hmac=genesis_hmac(),
                chat_id=chat_id,
                user_id=user_id,
                intent_json=json.dumps({"event": "unsigned_callback_dropped", "data": data[:200]}),
                decision="dropped",
                reasoning_summary="Unsigned or tampered callback_data received",
            )
        except Exception:
            logger.warning("Failed to write audit entry for dropped callback")
        return

    # Try to parse as JSON
    try:
        payload_obj: dict[str, object] = json.loads(payload)
    except json.JSONDecodeError:
        logger.warning("Callback payload is not valid JSON, dropping")
        return

    action = str(payload_obj.get("action", ""))
    user_id = callback.from_user.id

    if action == "answer":
        # Generic answer to callback query
        text = str(payload_obj.get("text", ""))
        show_alert = bool(payload_obj.get("show_alert", False))
        await callback.answer(text=text or None, show_alert=show_alert)
    elif action == "dismiss":
        await callback.answer()
    else:
        # Unknown action — answer generically
        logger.info("Unknown callback action: %s", action)
        await callback.answer(text="Action received")
