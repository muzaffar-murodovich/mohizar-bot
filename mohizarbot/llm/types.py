from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    role: str  # "system", "user", "assistant", "tool"
    content: str | list[dict[str, object]]
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, object]  # JSON Schema for the tool's input


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, object]


@dataclass
class LLMResponse:
    content: str
    model: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)


@dataclass
class StreamChunk:
    content_delta: str = ""
    tool_call_delta: ToolCall | None = None
    finish_reason: str | None = None
    model: str = ""
    index: int = 0
