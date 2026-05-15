from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from mohizarbot.policy.engine import PolicyContext, PolicyEngine
from mohizarbot.policy.intents import (
    DeleteMessageIntent,
    IntentBatch,
    SendMessageIntent,
)
from mohizarbot.policy.rate_limits import reset_buckets


@pytest.fixture(autouse=True)
def reset_rl() -> None:
    reset_buckets()


async def test_send_message_executes() -> None:
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=AsyncMock(model_dump=lambda: {"ok": True}))

    engine = PolicyEngine()
    batch = IntentBatch(actions=[SendMessageIntent(chat_id=1, text="hello")])
    ctx = PolicyContext(user_id=100, chat_id=1, bot=bot)

    results = await engine.execute(batch, ctx)
    assert len(results) == 1
    assert results[0].status == "executed"
    bot.send_message.assert_awaited_once()


async def test_edit_message_executes() -> None:
    bot = AsyncMock()
    bot.edit_message_text = AsyncMock(return_value=AsyncMock(model_dump=lambda: {"ok": True}))

    engine = PolicyEngine()
    from mohizarbot.policy.intents import EditMessageIntent

    batch = IntentBatch(actions=[EditMessageIntent(chat_id=1, message_id=5, text="updated")])
    ctx = PolicyContext(user_id=100, chat_id=1, bot=bot)

    results = await engine.execute(batch, ctx)
    assert results[0].status == "executed"


async def test_delete_message_queues_for_confirmation() -> None:
    bot = AsyncMock()
    bot.get_chat_member = AsyncMock(return_value=AsyncMock(status="administrator"))

    engine = PolicyEngine()
    batch = IntentBatch(actions=[DeleteMessageIntent(chat_id=-100, message_id=99)])
    ctx = PolicyContext(user_id=200, chat_id=-100, bot=bot)

    results = await engine.execute(batch, ctx)
    assert results[0].status == "queued_for_confirmation"


async def test_rate_limited_returns_blocked() -> None:
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=AsyncMock(model_dump=lambda: {"ok": True}))

    engine = PolicyEngine()
    ctx = PolicyContext(user_id=300, chat_id=1, bot=bot)

    # Fire 25 send_message intents with same user/chat to trigger limit (20/min)
    all_results = []
    for _ in range(25):
        batch = IntentBatch(actions=[SendMessageIntent(chat_id=1, text="spam")])
        all_results.extend(await engine.execute(batch, ctx))

    executed = [r for r in all_results if r.status == "executed"]
    assert len(executed) >= 20
    blocked = [r for r in all_results if r.status == "blocked"]
    assert len(blocked) >= 1


async def test_private_chat_bypasses_admin_check() -> None:
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=AsyncMock(model_dump=lambda: {"ok": True}))

    engine = PolicyEngine()
    batch = IntentBatch(actions=[SendMessageIntent(chat_id=123, text="private")])
    ctx = PolicyContext(user_id=400, chat_id=123, bot=bot)

    results = await engine.execute(batch, ctx)
    assert results[0].status == "executed"
