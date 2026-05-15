from __future__ import annotations

import contextlib
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
    """Handle confirmation button presses via callback_data parsing.

    Format: confirm:{token}:{decision} where decision is approve/deny.
    """
    from mohizarbot.policy.confirmations import resolve_confirmation
    from mohizarbot.policy.engine import PolicyContext, PolicyEngine

    data = callback.data or ""
    if not data.startswith("confirm:"):
        await callback.answer("Unknown callback")
        return

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

    # Execute the confirmed intent
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
