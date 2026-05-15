from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from collections.abc import Sequence

    from mohizarbot.llm.base import LLMProvider
    from mohizarbot.llm.types import ChatMessage, ToolSpec

logger = logging.getLogger(__name__)


class LLMUnavailableError(Exception):
    """Raised when all providers in the failover chain have failed."""


# Cost tiers: cheap providers are prioritized for simple/short prompts
_CHEAP_PROVIDERS = {"deepseek"}
_VISION_PROVIDERS = {"anthropic", "openai"}

# Token-count threshold for cost routing
_SHORT_PROMPT_TOKEN_ESTIMATE = 500


def _estimate_tokens(messages: Sequence[ChatMessage]) -> int:
    """Rough token estimate: ~1 token per 4 chars."""
    total = 0
    for msg in messages:
        content = msg.content
        if isinstance(content, str):
            total += len(content)
        else:
            total += sum(len(str(b.get("text", ""))) for b in content if isinstance(b, dict))
    return total // 4


class Router:
    """Selects a provider based on strategy and handles failover.

    Strategies:
      - cost-aware: short prompts → cheap provider (DeepSeek)
      - capability-aware: vision/long-context hints route to capable providers
      - explicit per-chat override always wins
    """

    def __init__(
        self,
        providers: list[LLMProvider],
        default: str | None = None,
    ) -> None:
        self._providers = {p.provider_name: p for p in providers}
        self._default = default or (providers[0].provider_name if providers else "")
        self._chain: list[str] = list(self._providers.keys())

    def select(
        self,
        messages: Sequence[ChatMessage],
        capability_hints: dict[str, object] | None = None,
    ) -> LLMProvider:
        """Pick the best provider given messages and capability hints.

        Resolution order:
        1. Explicit per-chat override (capability_hints["provider"])
        2. Capability-aware routing
        3. Cost-aware routing
        4. Default provider
        """
        hints = capability_hints or {}

        # 1. Explicit per-chat override
        explicit = hints.get("provider")
        if explicit and str(explicit) in self._providers:
            return self._providers[str(explicit)]

        # 2. Capability-aware routing
        if hints.get("vision") or hints.get("long_context"):
            for name in self._chain:
                if name in _VISION_PROVIDERS:
                    return self._providers[name]

        # 3. Cost-aware routing for short prompts
        token_est = _estimate_tokens(messages)
        if token_est < _SHORT_PROMPT_TOKEN_ESTIMATE:
            for name in self._chain:
                if name in _CHEAP_PROVIDERS:
                    return self._providers[name]

        # 4. Default
        if self._default in self._providers:
            return self._providers[self._default]
        return self._providers[self._chain[0]]

    @property
    def provider_names(self) -> list[str]:
        return self._chain

    def set_failover_chain(self, chain: list[str]) -> None:
        """Set the failover order. Providers not in chain are unavailable."""
        self._chain = [name for name in chain if name in self._providers]

    async def chat_with_failover(
        self,
        messages: list[ChatMessage],
        tools: list[ToolSpec] | None = None,
        capability_hints: dict[str, object] | None = None,
        **opts: object,
    ) -> object:
        """Call chat() with automatic failover across the chain.

        Catches httpx.HTTPStatusError (5xx) and httpx.TimeoutException,
        tries the next provider in the chain. Raises LLMUnavailableError
        if all providers fail.
        """
        provider = self.select(messages, capability_hints)
        # Start from the selected provider's position in the chain
        start_idx = 0
        for i, name in enumerate(self._chain):
            if name == provider.provider_name:
                start_idx = i
                break

        last_error: Exception | None = None
        for i in range(len(self._chain)):
            idx = (start_idx + i) % len(self._chain)
            name = self._chain[idx]
            p = self._providers[name]
            try:
                return await p.chat(messages, tools, **opts)
            except httpx.HTTPStatusError as e:
                if e.response.status_code < 500:
                    raise
                logger.warning("Provider %s failed: %s", name, e)
                last_error = e
                await asyncio.sleep(0.5)
            except httpx.TimeoutException as e:
                logger.warning("Provider %s failed: %s", name, e)
                last_error = e
                await asyncio.sleep(0.5)

        raise LLMUnavailableError(
            f"All providers failed (chain: {self._chain}). Last error: {last_error}"
        )
