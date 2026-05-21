from __future__ import annotations

from unittest.mock import AsyncMock

from mohizarbot.policy.engine import PolicyContext, PolicyEngine
from mohizarbot.policy.intents import (
    IntentBatch,
    SendMessageIntent,
    SendMessageWithKeyboardIntent,
    SetMessageReactionIntent,
)


async def test_send_message_with_keyboard_executed() -> None:
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=AsyncMock())
    bot.send_message.return_value.model_dump = lambda: {"ok": True}

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    intent = SendMessageWithKeyboardIntent(
        chat_id=123,
        text="Pick one:",
        buttons=[[{"text": "A", "callback_data": "signed_a"}]],
    )
    batch = IntentBatch(actions=[intent])
    results = await engine.execute(batch, ctx)
    assert results[0].status == "executed"
    bot.send_message.assert_awaited_once()


async def test_set_message_reaction_executed() -> None:
    bot = AsyncMock()
    bot.set_message_reaction = AsyncMock(return_value=True)

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    intent = SetMessageReactionIntent(chat_id=123, message_id=10, reaction=["👍"])
    batch = IntentBatch(actions=[intent])
    results = await engine.execute(batch, ctx)
    assert results[0].status == "executed"


async def test_edit_message_executed() -> None:
    bot = AsyncMock()
    bot.edit_message_text = AsyncMock(return_value=AsyncMock())
    bot.edit_message_text.return_value.model_dump = lambda: {"ok": True}

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    from mohizarbot.policy.intents import EditMessageIntent

    intent = EditMessageIntent(chat_id=123, message_id=42, text="updated")
    batch = IntentBatch(actions=[intent])
    results = await engine.execute(batch, ctx)
    assert results[0].status == "executed"


async def test_engine_permission_denied_for_admin_only_in_group() -> None:
    bot = AsyncMock()
    bot.get_chat_member = AsyncMock(return_value=AsyncMock())
    bot.get_chat_member.return_value.status = "member"

    ctx = PolicyContext(user_id=99, chat_id=-100123, bot=bot, hmac_key=b"x" * 32, bot_id=999)
    engine = PolicyEngine()

    from mohizarbot.policy.intents import PinChatMessageIntent

    intent = PinChatMessageIntent(chat_id=-100123, message_id=5)
    batch = IntentBatch(actions=[intent])
    results = await engine.execute(batch, ctx)
    # Non-admin in group cannot pin — should be denied or queued (high risk)
    assert results[0].status in ("denied", "queued_for_confirmation", "blocked")


async def test_send_message_in_private_chat_executed() -> None:
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=AsyncMock())
    bot.send_message.return_value.model_dump = lambda: {"ok": True}

    ctx = PolicyContext(user_id=1, chat_id=456, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    intent = SendMessageIntent(chat_id=456, text="hello")
    batch = IntentBatch(actions=[intent])
    results = await engine.execute(batch, ctx)
    assert results[0].status == "executed"
