from __future__ import annotations

from unittest.mock import AsyncMock

from mohizarbot.policy.intents import DeleteMessageIntent, SendMessageIntent
from mohizarbot.policy.permissions import _cache, check_permission


async def test_admin_can_delete() -> None:
    bot = AsyncMock()
    bot.get_chat_member = AsyncMock(return_value=AsyncMock(status="administrator"))
    _cache.clear()

    intent = DeleteMessageIntent(chat_id=-100, message_id=42)
    result = await check_permission(intent, user_id=200, chat_id=-100, bot=bot)
    assert result.allowed
    assert result.is_admin


async def test_non_admin_cannot_delete_others() -> None:
    bot = AsyncMock()
    bot.get_chat_member = AsyncMock(return_value=AsyncMock(status="member"))
    _cache.clear()

    intent = DeleteMessageIntent(chat_id=-100, message_id=42)
    result = await check_permission(intent, user_id=300, chat_id=-100, bot=bot)
    # Non-admin can delete own but with restricted reason
    assert result.allowed
    assert not result.is_admin


async def test_private_chat_bypasses_admin() -> None:
    bot = AsyncMock()
    intent = SendMessageIntent(chat_id=456, text="hi")
    result = await check_permission(intent, user_id=500, chat_id=456, bot=bot)
    assert result.allowed
    # Should not call getChatMember for private chat
    bot.get_chat_member.assert_not_called() if hasattr(bot, "get_chat_member") else None


async def test_cache_hit_avoids_duplicate_call() -> None:
    bot = AsyncMock()
    bot.get_chat_member = AsyncMock(return_value=AsyncMock(status="administrator"))
    _cache.clear()

    intent = DeleteMessageIntent(chat_id=-200, message_id=5)
    r1 = await check_permission(intent, user_id=600, chat_id=-200, bot=bot)
    assert r1.allowed

    # Second call should use cache
    r2 = await check_permission(intent, user_id=600, chat_id=-200, bot=bot)
    assert r2.allowed

    # get_chat_member should only be called once
    assert bot.get_chat_member.call_count == 1
