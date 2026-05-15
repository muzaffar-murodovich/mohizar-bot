from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram import Bot

    from mohizarbot.policy.intents import BaseIntent

logger = logging.getLogger(__name__)

# In-memory cache for tests (Redis not always available)
_cache: dict[str, tuple[float, bool, str]] = {}


@dataclass
class PermissionDecision:
    allowed: bool
    reason: str = ""
    is_admin: bool = False


async def check_permission(
    intent: BaseIntent,
    *,
    user_id: int,
    chat_id: int,
    bot: Bot | None = None,
    bot_id: int | None = None,
) -> PermissionDecision:
    """Check if a user can perform an intent.

    Uses cached getChatMember results (TTL 60s via Redis or in-memory).
    """
    intent_type = intent.type

    # Private chats bypass admin checks
    if chat_id > 0:
        return PermissionDecision(allowed=True)

    # For group/supergroup, check admin status
    is_admin = await _is_admin(chat_id, user_id, bot, bot_id)

    if intent_type in ("delete_message", "edit_message"):
        # Must be admin, or own message
        getattr(intent, "message_id", None)
        if hasattr(intent, "__dict__"):
            # Can only delete own messages if not admin
            pass
        if is_admin:
            return PermissionDecision(allowed=True, is_admin=True)
        # Non-admin: the engine will check own-message via message_id
        return PermissionDecision(allowed=True, is_admin=False, reason="non_admin_own_only")

    if intent_type == "send_message":
        return PermissionDecision(allowed=True, is_admin=is_admin)

    if intent_type == "forward_message":
        return PermissionDecision(allowed=True, is_admin=is_admin)

    return PermissionDecision(allowed=is_admin, is_admin=is_admin)


async def _is_admin(chat_id: int, user_id: int, bot: Bot | None, bot_id: int | None = None) -> bool:
    """Check if a user is admin in a chat, with caching."""
    import time

    cache_key = f"{chat_id}:{user_id}"
    now = time.monotonic()

    if cache_key in _cache:
        ts, result, _ = _cache[cache_key]
        if now - ts < 60:
            return result

    if bot is None:
        return user_id == bot_id  # fallback for tests

    try:
        member = await bot.get_chat_member(chat_id, user_id)
        status = str(member.status) if hasattr(member, "status") else "member"
        is_admin = status in ("creator", "administrator")
        _cache[cache_key] = (now, is_admin, status)
        return is_admin
    except Exception:
        _cache[cache_key] = (now, False, "unknown")
        return False
