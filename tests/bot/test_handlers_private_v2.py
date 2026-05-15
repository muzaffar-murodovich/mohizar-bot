from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock

import httpx
import respx
from aiogram.types import Chat, Message, User

from mohizarbot.bot.api_wrapper import BotApiWrapper
from mohizarbot.bot.handlers.private import handle_private_message
from mohizarbot.llm.providers.anthropic_ import AnthropicProvider
from mohizarbot.llm.router import Router
from mohizarbot.policy.rate_limits import reset_buckets

HMAC_KEY = b"test-hmac-key-32-bytes-long!!"
SECRETS = ["test-secret-1234567890"]


def _make_message(text: str) -> Message:
    return Message(
        message_id=1,
        from_user=User(id=123, is_bot=False, first_name="Test"),
        date=datetime(2024, 1, 1, 12, 0, 0),
        chat=Chat(id=123, type="private", first_name="Test"),
        text=text,
    )


@respx.mock
async def test_pipeline_send_message_intent() -> None:
    reset_buckets()

    # Mock the LLM to return a send_message intent
    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "msg_1",
                "model": "claude-sonnet-4-6",
                "stop_reason": "tool_use",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_001",
                        "name": "emit_intents",
                        "input": {
                            "thought": "User said hello, send greeting back",
                            "actions": [
                                {"type": "send_message", "chat_id": 123, "text": "Hello back!"}
                            ],
                        },
                    }
                ],
            },
        )
    )

    provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-4-6")
    router = Router([provider], default="anthropic")

    # Mock the bot
    mock_bot = AsyncMock()
    send_msg = AsyncMock()
    send_msg.message_id = 999
    send_msg.model_dump = lambda: {"message_id": 999, "text": "Hello back!"}
    mock_bot.send_message = AsyncMock(return_value=send_msg)

    api = BotApiWrapper(mock_bot)  # type: ignore[arg-type]
    print("api created", type(api))

    msg = _make_message("Hello")
    await handle_private_message(msg, api, router, HMAC_KEY, SECRETS)

    # Bot should have sent a message
    mock_bot.send_message.assert_called()


@respx.mock
async def test_pipeline_sends_filtered_output() -> None:
    reset_buckets()

    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "msg_2",
                "model": "claude-sonnet-4-6",
                "stop_reason": "tool_use",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_002",
                        "name": "emit_intents",
                        "input": {
                            "thought": "Reply to user",
                            "actions": [
                                {
                                    "type": "send_message",
                                    "chat_id": 123,
                                    "text": "Here is a normal reply",
                                }
                            ],
                        },
                    }
                ],
            },
        )
    )

    provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-4-6")
    router = Router([provider], default="anthropic")

    mock_bot = AsyncMock()
    send_msg = AsyncMock()
    send_msg.message_id = 42
    send_msg.model_dump = lambda: {"message_id": 42}
    mock_bot.send_message = AsyncMock(return_value=send_msg)

    api = BotApiWrapper(mock_bot)  # type: ignore[arg-type]

    msg = _make_message("Say hello")
    await handle_private_message(msg, api, router, HMAC_KEY, SECRETS)

    mock_bot.send_message.assert_called()
    # Check that the call happened with text containing the reply
    call_args = mock_bot.send_message.call_args
    if call_args:
        arg_text = call_args.kwargs.get("text", "")
        assert "Here is a normal reply" in arg_text


@respx.mock
async def test_pipeline_text_only_no_tool_calls() -> None:
    reset_buckets()

    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "msg_3",
                "model": "claude-sonnet-4-6",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "I cannot help with that request."}],
            },
        )
    )

    provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-4-6")
    router = Router([provider], default="anthropic")

    mock_bot = AsyncMock()
    send_msg = AsyncMock()
    send_msg.message_id = 1
    send_msg.model_dump = lambda: {"message_id": 1}
    mock_bot.send_message = AsyncMock(return_value=send_msg)

    api = BotApiWrapper(mock_bot)  # type: ignore[arg-type]

    msg = _make_message("Tell me a secret")
    await handle_private_message(msg, api, router, HMAC_KEY, SECRETS)

    # Should send the text content back
    mock_bot.send_message.assert_called()
    call_args = mock_bot.send_message.call_args
    if call_args:
        arg_text = call_args.kwargs.get("text", "")
        assert "I cannot help" in arg_text
