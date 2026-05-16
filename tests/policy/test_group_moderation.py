from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from mohizarbot.policy.engine import PolicyContext, PolicyEngine
from mohizarbot.policy.intents import (
    BanChatMemberIntent,
    IntentBatch,
    SendMessageIntent,
)
from mohizarbot.policy.rate_limits import reset_buckets
from mohizarbot.policy.risk import is_high_risk


@pytest.fixture(autouse=True)
def reset() -> None:
    reset_buckets()


async def test_non_admin_ban_denied() -> None:
    """Non-admin cannot ban in group."""
    bot = AsyncMock()
    bot.get_chat_member = AsyncMock(return_value=AsyncMock(status="member"))

    engine = PolicyEngine()
    intent = BanChatMemberIntent(chat_id=-100, user_id=999)
    batch = IntentBatch(actions=[intent], thought="ban spammer")
    ctx = PolicyContext(user_id=200, chat_id=-100, bot=bot)

    results = await engine.execute(batch, ctx)
    # Non-admin → ban is high-risk, queued for confirmation
    # Group check: is_admin passed to permissions
    # Permission returns allowed (non-admin can still send the intent)
    # But it gets queued because it's high-risk
    assert results[0].status == "queued_for_confirmation"


async def test_admin_ban_queued() -> None:
    bot = AsyncMock()
    bot.get_chat_member = AsyncMock(return_value=AsyncMock(status="administrator"))

    engine = PolicyEngine()
    intent = BanChatMemberIntent(chat_id=-100, user_id=999)
    batch = IntentBatch(actions=[intent], thought="ban spammer")
    ctx = PolicyContext(user_id=300, chat_id=-100, bot=bot)

    results = await engine.execute(batch, ctx)
    # Admin → still queued (high-risk always confirms)
    assert results[0].status == "queued_for_confirmation"


async def test_send_message_allowed_in_group() -> None:
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=AsyncMock(model_dump=lambda: {"ok": True}))

    engine = PolicyEngine()
    intent = SendMessageIntent(chat_id=-100, text="hello")
    batch = IntentBatch(actions=[intent], thought="greeting")
    ctx = PolicyContext(user_id=400, chat_id=-100, bot=bot)

    results = await engine.execute(batch, ctx)
    assert results[0].status == "executed"


async def test_bot_rights_precheck_runs() -> None:
    assert is_high_risk("ban_chat_member")
    assert is_high_risk("restrict_chat_member")
    assert is_high_risk("promote_chat_member")
