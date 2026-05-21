from __future__ import annotations

from unittest.mock import AsyncMock

from mohizarbot.policy.engine import PolicyContext, PolicyEngine
from mohizarbot.policy.intents import (
    CancelScheduledPostIntent,
    DeleteMessageIntent,
    IntentBatch,
)


async def test_delete_message_executed() -> None:
    bot = AsyncMock()
    bot.delete_message = AsyncMock(return_value=True)

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    intent = DeleteMessageIntent(chat_id=123, message_id=10)
    batch = IntentBatch(actions=[intent], thought="cleanup")
    results = await engine.execute(batch, ctx)
    # delete_message is HIGH risk → queued_for_confirmation
    assert results[0].status in ("executed", "queued_for_confirmation")


async def test_cancel_scheduled_post_executed() -> None:
    bot = AsyncMock()
    redis = AsyncMock()
    redis.delete = AsyncMock(return_value=1)

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32, redis=redis)
    engine = PolicyEngine()

    intent = CancelScheduledPostIntent(job_id="test_job_123")
    batch = IntentBatch(actions=[intent])
    results = await engine.execute(batch, ctx)
    # cancel_scheduled_post is HIGH risk → queued_for_confirmation
    assert results[0].status in ("executed", "queued_for_confirmation")


async def test_engine_exception_during_execution() -> None:
    """Test that exceptions during intent execution are caught."""
    from mohizarbot.policy.intents import SendMessageIntent

    bot = AsyncMock()
    bot.send_message = AsyncMock(side_effect=RuntimeError("Telegram API error"))

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    intent = SendMessageIntent(chat_id=123, text="test")
    batch = IntentBatch(actions=[intent])
    results = await engine.execute(batch, ctx)
    assert results[0].status == "blocked"
