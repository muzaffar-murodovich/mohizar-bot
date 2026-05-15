from __future__ import annotations

import json

import httpx
import pytest
import respx

from mohizarbot.llm.providers.openai_ import OpenAIProvider
from mohizarbot.llm.types import ChatMessage, ToolSpec


@pytest.fixture
def openai() -> OpenAIProvider:
    return OpenAIProvider(api_key="test-key", model="gpt-4o")


@respx.mock
async def test_chat_hits_correct_endpoint(openai: OpenAIProvider) -> None:
    route = respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "chatcmpl-123",
                "model": "gpt-4o",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "Hello!"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            },
        )
    )

    messages = [ChatMessage(role="user", content="Hi")]
    response = await openai.chat(messages)

    assert route.called
    assert response.content == "Hello!"
    assert response.model == "gpt-4o"


@respx.mock
async def test_chat_sends_auth_header(openai: OpenAIProvider) -> None:
    route = respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "c",
                "model": "gpt-4o",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "ok"},
                        "finish_reason": "stop",
                    }
                ],
            },
        )
    )

    await openai.chat([ChatMessage(role="user", content="Hi")])
    assert route.calls[0].request.headers["Authorization"] == "Bearer test-key"


@respx.mock
async def test_chat_parses_tool_calls(openai: OpenAIProvider) -> None:
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "c",
                "model": "gpt-4o",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_1",
                                    "type": "function",
                                    "function": {
                                        "name": "search",
                                        "arguments": '{"query": "cats"}',
                                    },
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
            },
        )
    )

    response = await openai.chat([ChatMessage(role="user", content="Search cats")])
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].id == "call_1"
    assert response.tool_calls[0].name == "search"
    assert response.tool_calls[0].arguments == {"query": "cats"}
    assert response.finish_reason == "tool_calls"


@respx.mock
async def test_chat_handles_system_message(openai: OpenAIProvider) -> None:
    route = respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "c",
                "model": "gpt-4o",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "ok"},
                        "finish_reason": "stop",
                    }
                ],
            },
        )
    )

    messages = [
        ChatMessage(role="system", content="Be helpful"),
        ChatMessage(role="user", content="Hi"),
    ]
    await openai.chat(messages)

    body = json.loads(route.calls[0].request.content)
    assert body["messages"][0]["role"] == "system"
    assert body["messages"][0]["content"] == "Be helpful"


@respx.mock
async def test_chat_sends_tools_in_request(openai: OpenAIProvider) -> None:
    route = respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "c",
                "model": "gpt-4o",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "ok"},
                        "finish_reason": "stop",
                    }
                ],
            },
        )
    )

    tools = [
        ToolSpec(
            name="search", description="Search web", parameters={"type": "object", "properties": {}}
        )
    ]
    await openai.chat([ChatMessage(role="user", content="Hi")], tools=tools)

    body = json.loads(route.calls[0].request.content)
    assert "tools" in body
    assert body["tools"][0]["type"] == "function"
    assert body["tools"][0]["function"]["name"] == "search"
