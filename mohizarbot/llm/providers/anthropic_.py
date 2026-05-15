from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx

from mohizarbot.llm.types import (
    ChatMessage,
    LLMResponse,
    StreamChunk,
    ToolCall,
    ToolSpec,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class AnthropicProvider:
    provider_name = "anthropic"

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-6",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._client = http_client or httpx.AsyncClient()

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolSpec] | None = None,
        **opts: object,
    ) -> LLMResponse:
        model = str(opts.get("model", self._model))
        body = _build_anthropic_body(messages, tools, model, opts)
        response = await self._client.post(
            ANTHROPIC_API,
            json=body,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(120.0),
        )
        response.raise_for_status()
        return _parse_anthropic_response(response.json())

    async def stream(
        self,
        messages: list[ChatMessage],
        tools: list[ToolSpec] | None = None,
        **opts: object,
    ) -> AsyncIterator[StreamChunk]:
        model = str(opts.get("model", self._model))
        body = _build_anthropic_body(messages, tools, model, opts)
        body["stream"] = True
        async with self._client.stream(
            "POST",
            ANTHROPIC_API,
            json=body,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(120.0),
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data: Any = json.loads(line[6:])
                for chunk in _parse_anthropic_sse(data):
                    yield chunk


def _build_anthropic_body(
    messages: list[ChatMessage],
    tools: list[ToolSpec] | None,
    model: str,
    opts: dict[str, object],
) -> dict[str, object]:
    system_parts: list[dict[str, object]] = []
    api_messages: list[dict[str, object]] = []

    for msg in messages:
        if msg.role == "system":
            system_parts.append({"type": "text", "text": _content_str(msg.content)})
        else:
            api_messages.append({"role": msg.role, "content": _content_str(msg.content)})

    body: dict[str, object] = {
        "model": model,
        "messages": api_messages,
        "max_tokens": int(str(opts.get("max_tokens", 4096))),
    }
    if system_parts:
        body["system"] = system_parts
    if tools:
        body["tools"] = [
            {"name": t.name, "description": t.description, "input_schema": t.parameters}
            for t in tools
        ]
    return body


def _content_str(content: str | list[dict[str, object]]) -> str:
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for b in content:
        if isinstance(b, dict) and b.get("type") == "text":
            parts.append(str(b.get("text", "")))
    return "".join(parts)


def _parse_anthropic_response(data: Any) -> LLMResponse:
    if not isinstance(data, dict):
        return LLMResponse(content="", model="")
    content = ""
    tool_calls: list[ToolCall] = []
    finish_reason = str(data.get("stop_reason", "stop"))

    for block in data.get("content", []) or []:
        if not isinstance(block, dict):
            continue
        if block.get("type") == "text":
            content += str(block.get("text", ""))
        elif block.get("type") == "tool_use":
            tool_calls.append(
                ToolCall(
                    id=str(block.get("id", "")),
                    name=str(block.get("name", "")),
                    arguments=block.get("input", {})
                    if isinstance(block.get("input"), dict)
                    else {},
                )
            )

    usage: dict[str, int] = {}
    u = data.get("usage")
    if isinstance(u, dict):
        usage = {
            "input_tokens": int(str(u.get("input_tokens", 0))),
            "output_tokens": int(str(u.get("output_tokens", 0))),
        }

    return LLMResponse(
        content=content,
        model=str(data.get("model", "")),
        tool_calls=tool_calls,
        finish_reason=finish_reason,
        usage=usage,
    )


def _parse_anthropic_sse(data: Any) -> list[StreamChunk]:
    if not isinstance(data, dict):
        return []
    event_type = str(data.get("type", ""))

    if event_type == "content_block_delta":
        delta = data.get("delta", {})
        if not isinstance(delta, dict):
            return []
        if delta.get("type") == "text_delta":
            return [
                StreamChunk(
                    content_delta=str(delta.get("text", "")),
                    model="",
                    index=int(str(data.get("index", 0))),
                )
            ]
        elif delta.get("type") == "input_json_delta":
            return [
                StreamChunk(
                    content_delta=str(delta.get("partial_json", "")),
                    model="",
                    index=int(str(data.get("index", 0))),
                )
            ]
    elif event_type == "message_start":
        msg = data.get("message", {})
        if isinstance(msg, dict):
            return [StreamChunk(model=str(msg.get("model", "")))]
    elif event_type == "message_delta":
        delta = data.get("delta", {})
        if isinstance(delta, dict):
            return [
                StreamChunk(
                    finish_reason=str(delta.get("stop_reason", "")),
                    model="",
                )
            ]

    return []
