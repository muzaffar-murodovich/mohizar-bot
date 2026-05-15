from __future__ import annotations

import httpx
import pytest
import respx

from mohizarbot.llm.providers.deepseek_ import DeepSeekProvider
from mohizarbot.llm.types import ChatMessage


@pytest.fixture
def deepseek() -> DeepSeekProvider:
    return DeepSeekProvider(api_key="test-key")


@respx.mock
async def test_chat_defaults_to_deepseek_chat(deepseek: DeepSeekProvider) -> None:
    route = respx.post("https://api.deepseek.com/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "ds_123",
                "model": "deepseek-chat",
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

    response = await deepseek.chat([ChatMessage(role="user", content="Hi")])

    assert route.called
    body = __import__("json").loads(route.calls[0].request.content)
    assert body["model"] == "deepseek-chat"
    assert response.model == "deepseek-chat"
    assert response.content == "Hello!"


@respx.mock
async def test_chat_hits_deepseek_endpoint(deepseek: DeepSeekProvider) -> None:
    route = respx.post("https://api.deepseek.com/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "ds",
                "model": "deepseek-chat",
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

    await deepseek.chat([ChatMessage(role="user", content="Hi")])
    assert route.calls[0].request.headers["Authorization"] == "Bearer test-key"


@respx.mock
async def test_chat_uses_explicit_model(deepseek: DeepSeekProvider) -> None:
    route = respx.post("https://api.deepseek.com/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "ds",
                "model": "deepseek-reasoner",
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

    await deepseek.chat([ChatMessage(role="user", content="Hi")], model="deepseek-reasoner")
    body = __import__("json").loads(route.calls[0].request.content)
    assert body["model"] == "deepseek-reasoner"


@respx.mock
async def test_chat_parses_tool_calls(deepseek: DeepSeekProvider) -> None:
    respx.post("https://api.deepseek.com/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "ds",
                "model": "deepseek-chat",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_ds",
                                    "type": "function",
                                    "function": {"name": "calc", "arguments": '{"expr": "2+2"}'},
                                }
                            ],
                        },
                        "finish_reason": "tool_calls",
                    }
                ],
            },
        )
    )

    response = await deepseek.chat([ChatMessage(role="user", content="calc 2+2")])
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "calc"


@respx.mock
async def test_chat_parses_usage(deepseek: DeepSeekProvider) -> None:
    respx.post("https://api.deepseek.com/chat/completions").mock(
        return_value=httpx.Response(
            200,
            json={
                "id": "ds",
                "model": "deepseek-chat",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": "ok"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75},
            },
        )
    )

    response = await deepseek.chat([ChatMessage(role="user", content="Hi")])
    assert response.usage == {"input_tokens": 50, "output_tokens": 25, "total_tokens": 75}
