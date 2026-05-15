from __future__ import annotations

import httpx
import pytest
import respx

from mohizarbot.llm.providers.anthropic_ import AnthropicProvider
from mohizarbot.llm.types import ChatMessage, ToolSpec


@pytest.fixture
def anthropic() -> AnthropicProvider:
    return AnthropicProvider(api_key="test-key", model="claude-sonnet-4-6")


@respx.mock
async def test_chat_sends_correct_request_shape(anthropic: AnthropicProvider) -> None:
    route = respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "msg_123",
                "model": "claude-sonnet-4-6",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "Hello!"}],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
        )
    )

    messages = [ChatMessage(role="user", content="Hi")]
    await anthropic.chat(messages)

    assert route.called
    req = route.calls[0].request
    assert req.headers["x-api-key"] == "test-key"
    assert req.headers["anthropic-version"] == "2023-06-01"
    body = req.content and __import__("json").loads(req.content)
    assert body["model"] == "claude-sonnet-4-6"
    assert body["messages"] == [{"role": "user", "content": "Hi"}]


@respx.mock
async def test_chat_parses_content_blocks(anthropic: AnthropicProvider) -> None:
    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "msg_1",
                "model": "claude-sonnet-4-6",
                "stop_reason": "end_turn",
                "content": [
                    {"type": "text", "text": "Part one. "},
                    {"type": "text", "text": "Part two."},
                ],
            },
        )
    )

    response = await anthropic.chat([ChatMessage(role="user", content="Hi")])
    assert response.content == "Part one. Part two."
    assert response.model == "claude-sonnet-4-6"
    assert response.finish_reason == "end_turn"


@respx.mock
async def test_chat_parses_tool_use_blocks(anthropic: AnthropicProvider) -> None:
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
                        "name": "get_weather",
                        "input": {"city": "Paris"},
                    }
                ],
            },
        )
    )

    response = await anthropic.chat([ChatMessage(role="user", content="Weather?")])
    assert response.content == ""
    assert len(response.tool_calls) == 1
    tc = response.tool_calls[0]
    assert tc.id == "toolu_001"
    assert tc.name == "get_weather"
    assert tc.arguments == {"city": "Paris"}


@respx.mock
async def test_chat_sends_tools_in_request(anthropic: AnthropicProvider) -> None:
    route = respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "msg_1",
                "model": "claude-sonnet-4-6",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "ok"}],
            },
        )
    )

    tools = [
        ToolSpec(
            name="search",
            description="Search the web",
            parameters={"type": "object", "properties": {}},
        )
    ]
    await anthropic.chat([ChatMessage(role="user", content="Hi")], tools=tools)

    body = __import__("json").loads(route.calls[0].request.content)
    assert "tools" in body
    assert body["tools"][0]["name"] == "search"


@respx.mock
async def test_chat_handles_system_message(anthropic: AnthropicProvider) -> None:
    route = respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "msg_1",
                "model": "claude-sonnet-4-6",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "ok"}],
            },
        )
    )

    messages = [
        ChatMessage(role="system", content="You are helpful."),
        ChatMessage(role="user", content="Hi"),
    ]
    await anthropic.chat(messages)

    body = __import__("json").loads(route.calls[0].request.content)
    assert "system" in body
    assert body["system"][0]["text"] == "You are helpful."
    assert body["messages"] == [{"role": "user", "content": "Hi"}]
