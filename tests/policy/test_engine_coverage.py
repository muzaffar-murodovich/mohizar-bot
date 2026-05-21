from __future__ import annotations

from unittest.mock import AsyncMock

from mohizarbot.policy.engine import ActionResult, PolicyContext, PolicyEngine
from mohizarbot.policy.intents import (
    CallbackResponseIntent,
    EditReplyMarkupIntent,
    ForwardMessageIntent,
    IntentBatch,
)


async def test_forward_message_executed() -> None:
    bot = AsyncMock()
    bot.forward_message = AsyncMock(return_value=AsyncMock())
    bot.forward_message.return_value.model_dump = lambda: {"ok": True}

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    intent = ForwardMessageIntent(from_chat_id=10, message_id=50, to_chat_id=20)
    batch = IntentBatch(actions=[intent])
    results = await engine.execute(batch, ctx)
    assert results[0].status == "executed"


async def test_edit_reply_markup_executed() -> None:
    bot = AsyncMock()
    bot.edit_message_reply_markup = AsyncMock(return_value=True)

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    intent = EditReplyMarkupIntent(chat_id=123, message_id=42, buttons=[])
    batch = IntentBatch(actions=[intent])
    results = await engine.execute(batch, ctx)
    assert results[0].status == "executed"


async def test_callback_response_executed() -> None:
    bot = AsyncMock()
    bot.answer_callback_query = AsyncMock(return_value=True)

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    intent = CallbackResponseIntent(callback_query_id="cbq_test", text="Hello", show_alert=True)
    batch = IntentBatch(actions=[intent])
    results = await engine.execute(batch, ctx)
    assert results[0].status == "executed"
    bot.answer_callback_query.assert_awaited_once()


async def test_action_class_for_unknown_returns_unknown() -> None:
    from mohizarbot.policy.intents import SendMessageIntent

    intent = SendMessageIntent(chat_id=1, text="hi")
    cls = PolicyEngine._action_class(intent)
    assert cls == "send_message"


async def test_action_result_fields() -> None:
    r = ActionResult(status="denied", reason="test reason")
    assert r.status == "denied"
    assert r.reason == "test reason"
    assert r.telegram_response is None


async def test_policy_context_redis_field() -> None:
    ctx = PolicyContext(user_id=1, chat_id=2, bot=AsyncMock(), redis=None)
    assert ctx.redis is None
    assert ctx.user_id == 1
    assert ctx.chat_id == 2
