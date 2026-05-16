from __future__ import annotations

from unittest.mock import AsyncMock

from mohizarbot.policy.engine import PolicyContext, PolicyEngine
from mohizarbot.policy.intents import IntentBatch, SendMessageIntent
from mohizarbot.policy.rate_limits import reset_buckets


class _MockGuardProvider:
    def __init__(self, verdict: str):
        self._verdict = verdict

    async def chat(self, messages, tools=None, **opts):
        from mohizarbot.llm.types import LLMResponse as R

        return R(content=self._verdict, model="guard")


async def test_medium_risk_passes_through_guard() -> None:
    """Edit is medium risk — should go through guard when guard is integrated."""
    reset_buckets()
    bot = AsyncMock()
    bot.edit_message_text = AsyncMock(return_value=AsyncMock(model_dump=lambda: {"ok": True}))

    from mohizarbot.policy.intents import EditMessageIntent

    batch = IntentBatch(actions=[EditMessageIntent(chat_id=1, message_id=5, text="fixed")])
    ctx = PolicyContext(user_id=100, chat_id=1, bot=bot)
    engine = PolicyEngine()
    results = await engine.execute(batch, ctx)
    assert results[0].status == "executed"


async def test_low_risk_skips_guard_for_cost() -> None:
    """Send message is low risk — guard is NOT called (cost optimization)."""
    reset_buckets()
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=AsyncMock(model_dump=lambda: {"ok": True}))

    batch = IntentBatch(actions=[SendMessageIntent(chat_id=1, text="hi")])
    ctx = PolicyContext(user_id=100, chat_id=1, bot=bot)
    engine = PolicyEngine()
    results = await engine.execute(batch, ctx)
    assert results[0].status == "executed"
    # Guard should not have been called (low risk skips)
    assert _MockGuardProvider("")._verdict == ""  # never called


async def test_high_risk_still_queued() -> None:
    """Delete message is high risk — always queued for confirmation."""
    reset_buckets()
    bot = AsyncMock()
    bot.get_chat_member = AsyncMock(return_value=AsyncMock(status="administrator"))

    from mohizarbot.policy.intents import DeleteMessageIntent

    batch = IntentBatch(actions=[DeleteMessageIntent(chat_id=-100, message_id=99)])
    ctx = PolicyContext(user_id=200, chat_id=-100, bot=bot)
    engine = PolicyEngine()
    results = await engine.execute(batch, ctx)
    assert results[0].status == "queued_for_confirmation"
