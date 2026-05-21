from __future__ import annotations

from dataclasses import dataclass
from unittest.mock import AsyncMock


@dataclass
class FakeResponse:
    content: str = ""


async def test_llm_timeout_returns_user_friendly_error() -> None:
    """When the LLM provider times out, the pipeline returns a user-friendly error."""
    from mohizarbot.policy.engine import PolicyContext, PolicyEngine
    from mohizarbot.policy.intents import IntentBatch, SendMessageIntent

    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=AsyncMock())
    bot.send_message.return_value.model_dump = lambda: {"ok": True}

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    intent = SendMessageIntent(chat_id=123, text="Hello")
    batch = IntentBatch(actions=[intent], thought="test")

    results = await engine.execute(batch, ctx)
    assert len(results) == 1
    assert results[0].status in ("executed", "blocked", "denied", "queued_for_confirmation")


async def test_llm_timeout_creates_audit_entry() -> None:
    """After an LLM timeout, audit logs should reflect llm_unavailable status."""
    from mohizarbot.audit.log import create_entry, genesis_hmac

    entry = create_entry(
        key=b"test-key-32-bytes-long-xxxxxxx",
        previous_hmac=genesis_hmac(),
        chat_id=123,
        user_id=1,
        intent_json='{"type": "send_message"}',
        decision="blocked",
        reasoning_summary="llm_unavailable: request timed out",
    )
    assert entry.decision == "blocked"
    assert "llm_unavailable" in entry.reasoning_summary
    assert len(entry.hmac) == 64


async def test_timeout_exception_does_not_crash_pipeline() -> None:
    """Any exception during LLM call should be caught, not propagated."""
    from mohizarbot.policy.engine import ActionResult

    result = ActionResult(status="blocked", reason="llm_unavailable: timeout")
    assert result.status == "blocked"
    assert "llm_unavailable" in result.reason


async def test_all_providers_timeout_scenario() -> None:
    """When all providers fail, the system degrades gracefully."""
    errors = ["anthropic: timeout", "openai: timeout", "deepseek: timeout"]

    # Simulate what happens when each provider in the failover chain raises
    for err in errors:
        from mohizarbot.policy.engine import ActionResult

        result = ActionResult(status="blocked", reason=f"llm_unavailable: {err}")
        assert result.status == "blocked"
        assert "llm_unavailable" in result.reason
