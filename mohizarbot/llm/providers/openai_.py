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

OPENAI_API = "https://api.openai.com/v1/chat/completions"


class OpenAIProvider:
    provider_name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
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
        body = _build_openai_body(messages, tools, model, opts)
        response = await self._client.post(
            OPENAI_API,
            json=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(120.0),
        )
        response.raise_for_status()
        return _parse_openai_response(response.json())

    async def stream(
        self,
        messages: list[ChatMessage],
        tools: list[ToolSpec] | None = None,
        **opts: object,
    ) -> AsyncIterator[StreamChunk]:
        model = str(opts.get("model", self._model))
        body = _build_openai_body(messages, tools, model, opts)
        body["stream"] = True
        body["stream_options"] = {"include_usage": True}
        async with self._client.stream(
            "POST",
            OPENAI_API,
            json=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(120.0),
        ) as response:
            response.raise_for_status()
            idx = 0
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[6:].strip()
                if payload == "[DONE]":
                    yield StreamChunk(finish_reason="stop")
                    return
                data: Any = json.loads(payload)
                chunk = _parse_openai_sse(data, idx)
                if chunk:
                    yield chunk
                    idx += 1


def _build_openai_body(
    messages: list[ChatMessage],
    tools: list[ToolSpec] | None,
    model: str,
    opts: dict[str, object],
) -> dict[str, object]:
    api_messages: list[dict[str, object]] = []
    for msg in messages:
        api_msg: dict[str, object] = {"role": msg.role, "content": _content_str(msg.content)}
        if msg.name:
            api_msg["name"] = msg.name
        if msg.tool_call_id:
            api_msg["tool_call_id"] = msg.tool_call_id
        if msg.tool_calls:
            api_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                }
                for tc in msg.tool_calls
            ]
        api_messages.append(api_msg)

    body: dict[str, object] = {"model": model, "messages": api_messages}
    if tools:
        body["tools"] = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]
    return body


def _content_str(content: str | list[dict[str, object]]) -> str:
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for b in content:
        if isinstance(b, dict):
            if b.get("type") == "text":
                parts.append(str(b.get("text", "")))
            elif b.get("type") == "image_url":
                parts.append("[image]")
    return "".join(parts)


def _parse_openai_response(data: Any) -> LLMResponse:
    if not isinstance(data, dict):
        return LLMResponse(content="", model="")
    choices_raw = data.get("choices", [])
    choice: dict[str, Any] = {}
    if isinstance(choices_raw, list) and choices_raw:
        first = choices_raw[0]
        if isinstance(first, dict):
            choice = first

    msg: dict[str, Any] = {}
    msg_raw = choice.get("message", {})
    if isinstance(msg_raw, dict):
        msg = msg_raw

    content = str(msg.get("content", "") or "")
    finish_reason = str(choice.get("finish_reason", "stop"))

    tool_calls: list[ToolCall] = []
    for tc in msg.get("tool_calls", []) or []:
        if not isinstance(tc, dict):
            continue
        fn: dict[str, Any] = {}
        fn_raw = tc.get("function", {})
        if isinstance(fn_raw, dict):
            fn = fn_raw
        args = fn.get("arguments", "{}")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        tool_calls.append(
            ToolCall(
                id=str(tc.get("id", "")),
                name=str(fn.get("name", "")),
                arguments=args if isinstance(args, dict) else {},
            )
        )

    usage: dict[str, int] = {}
    u = data.get("usage")
    if isinstance(u, dict):
        usage = {
            "input_tokens": int(str(u.get("prompt_tokens", 0))),
            "output_tokens": int(str(u.get("completion_tokens", 0))),
            "total_tokens": int(str(u.get("total_tokens", 0))),
        }

    return LLMResponse(
        content=content,
        model=str(data.get("model", "")),
        tool_calls=tool_calls,
        finish_reason=finish_reason,
        usage=usage,
    )


def _parse_openai_sse(data: Any, idx: int) -> StreamChunk | None:
    if not isinstance(data, dict):
        return None
    choices_raw = data.get("choices", [])
    if not isinstance(choices_raw, list) or not choices_raw:
        return None
    first = choices_raw[0]
    if not isinstance(first, dict):
        return None
    delta: dict[str, Any] = {}
    delta_raw = first.get("delta", {})
    if isinstance(delta_raw, dict):
        delta = delta_raw

    content_delta = str(delta.get("content", "") or "")
    finish = first.get("finish_reason")
    finish_str = str(finish) if finish else None

    return StreamChunk(
        content_delta=content_delta,
        finish_reason=finish_str,
        model=str(data.get("model", "")),
        index=idx,
    )
