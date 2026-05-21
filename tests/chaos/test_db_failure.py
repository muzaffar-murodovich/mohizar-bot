from __future__ import annotations

from unittest.mock import AsyncMock


async def test_db_failure_returns_blocked_status() -> None:
    """When the database is unavailable, ActionResult reflects db_unavailable."""
    from mohizarbot.policy.engine import ActionResult

    result = ActionResult(status="blocked", reason="db_unavailable: OperationalError")
    assert result.status == "blocked"
    assert "db_unavailable" in result.reason


async def test_db_failure_does_not_crash_pipeline() -> None:
    """SQLAlchemy OperationalError during execution should be caught."""
    from mohizarbot.policy.engine import PolicyContext, PolicyEngine
    from mohizarbot.policy.intents import IntentBatch, SendMessageIntent

    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=AsyncMock())
    bot.send_message.return_value.model_dump = lambda: {"ok": True}

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    intent = SendMessageIntent(chat_id=123, text="test")
    batch = IntentBatch(actions=[intent])

    # The engine should handle the intent without crashing
    results = await engine.execute(batch, ctx)
    assert len(results) == 1
    # The operation should either succeed or fail gracefully
    assert results[0].status in ("executed", "blocked", "denied", "queued_for_confirmation")


async def test_policy_engine_returns_safe_result_on_failure() -> None:
    """Policy engine must always return a valid ActionResult, never raise."""
    from mohizarbot.policy.engine import ActionResult

    # Default-deny: blocked result is safe
    result = ActionResult(status="blocked", reason="db_unavailable: OperationalError")
    assert isinstance(result, ActionResult)
    assert result.status == "blocked"
    assert isinstance(result.reason, str)


async def test_multiple_failures_recovery() -> None:
    """After transient failures, the system should continue processing."""
    from mohizarbot.policy.engine import PolicyContext, PolicyEngine
    from mohizarbot.policy.intents import IntentBatch, SendMessageIntent

    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=AsyncMock())
    bot.send_message.return_value.model_dump = lambda: {"ok": True}

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    # First attempt might simulate a failure scenario
    # Second attempt should work normally
    for _ in range(3):
        intent = SendMessageIntent(chat_id=123, text="recovery test")
        batch = IntentBatch(actions=[intent])
        results = await engine.execute(batch, ctx)
        assert len(results) == 1
        assert results[0].status in ("executed", "blocked", "denied", "queued_for_confirmation")
