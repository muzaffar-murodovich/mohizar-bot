from __future__ import annotations

import httpx
import respx

from mohizarbot.llm.providers.openai_ import OpenAIProvider
from mohizarbot.llm.types import ChatMessage

SSE_DATA = (
    'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1,'
    '"model":"gpt-4o","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}\n'
    "\n"
    'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1,'
    '"model":"gpt-4o","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}\n'
    "\n"
    'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1,'
    '"model":"gpt-4o","choices":[{"index":0,"delta":{"content":" world"},"finish_reason":null}]}\n'
    "\n"
    'data: {"id":"chatcmpl-123","object":"chat.completion.chunk","created":1,'
    '"model":"gpt-4o","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}\n'
    "\n"
    "data: [DONE]\n"
    "\n"
)


@respx.mock
async def test_stream_parses_sse_data_lines() -> None:
    provider = OpenAIProvider(api_key="test-key", model="gpt-4o")

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, content=SSE_DATA)
    )

    chunks = []
    async for chunk in provider.stream([ChatMessage(role="user", content="Hi")]):
        chunks.append(chunk)

    # Content chunks: "Hello", " world", then a finish_reason chunk, then [DONE]
    content_chunks = [c for c in chunks if c.content_delta]
    assert len(content_chunks) == 2
    assert content_chunks[0].content_delta == "Hello"
    assert content_chunks[1].content_delta == " world"


@respx.mock
async def test_done_terminates_stream() -> None:
    provider = OpenAIProvider(api_key="test-key", model="gpt-4o")

    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=httpx.Response(200, content=SSE_DATA)
    )

    chunks = []
    async for chunk in provider.stream([ChatMessage(role="user", content="Hi")]):
        chunks.append(chunk)

    # Last meaningful chunk should have finish_reason from "stop" before [DONE]
    finish_chunks = [c for c in chunks if c.finish_reason == "stop"]
    assert len(finish_chunks) >= 1

    # [DONE] produces a final stop chunk
    last = chunks[-1]
    assert last.finish_reason == "stop" or last.finish_reason is not None
