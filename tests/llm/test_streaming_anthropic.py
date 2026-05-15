from __future__ import annotations

import httpx
import respx

from mohizarbot.llm.providers.anthropic_ import AnthropicProvider
from mohizarbot.llm.types import ChatMessage

SSE_DATA = (
    'data: {"type":"message_start","message":{"id":"msg_1","model":"claude-sonnet-4-6","role":"assistant"}}\n'
    "\n"
    'data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}\n'
    "\n"
    'data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Hello"}}\n'
    "\n"
    'data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":" world"}}\n'
    "\n"
    'data: {"type":"content_block_stop","index":0}\n'
    "\n"
    'data: {"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":null}}\n'
    "\n"
    'data: {"type":"message_stop"}\n'
    "\n"
)


@respx.mock
async def test_stream_yields_chunks_in_order() -> None:
    provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-4-6")

    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(200, content=SSE_DATA)
    )

    chunks = []
    async for chunk in provider.stream([ChatMessage(role="user", content="Hi")]):
        chunks.append(chunk)

    # Should have at least: message_start, 2 text deltas, message_delta
    assert len(chunks) >= 3

    # Content-bearing chunks
    content_chunks = [c for c in chunks if c.content_delta]
    assert len(content_chunks) == 2
    assert content_chunks[0].content_delta == "Hello"
    assert content_chunks[1].content_delta == " world"

    # message_start has model
    model_chunks = [c for c in chunks if c.model]
    assert len(model_chunks) >= 1
    assert model_chunks[0].model == "claude-sonnet-4-6"

    # Final chunk has finish_reason
    finish_chunks = [c for c in chunks if c.finish_reason]
    assert len(finish_chunks) >= 1
    assert finish_chunks[-1].finish_reason == "end_turn"
