from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from mohizarbot.llm.types import (
        ChatMessage,
        LLMResponse,
        StreamChunk,
        ToolSpec,
    )

__all__ = ["LLMProvider"]


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol for LLM providers.

    Every provider (Anthropic, OpenAI, DeepSeek, etc.) must implement
    chat() and stream(). Code outside mohizarbot/llm/providers/ must
    only reference this Protocol — never import provider modules directly.
    """

    @property
    def provider_name(self) -> str: ...

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolSpec] | None = None,
        **opts: object,
    ) -> LLMResponse: ...

    async def stream(
        self,
        messages: list[ChatMessage],
        tools: list[ToolSpec] | None = None,
        **opts: object,
    ) -> AsyncIterator[StreamChunk]: ...
